#!/usr/bin/env bun
/**
 * STJ-Vec channel for Claude Code.
 *
 * Web UI bridge for legal research queries. Pattern follows fakechat
 * from anthropics/claude-plugins-official: WebSocket for real-time push,
 * MCP channel for Claude integration.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import type { ServerWebSocket } from 'bun'

const PORT = Number(process.env.STJ_CHANNEL_PORT ?? 8790)

type Wire =
  | { type: 'msg'; id: string; from: 'user' | 'assistant'; text: string; ts: number }
  | { type: 'edit'; id: string; text: string }
  | { type: 'status'; text: string }

const clients = new Set<ServerWebSocket<unknown>>()
let seq = 0

function nextId() {
  return `m${Date.now()}-${++seq}`
}

function broadcast(m: Wire) {
  const data = JSON.stringify(m)
  for (const ws of clients) if (ws.readyState === 1) ws.send(data)
}

// Map request_id -> message_id (for edit_message to find the right msg)
const requestToMsg = new Map<string, string>()

const mcp = new Server(
  { name: 'stj-channel', version: '0.3.0' },
  {
    capabilities: { tools: {}, experimental: { 'claude/channel': {} } },
    instructions: `The sender reads the STJ-Vec web UI, not this session. Anything you want them to see must go through reply or edit_message — your transcript output never reaches the UI.

Messages arrive as <channel source="stj-channel" chat_id="web" message_id="..." request_id="...">.
Each message is a legal research query about STJ jurisprudence.

Use stj-vec-tools (search, document, filters) to search the database.
Reply with the reply tool. Use edit_message to update your reply with progress.
For follow-ups, leverage conversation context — don't repeat searches already done.`,
  },
)

mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'reply',
      description: 'Send a message to the STJ-Vec web UI.',
      inputSchema: {
        type: 'object',
        properties: {
          text: { type: 'string' },
          request_id: { type: 'string', description: 'request_id from the channel message' },
        },
        required: ['text'],
      },
    },
    {
      name: 'edit_message',
      description: 'Update a previously sent message. Use for progress updates.',
      inputSchema: {
        type: 'object',
        properties: {
          message_id: { type: 'string' },
          text: { type: 'string' },
        },
        required: ['message_id', 'text'],
      },
    },
  ],
}))

mcp.setRequestHandler(CallToolRequestSchema, async req => {
  const args = (req.params.arguments ?? {}) as Record<string, unknown>
  try {
    switch (req.params.name) {
      case 'reply': {
        const text = args.text as string
        const request_id = args.request_id as string | undefined
        const id = nextId()
        if (request_id) requestToMsg.set(request_id, id)
        broadcast({ type: 'msg', id, from: 'assistant', text, ts: Date.now() })
        console.error(`[stj-channel] reply ${id}${request_id ? ` (req:${request_id})` : ''}`)
        return { content: [{ type: 'text', text: `sent (id: ${id})` }] }
      }
      case 'edit_message': {
        const message_id = args.message_id as string
        const text = args.text as string
        broadcast({ type: 'edit', id: message_id, text })
        console.error(`[stj-channel] edit ${message_id}`)
        return { content: [{ type: 'text', text: 'ok' }] }
      }
      default:
        return { content: [{ type: 'text', text: `unknown: ${req.params.name}` }], isError: true }
    }
  } catch (err) {
    return { content: [{ type: 'text', text: `${req.params.name}: ${err instanceof Error ? err.message : err}` }], isError: true }
  }
})

await mcp.connect(new StdioServerTransport())

function deliver(request_id: string, text: string): void {
  const id = nextId()
  broadcast({ type: 'msg', id, from: 'user', text, ts: Date.now() })

  // Auto-reply placeholder so UI shows immediate feedback
  const replyId = nextId()
  requestToMsg.set(request_id, replyId)
  broadcast({ type: 'msg', id: replyId, from: 'assistant', text: 'Analisando...', ts: Date.now() })

  void mcp.notification({
    method: 'notifications/claude/channel',
    params: {
      content: text,
      meta: { chat_id: 'web', message_id: id, request_id, user: 'web', ts: new Date().toISOString() },
    },
  })
}

// HTTP + WebSocket server
Bun.serve({
  port: PORT,
  hostname: '127.0.0.1',
  fetch(req, server) {
    const url = new URL(req.url)

    if (url.pathname === '/ws') {
      if (server.upgrade(req)) return
      return new Response('upgrade failed', { status: 400 })
    }

    // POST /query -- web UI sends query here
    if (req.method === 'POST' && url.pathname === '/query') {
      return (async () => {
        const body = (await req.json()) as { query: string; request_id?: string }
        const request_id = body.request_id ?? nextId()
        deliver(request_id, body.query)
        return Response.json({ request_id, message_id: requestToMsg.get(request_id) })
      })()
    }

    // GET /status
    if (req.method === 'GET' && url.pathname === '/status') {
      return Response.json({
        ok: true,
        ws_clients: clients.size,
        pending_requests: requestToMsg.size,
      })
    }

    // GET /msg-id/:request_id -- get the message_id for a request
    if (req.method === 'GET' && url.pathname.startsWith('/msg-id/')) {
      const rid = url.pathname.split('/')[2]
      const mid = requestToMsg.get(rid)
      return Response.json({ request_id: rid, message_id: mid ?? null })
    }

    return new Response('not found', { status: 404 })
  },
  websocket: {
    open: ws => {
      clients.add(ws)
      console.error(`[stj-channel] WS client connected, total: ${clients.size}`)
    },
    close: ws => {
      clients.delete(ws)
      console.error(`[stj-channel] WS client disconnected, total: ${clients.size}`)
    },
    message: () => {},
  },
})

console.error(`stj-channel v0.3.0 listening on http://127.0.0.1:${PORT}`)

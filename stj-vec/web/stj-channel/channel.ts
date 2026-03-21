#!/usr/bin/env bun
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const PORT = parseInt(process.env.STJ_CHANNEL_PORT ?? "8790");

// Cada request_id tem um controller SSE para push
const activeStreams = new Map<
  string,
  {
    controller: ReadableStreamDefaultController;
    timeout: ReturnType<typeof setTimeout>;
  }
>();

const mcp = new Server(
  { name: "stj-channel", version: "0.1.0" },
  {
    capabilities: {
      experimental: { "claude/channel": {} },
      tools: {},
    },
    instructions: `Mensagens chegam como <channel source="stj-channel" request_id="...">.
Cada mensagem e uma query de pesquisa juridica sobre jurisprudencia do STJ.
Voce DEVE responder usando a tool stj_channel_reply, passando o request_id da tag channel.
Use as tools stj-vec-tools (search, document, filters) para buscar na base.
Para follow-ups, aproveite o contexto da conversa -- nao repita buscas ja feitas.`,
  }
);

// Tool discovery
mcp.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "stj_channel_reply",
      description:
        "Responde uma query de pesquisa juridica. Use apos completar buscas e analise.",
      inputSchema: {
        type: "object" as const,
        properties: {
          request_id: {
            type: "string",
            description:
              "ID da requisicao (atributo request_id da tag channel)",
          },
          text: {
            type: "string",
            description:
              "Resposta completa com analise e citacoes de precedentes",
          },
        },
        required: ["request_id", "text"],
      },
    },
  ],
}));

// Tool execution -- push via SSE
mcp.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "stj_channel_reply") {
    const { request_id, text } = req.params.arguments as {
      request_id: string;
      text: string;
    };

    const stream = activeStreams.get(request_id);
    if (stream) {
      clearTimeout(stream.timeout);
      const encoder = new TextEncoder();
      stream.controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({ type: "reply", request_id, text })}\n\n`
        )
      );
      stream.controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({ type: "done", request_id })}\n\n`
        )
      );
      stream.controller.close();
      activeStreams.delete(request_id);
    }

    return { content: [{ type: "text", text: "reply pushed via SSE" }] };
  }
  throw new Error(`unknown tool: ${req.params.name}`);
});

await mcp.connect(new StdioServerTransport());

// HTTP server
let nextId = 1;
const STREAM_TIMEOUT_MS = 600_000; // 10 min

Bun.serve({
  port: PORT,
  hostname: "127.0.0.1",
  async fetch(req) {
    const url = new URL(req.url);

    // POST /query -- fire-and-forget, retorna request_id imediatamente
    if (req.method === "POST" && url.pathname === "/query") {
      const body = (await req.json()) as {
        query: string;
        request_id?: string;
      };
      const request_id = body.request_id ?? String(nextId++);

      await mcp.notification({
        method: "notifications/claude/channel",
        params: {
          content: body.query,
          meta: { request_id },
        },
      });

      return Response.json({ request_id });
    }

    // GET /stream/:id -- SSE push stream
    if (req.method === "GET" && url.pathname.startsWith("/stream/")) {
      const request_id = url.pathname.split("/")[2];

      const stream = new ReadableStream({
        start(controller) {
          const encoder = new TextEncoder();
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ type: "connected", request_id })}\n\n`
            )
          );

          const timeout = setTimeout(() => {
            controller.enqueue(
              encoder.encode(
                `data: ${JSON.stringify({ type: "timeout", request_id })}\n\n`
              )
            );
            controller.close();
            activeStreams.delete(request_id);
          }, STREAM_TIMEOUT_MS);

          activeStreams.set(request_id, { controller, timeout });
        },
        cancel() {
          const s = activeStreams.get(request_id);
          if (s) clearTimeout(s.timeout);
          activeStreams.delete(request_id);
        },
      });

      return new Response(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
        },
      });
    }

    // GET /status
    if (req.method === "GET" && url.pathname === "/status") {
      return Response.json({
        ok: true,
        active_streams: activeStreams.size,
      });
    }

    return new Response("not found", { status: 404 });
  },
});

console.error(`stj-channel listening on http://127.0.0.1:${PORT}`);

"""
CCui WebSocket Backend
Simple WebSocket server for Claude Code UI chat interface.
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CCui WebSocket Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_data: Dict[str, dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.session_data[client_id] = {
            "connected_at": datetime.now().isoformat(),
            "messages": [],
            "context_used": 0
        }
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.session_data:
            del self.session_data[client_id]
        logger.info(f"Client {client_id} disconnected. Total: {len(self.active_connections)}")

    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)

    async def broadcast(self, data: dict):
        for client_id, connection in self.active_connections.items():
            await connection.send_json(data)


manager = ConnectionManager()


class ChatRequest(BaseModel):
    message: str
    token: str = "dev-token"


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ccui-ws",
        "connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    HTTP endpoint for sending chat messages.
    Streams response to all connected WebSocket clients with matching token.
    """
    content = request.message.strip()
    token = request.token

    if not content:
        return {"status": "error", "message": "Empty message"}

    logger.info(f"[POST /api/chat] Received: {content[:50]}...")

    # Find connected client with this token
    target_clients = [cid for cid in manager.active_connections.keys() if cid.startswith(token)]

    if not target_clients:
        # No WebSocket connection, return direct response
        response = generate_response(content)
        return {
            "status": "ok",
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

    # Generate and stream response
    response = generate_response(content)

    for client_id in target_clients:
        # Send tokens for streaming effect
        words = response.split()

        for word in words:
            await manager.send_json(client_id, {
                "type": "token",
                "content": word + " "
            })
            await asyncio.sleep(0.015)  # Simulate streaming

        # Send completion
        await manager.send_json(client_id, {
            "type": "done"
        })

    return {"status": "ok", "message": "Response streamed"}


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(default="anonymous")
):
    client_id = f"{token}_{id(websocket)}"
    await manager.connect(websocket, client_id)

    # Send welcome message
    await manager.send_json(client_id, {
        "type": "connected",
        "message": "Connected to CCui backend",
        "client_id": client_id,
        "timestamp": datetime.now().isoformat()
    })

    try:
        while True:
            data = await websocket.receive_json()
            await handle_message(client_id, data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


async def handle_message(client_id: str, data: dict):
    """Process incoming messages and generate responses."""
    msg_type = data.get("type", "unknown")

    if msg_type == "chat":
        await handle_chat_message(client_id, data)
    elif msg_type == "ping":
        await manager.send_json(client_id, {"type": "pong", "timestamp": datetime.now().isoformat()})
    elif msg_type == "status":
        await send_status(client_id)
    else:
        await manager.send_json(client_id, {
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        })


async def handle_chat_message(client_id: str, data: dict):
    """Handle chat messages - echo with simulated thinking."""
    content = data.get("content", "").strip()

    if not content:
        return

    # Store user message
    if client_id in manager.session_data:
        manager.session_data[client_id]["messages"].append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    # Send acknowledgment
    await manager.send_json(client_id, {
        "type": "message_received",
        "content": content,
        "timestamp": datetime.now().isoformat()
    })

    # Simulate thinking
    await manager.send_json(client_id, {
        "type": "thinking_start",
        "label": "Processing"
    })

    # Brief delay to simulate processing
    await asyncio.sleep(0.5)

    # Generate response based on input
    response = generate_response(content)

    await manager.send_json(client_id, {
        "type": "thinking_complete",
        "duration": "0.5s"
    })

    # Send response
    await manager.send_json(client_id, {
        "type": "message",
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().isoformat()
    })

    # Update context usage (simulated)
    if client_id in manager.session_data:
        manager.session_data[client_id]["context_used"] += len(content) + len(response)
        context_percent = min(100, manager.session_data[client_id]["context_used"] // 1000)

        await manager.send_json(client_id, {
            "type": "context_update",
            "percentUsed": context_percent
        })


def generate_response(content: str) -> str:
    """Generate a response based on input content."""
    content_lower = content.lower()

    # Command handling
    if content.startswith("/"):
        cmd = content[1:].split()[0].lower()
        if cmd == "help":
            return """**Available Commands:**
- `/help` - Show this help message
- `/status` - Show session status
- `/clear` - Clear conversation
- `/model` - Show current model info

**Tips:**
- Type naturally to chat
- Use code blocks with triple backticks
- Press Enter to send, Shift+Enter for new line"""
        elif cmd == "status":
            return "Session active. WebSocket connected. Ready for input."
        elif cmd == "clear":
            return "Conversation cleared."
        elif cmd == "model":
            return "**Current Model:** Claude 3.7 Sonnet (simulated)\n**Context:** 200K tokens\n**Status:** Ready"
        else:
            return f"Unknown command: `/{cmd}`. Type `/help` for available commands."

    # Echo with enhancement
    if "hello" in content_lower or "hi" in content_lower or "ola" in content_lower:
        return f"Hello! I'm CCui, your Claude Code interface. How can I help you today?\n\nYou said: *{content}*"

    if "test" in content_lower:
        return f"""**Test received!**

Your message: `{content}`

The WebSocket connection is working correctly. Here's what I can do:
- Process chat messages
- Execute commands (try `/help`)
- Show code blocks:

```python
print("Hello from CCui!")
```

Feel free to explore!"""

    # Default echo response
    return f"""Received your message:

> {content}

This is a demonstration response from the CCui WebSocket backend. The full Claude integration would process this through the Claude API.

*Timestamp: {datetime.now().strftime('%H:%M:%S')}*"""


async def send_status(client_id: str):
    """Send current session status."""
    session = manager.session_data.get(client_id, {})
    await manager.send_json(client_id, {
        "type": "status",
        "connected_at": session.get("connected_at"),
        "message_count": len(session.get("messages", [])),
        "context_used": session.get("context_used", 0)
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

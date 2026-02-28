import { describe, it, expect } from "vitest";
import type { MessagePart, ChatMessage, ServerMessage, ClientMessage } from "../types/protocol";

describe("protocol types", () => {
  it("MessagePart aceita todos os tipos validos", () => {
    const parts: MessagePart[] = [
      { type: "text", content: "Ola" },
      { type: "thinking", content: "Analisando..." },
      { type: "tool_use", content: '{"path":"/x"}', metadata: { toolName: "Read", toolId: "tu_1" } },
      { type: "tool_result", content: "conteudo do arquivo", metadata: { toolId: "tu_1" } },
    ];
    expect(parts).toHaveLength(4);
  });

  it("ChatMessage tem campos obrigatorios", () => {
    const msg: ChatMessage = {
      id: "msg_1",
      role: "assistant",
      parts: [{ type: "text", content: "Resposta" }],
      timestamp: Date.now(),
    };
    expect(msg.role).toBe("assistant");
    expect(msg.parts[0].type).toBe("text");
  });

  it("ServerMessage aceita chat_delta", () => {
    const msg: ServerMessage = {
      type: "chat_delta",
      message_id: "msg_1",
      part: { type: "text", content: "chunk" },
    };
    expect(msg.type).toBe("chat_delta");
  });

  it("chat_start tem session_id", () => {
    const msg: ServerMessage = {
      type: "chat_start",
      message_id: "m1",
      session_id: "sess_abc",
    };
    expect(msg.session_id).toBe("sess_abc");
  });

  it("chat_delta tem session_id", () => {
    const msg: ServerMessage = {
      type: "chat_delta",
      message_id: "m1",
      session_id: "sess_abc",
      part: { type: "text", content: "chunk" },
    };
    expect(msg.session_id).toBe("sess_abc");
  });

  it("chat_end tem session_id", () => {
    const msg: ServerMessage = {
      type: "chat_end",
      message_id: "m1",
      session_id: "sess_abc",
    };
    expect(msg.session_id).toBe("sess_abc");
  });

  it("chat_init existe e tem campos corretos", () => {
    const msg: ServerMessage = {
      type: "chat_init",
      session_id: "sess_abc",
      model: "claude-sonnet-4-5",
      claude_session_id: "claude_xyz",
    };
    expect(msg.type).toBe("chat_init");
    expect(msg.model).toBe("claude-sonnet-4-5");
  });

  it("ClientMessage aceita chat_input com session_id", () => {
    const msg: ClientMessage = {
      type: "chat_input",
      session_id: "sess_abc",
      text: "Qual o status do processo?",
    };
    expect(msg.type).toBe("chat_input");
  });
});

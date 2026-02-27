import { describe, it, expect } from "vitest";
import type { MessagePart, ChatMessage, ServerMessage } from "../types/protocol";

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
});

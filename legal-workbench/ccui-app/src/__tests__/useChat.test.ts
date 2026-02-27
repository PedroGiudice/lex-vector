import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

const mockSend = vi.fn();
let messageHandler: ((msg: any) => void) | null = null;
const mockOnMessage = vi.fn((handler: any) => {
  messageHandler = handler;
  return () => { messageHandler = null; };
});

vi.mock("../contexts/WebSocketContext", () => ({
  useWebSocket: () => ({
    send: mockSend,
    onMessage: mockOnMessage,
  }),
}));

import { useChat } from "../hooks/useChat";

describe("useChat", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    messageHandler = null;
  });

  it("acumula mensagens do usuario via sendMessage", () => {
    const { result } = renderHook(() => useChat());
    act(() => result.current.sendMessage("Ola"));
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].parts[0].content).toBe("Ola");
    expect(mockSend).toHaveBeenCalledWith({ type: "input", channel: "main", text: "Ola" });
  });

  it("processa chat_start + chat_delta + chat_end", () => {
    const { result } = renderHook(() => useChat());

    act(() => messageHandler?.({ type: "chat_start", message_id: "m1" }));
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.isStreaming).toBe(true);

    act(() => messageHandler?.({
      type: "chat_delta",
      message_id: "m1",
      part: { type: "text", content: "Resposta" },
    }));
    expect(result.current.messages[0].parts).toHaveLength(1);
    expect(result.current.messages[0].parts[0].content).toBe("Resposta");

    act(() => messageHandler?.({ type: "chat_end", message_id: "m1" }));
    expect(result.current.isStreaming).toBe(false);
    expect(result.current.messages[0].isStreaming).toBe(false);
  });

  it("clearMessages limpa tudo", () => {
    const { result } = renderHook(() => useChat());
    act(() => result.current.sendMessage("msg"));
    act(() => result.current.clearMessages());
    expect(result.current.messages).toHaveLength(0);
  });
});

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

const mockSessionId = "sess_test_123";
vi.mock("../contexts/SessionContext", () => ({
  useSession: () => ({
    sessionId: mockSessionId,
    caseId: "caso-001",
    selectCase: vi.fn(),
    createSession: vi.fn(),
    reset: vi.fn(),
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
  });

  it("sendMessage envia chat_input com session_id", () => {
    const { result } = renderHook(() => useChat());
    act(() => result.current.sendMessage("Ola processProxy"));
    expect(mockSend).toHaveBeenCalledWith({
      type: "chat_input",
      session_id: "sess_test_123",
      text: "Ola processProxy",
    });
  });

  it("ignora chat_init sem crashar", () => {
    const { result } = renderHook(() => useChat());
    act(() => messageHandler?.({
      type: "chat_init",
      session_id: "sess_abc",
      model: "claude-sonnet-4-5",
      claude_session_id: "claude_xyz",
    }));
    expect(result.current.messages).toHaveLength(0);
  });

  it("chat_start/delta/end com session_id funcionam igual", () => {
    const { result } = renderHook(() => useChat());

    act(() => messageHandler?.({ type: "chat_start", message_id: "m1", session_id: "sess_abc" }));
    expect(result.current.isStreaming).toBe(true);

    act(() => messageHandler?.({
      type: "chat_delta",
      message_id: "m1",
      session_id: "sess_abc",
      part: { type: "text", content: "ola" },
    }));
    expect(result.current.messages[0].parts[0].content).toBe("ola");

    act(() => messageHandler?.({ type: "chat_end", message_id: "m1", session_id: "sess_abc" }));
    expect(result.current.isStreaming).toBe(false);
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

  it("chat_start duplicado com mesmo message_id nao adiciona mensagem extra", () => {
    const { result } = renderHook(() => useChat());

    act(() => messageHandler?.({ type: "chat_start", message_id: "m1" }));
    act(() => messageHandler?.({ type: "chat_start", message_id: "m1" }));
    act(() => messageHandler?.({ type: "chat_start", message_id: "m1" }));

    expect(result.current.messages).toHaveLength(1);
  });

  it("clearMessages limpa tudo", () => {
    const { result } = renderHook(() => useChat());
    act(() => result.current.sendMessage("msg"));
    act(() => result.current.clearMessages());
    expect(result.current.messages).toHaveLength(0);
  });
});

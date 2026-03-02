import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import React from "react";

// Mock WebSocket
let wsInstance: any = null;
let messageHandlers: Set<(msg: any) => void>;

const mockSend = vi.fn();
const mockConnect = vi.fn(() => Promise.resolve());
const mockDisconnect = vi.fn();
const mockRetryManual = vi.fn();

beforeEach(() => {
  messageHandlers = new Set();
  mockSend.mockClear();
  mockConnect.mockClear();
  wsInstance = null;
});

vi.mock("../../contexts/WebSocketContext", () => ({
  WebSocketProvider: ({ children }: { children: React.ReactNode }) => children,
  useWebSocket: () => ({
    status: "connected",
    retryCount: 0,
    maxRetries: 5,
    send: mockSend,
    connect: mockConnect,
    disconnect: mockDisconnect,
    retryManual: mockRetryManual,
    onMessage: (handler: any) => {
      messageHandlers.add(handler);
      return () => messageHandlers.delete(handler);
    },
  }),
}));

// Mock API hooks
const mockCases = [
  { id: "caso-001", path: "/cases/001", ready: true, doc_count: 5, last_modified: "2026-01-01" },
];

vi.mock("../../hooks/useCcuiApi", () => ({
  useCases: () => ({
    cases: mockCases,
    loading: false,
    error: null,
    fetchCases: vi.fn(),
  }),
  useHealth: () => ({
    healthy: true,
    loading: false,
    error: null,
    checkHealth: vi.fn(),
  }),
  useSessions: () => ({
    sessions: [],
    loading: false,
    error: null,
    fetchSessions: vi.fn(),
  }),
  useSessionChannels: () => ({
    channels: [],
    loading: false,
    error: null,
    fetchChannels: vi.fn(),
  }),
}));

// Mock StartupGate (bypass health check)
vi.mock("../../components/StartupGate", () => ({
  StartupGate: ({ children }: { children: React.ReactNode }) => children,
}));

// Mock useTauriStore -- usa localStorage como fallback (ambiente de teste)
const storage: Record<string, string> = {};
vi.stubGlobal("localStorage", {
  getItem: (key: string) => storage[key] ?? null,
  setItem: (key: string, val: string) => { storage[key] = val; },
  removeItem: (key: string) => { delete storage[key]; },
});

import App from "../../App";

function emitWs(msg: any) {
  messageHandlers.forEach((h) => h(msg));
}

describe("chat flow integration", () => {
  it("fluxo completo: case select -> session -> chat message", async () => {
    render(<App />);

    // 1. Aguardar CaseSelector carregar
    const caseCard = await screen.findByText("caso-001");
    expect(caseCard).toBeInTheDocument();

    // 2. Clicar no caso
    fireEvent.click(caseCard);

    // 3. Simular session_created via WS
    act(() => {
      emitWs({ type: "session_created", session_id: "sess-1", case_id: "caso-001" });
    });

    // 4. SessionView deve estar renderizado (input visivel)
    const input = await screen.findByPlaceholderText("Instruir o Claude...");
    expect(input).toBeInTheDocument();

    // 5. Digitar e enviar mensagem
    fireEvent.change(input, { target: { value: "Qual o prazo?" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(mockSend).toHaveBeenCalledWith({
      type: "chat_input",
      session_id: "sess-1",
      text: "Qual o prazo?",
    });

    // 6. Verificar mensagem do usuario renderizada
    expect(screen.getByText("Qual o prazo?")).toBeInTheDocument();

    // 7. Simular resposta do assistente
    act(() => {
      emitWs({ type: "chat_start", message_id: "m1", session_id: "sess_test" });
    });

    act(() => {
      emitWs({
        type: "chat_delta",
        message_id: "m1",
        session_id: "sess_test",
        part: { type: "text", content: "O prazo prescricional e de 3 anos." },
      });
    });

    act(() => {
      emitWs({ type: "chat_end", message_id: "m1", session_id: "sess_test" });
    });

    // 8. Verificar resposta renderizada
    expect(screen.getByText(/prazo prescricional/)).toBeInTheDocument();
  });
});

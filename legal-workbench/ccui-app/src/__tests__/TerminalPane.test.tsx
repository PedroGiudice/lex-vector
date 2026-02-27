import { render, screen, act } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { TerminalPane } from "../components/TerminalPane";
import { WebSocketProvider } from "../contexts/WebSocketContext";
import type { ServerMessage } from "../types/protocol";

// Captura o handler registrado via onMessage para disparo manual nos testes
let capturedHandler: ((msg: ServerMessage) => void) | null = null;

vi.mock("../contexts/WebSocketContext", () => ({
  useWebSocket: () => ({
    status: "connected",
    retryCount: 0,
    maxRetries: 5,
    send: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    retryManual: vi.fn(),
    onMessage: (handler: (msg: ServerMessage) => void) => {
      capturedHandler = handler;
      return () => { capturedHandler = null; };
    },
  }),
  WebSocketProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe("TerminalPane", () => {
  it("exibe placeholder quando sem output", () => {
    render(<TerminalPane channel="main" />);
    expect(screen.getByText(/aguardando output/i)).toBeInTheDocument();
  });

  it("exibe output quando recebe mensagem do canal correto", () => {
    render(<TerminalPane channel="main" />);

    act(() => {
      capturedHandler?.({
        type: "output",
        channel: "main",
        data: "Hello from Claude\n",
      });
    });

    expect(screen.getByText(/Hello from Claude/)).toBeInTheDocument();
  });

  it("ignora mensagens de outros canais", () => {
    render(<TerminalPane channel="main" />);

    act(() => {
      capturedHandler?.({
        type: "output",
        channel: "researcher",
        data: "Mensagem do researcher",
      });
    });

    expect(screen.queryByText(/Mensagem do researcher/)).not.toBeInTheDocument();
    expect(screen.getByText(/aguardando output/i)).toBeInTheDocument();
  });

  it("remove sequencias ANSI do output", () => {
    render(<TerminalPane channel="main" />);

    act(() => {
      capturedHandler?.({
        type: "output",
        channel: "main",
        data: "\x1b[32mTexto verde\x1b[0m",
      });
    });

    expect(screen.getByText("Texto verde")).toBeInTheDocument();
    // Nao deve conter o escape code bruto
    expect(screen.queryByText(/\x1b/)).not.toBeInTheDocument();
  });

  it("acumula multiplas mensagens", () => {
    render(<TerminalPane channel="main" />);

    act(() => {
      capturedHandler?.({ type: "output", channel: "main", data: "Linha 1\n" });
      capturedHandler?.({ type: "output", channel: "main", data: "Linha 2\n" });
      capturedHandler?.({ type: "output", channel: "main", data: "Linha 3\n" });
    });

    const pre = screen.getByLabelText(/saida do canal main/i);
    expect(pre.textContent).toContain("Linha 1");
    expect(pre.textContent).toContain("Linha 2");
    expect(pre.textContent).toContain("Linha 3");
  });

  it("limpa output ao mudar de canal", () => {
    const { rerender } = render(<TerminalPane channel="main" />);

    act(() => {
      capturedHandler?.({ type: "output", channel: "main", data: "Output antigo" });
    });

    expect(screen.getByText(/Output antigo/)).toBeInTheDocument();

    rerender(<TerminalPane channel="researcher" />);

    expect(screen.queryByText(/Output antigo/)).not.toBeInTheDocument();
    // Verifica que o placeholder do novo canal aparece (texto com ou sem aspas)
    expect(
      screen.getByLabelText(/saida do canal researcher/i).textContent
    ).toMatch(/researcher/i);
  });
});

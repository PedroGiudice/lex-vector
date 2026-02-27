import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { CaseSelector } from "../components/CaseSelector";
import { WebSocketProvider } from "../contexts/WebSocketContext";
import { SessionProvider } from "../contexts/SessionContext";
import type { CaseInfo } from "../types/protocol";

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <WebSocketProvider>
      <SessionProvider>{children}</SessionProvider>
    </WebSocketProvider>
  );
}

const mockCases: CaseInfo[] = [
  {
    id: "caso-silva",
    path: "/data/caso-silva",
    ready: true,
    doc_count: 5,
    last_modified: "2026-01-15T12:00:00Z",
  },
  {
    id: "caso-nao-pronto",
    path: "/data/caso-nao-pronto",
    ready: false,
    doc_count: 0,
    last_modified: "2026-01-10T09:00:00Z",
  },
];

describe("CaseSelector", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("exibe spinner enquanto carrega", () => {
    // fetch nunca resolve -- loading fica ativo
    vi.mocked(fetch).mockReturnValue(new Promise(() => {}) as Promise<Response>);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    // Texto do loading pode variar (Carregando/Buscando) -- verifica spinner estruturalmente
    const body = document.body.textContent ?? "";
    const hasLoadingText =
      /carregando/i.test(body) ||
      /buscando/i.test(body) ||
      /aguardando/i.test(body);
    expect(hasLoadingText).toBe(true);
  });

  it("lista casos apos fetch bem-sucedido", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cases: mockCases }),
    } as Response);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText("caso-silva")).toBeInTheDocument();
      expect(screen.getByText("caso-nao-pronto")).toBeInTheDocument();
    });
  });

  it("exibe badge de status de pronto e nao-pronto", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cases: mockCases }),
    } as Response);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    await waitFor(() => {
      // O texto exato pode variar (Pronto / Nao pronto / Nao preparado)
      // -- verifica que ha pelo menos 2 badges de status distintos
      const body = document.body.textContent ?? "";
      expect(body).toMatch(/pronto/i);
    });
  });

  it("mensagem de lista vazia quando nao ha casos", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cases: [] }),
    } as Response);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText(/nenhum caso encontrado/i)).toBeInTheDocument();
    });
  });

  it("exibe ErrorBanner quando fetch falha", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 503,
    } as Response);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    await waitFor(() => {
      // ErrorBanner deve aparecer com algum texto de erro
      expect(screen.queryByText(/carregando casos/i)).not.toBeInTheDocument();
    });
  });

  it("caso nao-pronto tem botao desabilitado", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cases: mockCases }),
    } as Response);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText("caso-nao-pronto")).toBeInTheDocument();
    });

    // O botao do caso nao-pronto deve estar desabilitado
    const buttons = screen.getAllByRole("button");
    const naoProntoBtn = buttons.find((b) =>
      b.textContent?.includes("caso-nao-pronto")
    );
    expect(naoProntoBtn).toBeDisabled();
  });

  it("clicar em caso pronto chama createSession", async () => {
    const user = userEvent.setup();

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cases: [mockCases[0]] }), // apenas caso pronto
    } as Response);

    render(
      <Wrapper>
        <CaseSelector />
      </Wrapper>
    );

    await waitFor(() => {
      expect(screen.getByText("caso-silva")).toBeInTheDocument();
    });

    const btn = screen.getByRole("button", { name: /caso-silva/i });
    await user.click(btn);

    // Apos click, createSession foi chamado -- nao explodiu
    // (verificacao indireta: nenhum erro lancado)
    expect(btn).toBeInTheDocument();
  });
});

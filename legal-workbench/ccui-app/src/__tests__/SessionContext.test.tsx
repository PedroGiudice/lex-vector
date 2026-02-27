import { renderHook, act } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { SessionProvider, useSession } from "../contexts/SessionContext";
import { WebSocketProvider } from "../contexts/WebSocketContext";

// Wrapper com ambos os providers necessarios
function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <WebSocketProvider>
      <SessionProvider>{children}</SessionProvider>
    </WebSocketProvider>
  );
}

describe("SessionContext", () => {
  it("estado inicial: sem caso, sem sessao, sem canais", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    expect(result.current.caseId).toBeNull();
    expect(result.current.sessionId).toBeNull();
    expect(result.current.channels).toHaveLength(0);
  });

  it("selectCase define caseId sem criar sessao WS", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    act(() => {
      result.current.selectCase("caso-001");
    });

    expect(result.current.caseId).toBe("caso-001");
    expect(result.current.sessionId).toBeNull();
  });

  it("addChannel adiciona canal e nao duplica", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    act(() => {
      result.current.addChannel({ name: "researcher", pane_id: "%5" });
    });

    expect(result.current.channels).toHaveLength(1);
    expect(result.current.channels[0].name).toBe("researcher");

    act(() => {
      result.current.addChannel({ name: "researcher", pane_id: "%5" });
    });

    expect(result.current.channels).toHaveLength(1);
  });

  it("removeChannel remove canal pelo nome", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    act(() => {
      result.current.addChannel({ name: "researcher", pane_id: "%5" });
      result.current.addChannel({ name: "coder", pane_id: "%6" });
    });

    expect(result.current.channels).toHaveLength(2);

    act(() => {
      result.current.removeChannel("researcher");
    });

    expect(result.current.channels).toHaveLength(1);
    expect(result.current.channels[0].name).toBe("coder");
  });

  it("reset limpa todo o estado", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    act(() => {
      result.current.selectCase("caso-001");
      result.current.addChannel({ name: "main", pane_id: "main" });
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.caseId).toBeNull();
    expect(result.current.sessionId).toBeNull();
    expect(result.current.channels).toHaveLength(0);
  });

  it("useSession fora do provider lanca erro", () => {
    expect(() => {
      renderHook(() => useSession());
    }).toThrow("useSession deve ser usado dentro de SessionProvider");
  });
});

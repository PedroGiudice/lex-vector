import { renderHook, act } from "@testing-library/react";
import React from "react";
import { describe, it, expect } from "vitest";
import { SessionProvider, useSession } from "../contexts/SessionContext";
import { WebSocketProvider } from "../contexts/WebSocketContext";

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <WebSocketProvider>
      <SessionProvider>{children}</SessionProvider>
    </WebSocketProvider>
  );
}

describe("SessionContext", () => {
  it("estado inicial: sem caso, sem sessao", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    expect(result.current.caseId).toBeNull();
    expect(result.current.sessionId).toBeNull();
  });

  it("selectCase define caseId sem criar sessao WS", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    act(() => {
      result.current.selectCase("caso-001");
    });

    expect(result.current.caseId).toBe("caso-001");
    expect(result.current.sessionId).toBeNull();
  });

  it("reset limpa todo o estado", () => {
    const { result } = renderHook(() => useSession(), { wrapper });

    act(() => {
      result.current.selectCase("caso-001");
    });

    act(() => {
      result.current.reset();
    });

    expect(result.current.caseId).toBeNull();
    expect(result.current.sessionId).toBeNull();
  });

  it("useSession fora do provider lanca erro", () => {
    expect(() => {
      renderHook(() => useSession());
    }).toThrow("useSession deve ser usado dentro de SessionProvider");
  });
});

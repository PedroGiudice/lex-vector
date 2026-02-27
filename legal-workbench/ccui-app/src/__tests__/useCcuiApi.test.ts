import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { useCases, useHealth, useSessionChannels } from "../hooks/useCcuiApi";

describe("useHealth", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("retorna true quando backend responde 'ok'", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      text: async () => "ok",
    } as Response);

    const { result } = renderHook(() => useHealth());

    let healthy: boolean | undefined;
    await act(async () => {
      healthy = await result.current.check();
    });

    expect(healthy).toBe(true);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("retorna false quando fetch falha", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("Connection refused"));

    const { result } = renderHook(() => useHealth());

    let healthy: boolean | undefined;
    await act(async () => {
      healthy = await result.current.check();
    });

    expect(healthy).toBe(false);
    expect(result.current.error).toMatch(/Connection refused/);
  });
});

describe("useCases", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("busca lista de casos corretamente", async () => {
    const mockCases = [
      { id: "caso-001", path: "/data/caso-001", ready: true, doc_count: 3, last_modified: "2026-01-01T00:00:00Z" },
      { id: "caso-002", path: "/data/caso-002", ready: false, doc_count: 0, last_modified: "2026-01-02T00:00:00Z" },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ cases: mockCases }),
    } as Response);

    const { result } = renderHook(() => useCases());

    await act(async () => {
      await result.current.fetchCases();
    });

    expect(result.current.cases).toHaveLength(2);
    expect(result.current.cases[0].id).toBe("caso-001");
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it("define error quando fetch falha", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 500,
    } as Response);

    const { result } = renderHook(() => useCases());

    await act(async () => {
      await result.current.fetchCases();
    });

    expect(result.current.cases).toHaveLength(0);
    expect(result.current.error).toBeTruthy();
  });

  it("loading e true durante fetch", async () => {
    let resolvePromise!: (v: unknown) => void;
    vi.mocked(fetch).mockReturnValueOnce(
      new Promise((r) => { resolvePromise = r; }) as Promise<Response>
    );

    const { result } = renderHook(() => useCases());

    act(() => {
      result.current.fetchCases();
    });

    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolvePromise({ ok: true, json: async () => ({ cases: [] }) });
    });

    await waitFor(() => expect(result.current.loading).toBe(false));
  });
});

describe("useSessionChannels", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("busca canais de uma sessao", async () => {
    const mockChannels = [
      { name: "main", pane_id: "main" },
      { name: "researcher", pane_id: "%5", color: "#4ade80" },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ channels: mockChannels }),
    } as Response);

    const { result } = renderHook(() => useSessionChannels());

    await act(async () => {
      await result.current.fetchChannels("sess-abc");
    });

    expect(result.current.channels).toHaveLength(2);
    expect(result.current.channels[1].name).toBe("researcher");
  });
});

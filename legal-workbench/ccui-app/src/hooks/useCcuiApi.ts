/**
 * Fetch wrappers para os endpoints REST do ccui-backend.
 * Base URL: localhost:8005 (dentro do SSH tunnel).
 */

import { useState, useCallback } from "react";
import type { CaseInfo, Channel, SessionInfo } from "../types/protocol";

const API_BASE = "http://localhost:8005";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`Erro ${res.status} ao acessar ${path}`);
  }
  return res.json() as Promise<T>;
}

// ---- Health ----

export function useHealth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const check = useCallback(async (): Promise<boolean> => {
    setLoading(true);
    setError(null);
    try {
      const text = await fetch(`${API_BASE}/health`).then((r) => r.text());
      return text.trim() === "ok";
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha no health check";
      setError(msg);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { check, loading, error };
}

// ---- Cases ----

export function useCases() {
  const [cases, setCases] = useState<CaseInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ cases: unknown[] }>("/api/cases");
      const normalizeCase = (c: Record<string, unknown>): CaseInfo => ({
        ...(c as unknown as CaseInfo),
        last_modified:
          typeof c.last_modified === "number"
            ? new Date(c.last_modified * 1000).toISOString()
            : (c.last_modified as string),
      });
      setCases((data.cases ?? []).map((c) => normalizeCase(c as Record<string, unknown>)));
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao carregar casos";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  return { cases, loading, error, fetchCases };
}

// ---- Sessions ----

export function useSessions() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSessions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ sessions: (string | SessionInfo)[] }>("/api/sessions");
      const raw = data.sessions ?? [];
      setSessions(
        raw.map((s) =>
          typeof s === "string" ? { session_id: s } : s
        )
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao carregar sessoes";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  const renameSession = useCallback(async (id: string, name: string) => {
    const res = await fetch(`${API_BASE}/api/sessions/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error(`Erro ${res.status} ao renomear sessao`);
    await fetchSessions();
  }, [fetchSessions]);

  const deleteSession = useCallback(async (id: string) => {
    const res = await fetch(`${API_BASE}/api/sessions/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error(`Erro ${res.status} ao deletar sessao`);
    await fetchSessions();
  }, [fetchSessions]);

  return { sessions, loading, error, fetchSessions, renameSession, deleteSession };
}

// ---- Channels de uma sessao ----

export function useSessionChannels() {
  const [channels, setChannels] = useState<Channel[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChannels = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<{ channels: Channel[] }>(
        `/api/sessions/${sessionId}/channels`
      );
      setChannels(data.channels);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao carregar canais";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  return { channels, loading, error, fetchChannels };
}

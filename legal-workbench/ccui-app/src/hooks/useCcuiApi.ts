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
      const data = await apiFetch<{ cases: CaseInfo[] }>("/api/cases");
      setCases(data.cases);
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
      const data = await apiFetch<{ sessions: SessionInfo[] }>("/api/sessions");
      setSessions(data.sessions);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao carregar sessoes";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  return { sessions, loading, error, fetchSessions };
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

import type { SearchRequest, SearchResponse, DocumentResponse, HealthResponse, FiltersResponse } from './types.ts';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  search: (body: SearchRequest) =>
    fetchJson<SearchResponse>('/api/search', { method: 'POST', body: JSON.stringify(body) }),
  document: (docId: string) =>
    fetchJson<DocumentResponse>(`/api/document/${docId}`),
  health: () => fetchJson<HealthResponse>('/api/health'),
  filters: () => fetchJson<FiltersResponse>('/api/filters'),
};

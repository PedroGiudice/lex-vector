import axios from 'axios';
import { getApiBaseUrl } from '@/lib/tauri';

const api = axios.create({
  baseURL: `${getApiBaseUrl()}/api/stj/api/v1`,
  timeout: 30000,
});

export interface SearchParams {
  termo: string;
  orgao?: string;
  dias?: number;
  limit?: number;
  offset?: number;
  campo?: 'ementa' | 'texto_integral';
}

export interface AcordaoSummary {
  id: string;
  numero_processo: string;
  orgao_julgador: string;
  tipo_decisao?: string;
  relator?: string;
  data_publicacao?: string;
  data_julgamento?: string;
  ementa?: string;
  resultado_julgamento?: string;
}

export interface SearchResponse {
  total: number;
  limit: number;
  offset: number;
  resultados: AcordaoSummary[];
}

export interface AcordaoDetail extends AcordaoSummary {
  texto_integral?: string;
  classe_processual?: string;
  assuntos?: string;
  fonte_url?: string;
}

export interface StatsResponse {
  total_acordaos: number;
  por_orgao: Record<string, number>;
  por_tipo: Record<string, number>;
  ultimos_30_dias: number;
}

// Sync types
export type SyncPeriod = '30' | '90' | '365' | 'desde_2022' | 'custom';

export interface SyncParams {
  period: SyncPeriod;
  dataInicio?: string; // ISO date string for custom period
  dataFim?: string; // ISO date string for custom period
  orgaos?: string[]; // Optional filter by orgaos
}

export type SyncStatusType = 'idle' | 'downloading' | 'processing' | 'complete' | 'error';

export interface SyncProgress {
  downloaded: number;
  processed: number;
  inserted: number;
  duplicates: number;
  errors: number;
  percent?: number;
  currentPage?: number;
  totalPages?: number;
  message?: string;
}

export interface SyncStatusResponse {
  status: SyncStatusType;
  progress: SyncProgress;
  startedAt?: string;
  finishedAt?: string;
  error?: string;
}

export interface SyncTriggerResponse {
  success: boolean;
  message: string;
  taskId?: string;
}

// Export types
export type ExportFormat = 'csv' | 'json';

export interface ExportParams {
  termo?: string;
  orgao?: string;
  dias?: number;
  campo?: 'ementa' | 'texto_integral';
  format: ExportFormat;
}

export const stjApi = {
  search: (params: SearchParams) => api.get<SearchResponse>('/search', { params }),

  getCase: (id: string) => api.get<AcordaoDetail>(`/case/${id}`),

  getStats: () => api.get<StatsResponse>('/stats'),

  health: () => api.get('/health'),

  // Sync operations
  triggerSync: (params: SyncParams) => api.post<SyncTriggerResponse>('/sync', params),

  getSyncStatus: () => api.get<SyncStatusResponse>('/sync/status'),

  cancelSync: () => api.post<{ success: boolean; message: string }>('/sync/cancel'),

  // Export operations
  exportResults: (params: ExportParams) => {
    const { format, ...searchParams } = params;
    return api.get(`/export/${format}`, {
      params: searchParams,
      responseType: 'blob',
    });
  },
};

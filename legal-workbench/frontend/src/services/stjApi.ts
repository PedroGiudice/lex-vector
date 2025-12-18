import axios from 'axios';

const api = axios.create({
  baseURL: '/api/stj/api/v1',
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

export const stjApi = {
  search: (params: SearchParams) =>
    api.get<SearchResponse>('/search', { params }),

  getCase: (id: string) =>
    api.get<AcordaoDetail>(`/case/${id}`),

  getStats: () =>
    api.get<StatsResponse>('/stats'),

  health: () =>
    api.get('/health'),
};

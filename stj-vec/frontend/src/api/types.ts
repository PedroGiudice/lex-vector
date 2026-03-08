export interface SearchRequest {
  query: string;
  limit?: number;
  filters?: SearchFilters;
}

export interface SearchFilters {
  ministro?: string;
  tipo?: string;
  classe?: string;
  orgao_julgador?: string;
  data_from?: string;
  data_to?: string;
}

export interface Scores {
  dense: number;
  sparse: number;
  rrf: number;
  dense_rank: number;
  sparse_rank: number;
}

export interface SearchResultItem {
  chunk_id: string;
  content: string;
  chunk_index: number;
  doc_id: string;
  processo: string;
  classe: string;
  ministro: string;
  orgao_julgador: string;
  data_julgamento: string;
  tipo: string;
  assuntos: string;
  scores: Scores;
}

export interface QueryInfo {
  embedding_ms: number;
  search_ms: number;
  metadata_ms: number;
  total_ms: number;
  dense_candidates: number;
  sparse_candidates: number;
  pre_filter_count: number;
  post_filter_count: number;
}

export interface SearchResponse {
  results: SearchResultItem[];
  query_info: QueryInfo;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  token_count: number;
}

export interface DocumentMeta {
  id: string;
  processo: string;
  classe: string;
  ministro: string;
  orgao_julgador: string;
  data_julgamento: string;
  data_publicacao: string;
  tipo: string;
  assuntos: string;
}

export interface DocumentResponse {
  document: DocumentMeta;
  chunks: DocumentChunk[];
  total_chunks: number;
}

export interface HealthResponse {
  status: string;
  qdrant: boolean;
  sqlite: boolean;
  model_loaded: boolean;
  collection_points: number;
  uptime_secs: number;
}

export interface FiltersResponse {
  ministros: string[];
  classes: string[];
  tipos: string[];
  orgaos_julgadores: string[];
}

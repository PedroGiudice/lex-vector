use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct SearchRequest {
    pub query: String,
    pub limit: Option<usize>,
    pub filters: Option<SearchFilters>,
}

#[derive(Debug, Deserialize, Default, Clone)]
pub struct SearchFilters {
    pub ministro: Option<String>,
    pub tipo: Option<String>,
    pub classe: Option<String>,
    pub orgao_julgador: Option<String>,
    pub data_from: Option<String>,
    pub data_to: Option<String>,
}

impl SearchFilters {
    pub fn is_empty(&self) -> bool {
        self.ministro.is_none()
            && self.tipo.is_none()
            && self.classe.is_none()
            && self.orgao_julgador.is_none()
            && self.data_from.is_none()
            && self.data_to.is_none()
    }
}

#[derive(Debug, Serialize)]
pub struct SearchResponse {
    pub results: Vec<SearchResultItem>,
    pub query_info: QueryInfo,
}

#[derive(Debug, Serialize)]
pub struct SearchResultItem {
    pub chunk_id: String,
    pub content: String,
    pub chunk_index: i64,
    pub doc_id: String,
    pub processo: String,
    pub classe: String,
    pub ministro: String,
    pub orgao_julgador: String,
    pub data_julgamento: String,
    pub tipo: String,
    pub assuntos: String,
    pub scores: Scores,
}

#[derive(Debug, Serialize)]
pub struct Scores {
    pub dense: f32,
    pub sparse: f32,
    pub rrf: f64,
    pub dense_rank: usize,
    pub sparse_rank: usize,
}

#[derive(Debug, Serialize)]
pub struct QueryInfo {
    pub embedding_ms: u64,
    pub search_ms: u64,
    pub metadata_ms: u64,
    pub total_ms: u64,
    pub dense_candidates: usize,
    pub sparse_candidates: usize,
    pub pre_filter_count: usize,
    pub post_filter_count: usize,
}

#[derive(Debug, Serialize)]
pub struct DocumentResponse {
    pub document: DocumentMeta,
    pub chunks: Vec<DocumentChunk>,
    pub total_chunks: usize,
}

#[derive(Debug, Serialize)]
pub struct DocumentMeta {
    pub id: String,
    pub processo: String,
    pub classe: String,
    pub ministro: String,
    pub orgao_julgador: String,
    pub data_julgamento: String,
    pub data_publicacao: String,
    pub tipo: String,
    pub assuntos: String,
}

#[derive(Debug, Serialize)]
pub struct DocumentChunk {
    pub id: String,
    pub chunk_index: i64,
    pub content: String,
    pub token_count: i64,
}

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub qdrant: bool,
    pub sqlite: bool,
    pub model_loaded: bool,
    pub model_name: String,
    pub collection_points: u64,
    pub document_count: u64,
    pub uptime_secs: u64,
}

#[derive(Debug, Serialize, Clone)]
pub struct FiltersResponse {
    pub ministros: Vec<String>,
    pub classes: Vec<String>,
    pub tipos: Vec<String>,
    pub orgaos_julgadores: Vec<String>,
}

/// Metadados de chunk enriquecidos com dados do documento (resultado do JOIN).
#[derive(Debug)]
pub struct ChunkWithMetadata {
    pub chunk_id: String,
    pub content: String,
    pub chunk_index: i64,
    pub doc_id: String,
    pub processo: String,
    pub classe: String,
    pub ministro: String,
    pub orgao_julgador: String,
    pub data_julgamento: String,
    pub tipo: String,
    pub assuntos: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_search_request_deserialization() {
        let json = r#"{"query": "dano moral"}"#;
        let req: SearchRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.query, "dano moral");
        assert!(req.limit.is_none());
        assert!(req.filters.is_none());
    }

    #[test]
    fn test_search_request_with_filters() {
        let json = r#"{
            "query": "dano moral",
            "limit": 10,
            "filters": {"ministro": "NANCY ANDRIGHI", "tipo": "acordao"}
        }"#;
        let req: SearchRequest = serde_json::from_str(json).unwrap();
        assert_eq!(req.limit, Some(10));
        let f = req.filters.unwrap();
        assert_eq!(f.ministro.as_deref(), Some("NANCY ANDRIGHI"));
        assert!(!f.is_empty());
    }

    #[test]
    fn test_scores_serialization() {
        let scores = Scores {
            dense: 0.847,
            sparse: 12.34,
            rrf: 0.0328,
            dense_rank: 3,
            sparse_rank: 7,
        };
        let json = serde_json::to_string(&scores).unwrap();
        assert!(json.contains("dense_rank"));
        assert!(json.contains("sparse_rank"));
    }
}

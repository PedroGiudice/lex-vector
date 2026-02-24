use serde::{Deserialize, Serialize};

/// Documento STJ (metadados do acordao/decisao)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub id: String,
    pub processo: Option<String>,
    pub classe: Option<String>,
    pub ministro: Option<String>,
    pub orgao_julgador: Option<String>,
    pub data_publicacao: Option<String>,
    pub data_julgamento: Option<String>,
    pub assuntos: Option<String>,
    pub teor: Option<String>,
    pub tipo: Option<String>,
    pub chunk_count: i32,
    pub source_file: Option<String>,
}

/// Chunk de texto com posicao no documento
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Chunk {
    pub id: String,
    pub doc_id: String,
    pub chunk_index: i32,
    pub content: String,
    pub token_count: i32,
}

/// Resultado de busca: chunk + score + metadados do documento
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub score: f64,
    pub chunk: Chunk,
    pub document: Document,
}

/// Filtros opcionais para busca
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct SearchFilters {
    pub ministro: Option<String>,
    pub tipo: Option<String>,
    pub orgao_julgador: Option<String>,
    pub data_from: Option<String>,
    pub data_to: Option<String>,
}

/// Estatisticas do banco
#[derive(Debug, Serialize, Deserialize)]
pub struct DbStats {
    pub document_count: i64,
    pub chunk_count: i64,
    pub embedding_count: i64,
    pub ingest_pending: i64,
    pub ingest_chunked: i64,
    pub ingest_done: i64,
}

/// Status de ingestion de um arquivo
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IngestStatus {
    pub source_file: String,
    pub status: String,
    pub doc_count: i32,
    pub chunk_count: i32,
    pub error: Option<String>,
}

/// Metadado bruto do JSON do STJ (camelCase do JSON original)
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StjMetadata {
    pub seq_documento: i64,
    pub data_publicacao: Option<i64>,
    pub tipo_documento: Option<String>,
    pub numero_registro: Option<String>,
    pub processo: Option<String>,
    pub ministro: Option<String>,
    pub recurso: Option<String>,
    pub teor: Option<String>,
    pub assuntos: Option<String>,
}

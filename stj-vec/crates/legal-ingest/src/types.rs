use serde::{Deserialize, Serialize};

/// Documento legal do corpus (CF, acordaos TCU, decretos TESEMO)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LegalDocument {
    pub id: String,
    pub tipo: String,
    pub titulo: String,
    pub texto: String,
    pub fonte: String,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub data_publicacao: Option<String>,
    #[serde(default)]
    pub metadata: serde_json::Value,
}

/// Chunk de texto legal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LegalChunk {
    pub id: String,
    pub doc_id: String,
    pub chunk_index: i32,
    pub content: String,
    pub token_count: i32,
}

/// Fonte detectada pelo scanner
#[derive(Debug, Clone)]
pub struct CorpusSource {
    pub name: String,
    pub source_type: SourceType,
    pub files: Vec<std::path::PathBuf>,
    pub doc_count: usize,
}

#[derive(Debug, Clone, PartialEq)]
pub enum SourceType {
    Constituicao,
    AcordaoTcu,
    DecretoTesemo,
}

/// Estatisticas do banco
#[derive(Debug, Serialize)]
pub struct DbStats {
    pub document_count: i64,
    pub chunk_count: i64,
    pub embedding_count: i64,
    pub sources: Vec<SourceStats>,
}

#[derive(Debug, Serialize)]
pub struct SourceStats {
    pub source: String,
    pub status: String,
    pub doc_count: i32,
    pub chunk_count: i32,
}

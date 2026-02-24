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

/// Metadado bruto do JSON do STJ (campo names variam entre sources)
#[derive(Debug, Clone, Deserialize)]
pub struct StjMetadata {
    #[serde(alias = "seqDocumento", alias = "SeqDocumento")]
    pub seq_documento: i64,
    #[serde(alias = "dataPublicacao", alias = "DataPublicacao", default, deserialize_with = "deserialize_date_flexible")]
    pub data_publicacao: Option<String>,
    #[serde(alias = "tipoDocumento", alias = "TipoDocumento")]
    pub tipo_documento: Option<String>,
    #[serde(alias = "numeroRegistro", alias = "NumeroRegistro")]
    pub numero_registro: Option<String>,
    #[serde(alias = "processo", alias = "Processo")]
    pub processo: Option<String>,
    #[serde(alias = "NM_MINISTRO", alias = "nM_MINISTRO", alias = "ministro")]
    pub ministro: Option<String>,
    #[serde(alias = "recurso", alias = "Recurso")]
    pub recurso: Option<String>,
    #[serde(alias = "teor", alias = "Teor")]
    pub teor: Option<String>,
    #[serde(alias = "assuntos", alias = "Assuntos")]
    pub assuntos: Option<String>,
}

/// Aceita data como string ("2024-04-03") ou epoch i64, retorna sempre Option<String>.
fn deserialize_date_flexible<'de, D>(deserializer: D) -> Result<Option<String>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    use serde::de;

    struct DateVisitor;
    impl<'de> de::Visitor<'de> for DateVisitor {
        type Value = Option<String>;
        fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
            f.write_str("string date or integer epoch")
        }
        fn visit_str<E: de::Error>(self, v: &str) -> Result<Self::Value, E> {
            Ok(Some(v.to_string()))
        }
        fn visit_i64<E: de::Error>(self, v: i64) -> Result<Self::Value, E> {
            Ok(Some(v.to_string()))
        }
        fn visit_u64<E: de::Error>(self, v: u64) -> Result<Self::Value, E> {
            Ok(Some(v.to_string()))
        }
        fn visit_none<E: de::Error>(self) -> Result<Self::Value, E> {
            Ok(None)
        }
        fn visit_unit<E: de::Error>(self) -> Result<Self::Value, E> {
            Ok(None)
        }
    }

    deserializer.deserialize_any(DateVisitor)
}

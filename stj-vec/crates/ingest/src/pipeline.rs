use std::collections::HashMap;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use indicatif::{ProgressBar, ProgressStyle};
use tracing::info;

use stj_vec_core::chunker::chunk_legal_text;
use stj_vec_core::config::AppConfig;
use stj_vec_core::storage::Storage;
use stj_vec_core::types::{Chunk, DbStats, Document, StjMetadata};

use crate::scanner::{find_new_sources, scan_integras_dir, SourceDir};

/// Pipeline de ingestion: scan, chunk, embed.
pub struct Pipeline {
    storage: Storage,
    config: AppConfig,
    integras_dir: PathBuf,
    metadata_dir: PathBuf,
}

impl Pipeline {
    pub fn new(config: AppConfig) -> Result<Self> {
        let integras_dir = PathBuf::from(&config.data.integras_dir);
        let metadata_dir = PathBuf::from(&config.data.metadata_dir);
        let storage = Storage::open(&config.data.db_path, config.embedding.dim)?;
        Ok(Self {
            storage,
            config,
            integras_dir,
            metadata_dir,
        })
    }

    /// Scan integras dir, registra novos como "pending".
    pub fn scan(&self) -> Result<Vec<SourceDir>> {
        let all = scan_integras_dir(&self.integras_dir)?;
        let new = find_new_sources(&all, &self.storage)?;
        for s in &new {
            self.storage
                .set_ingest_status(&s.name, "pending", 0, 0)?;
        }
        info!(total = all.len(), new = new.len(), "scan complete");
        Ok(all)
    }

    /// Chunk sources com status "pending".
    pub fn chunk_pending(&self) -> Result<()> {
        let pending = self.storage.list_ingest_by_status("pending")?;
        if pending.is_empty() {
            info!("no pending sources to chunk");
            return Ok(());
        }

        for ingest in &pending {
            let source_name = &ingest.source_file;
            let source_path = self.integras_dir.join(source_name);
            if !source_path.is_dir() {
                tracing::warn!(source = %source_name, "source dir not found, skipping");
                continue;
            }

            let metadata = load_metadata(&self.metadata_dir, source_name)?;

            let txt_files: Vec<_> = std::fs::read_dir(&source_path)?
                .filter_map(|e| e.ok())
                .filter(|e| {
                    e.path()
                        .extension()
                        .is_some_and(|ext| ext.eq_ignore_ascii_case("txt"))
                })
                .collect();

            let pb = ProgressBar::new(txt_files.len() as u64);
            pb.set_style(
                ProgressStyle::default_bar()
                    .template("[{elapsed_precise}] {bar:40} {pos}/{len} {msg}")
                    .expect("valid template"),
            );
            pb.set_message(source_name.clone());

            let mut doc_count: i32 = 0;
            let mut total_chunks: i32 = 0;

            for entry in &txt_files {
                let file_path = entry.path();
                let stem = file_path
                    .file_stem()
                    .unwrap_or_default()
                    .to_string_lossy()
                    .into_owned();

                let content = std::fs::read_to_string(&file_path)
                    .with_context(|| format!("falha ao ler {}", file_path.display()))?;

                let chunk_output =
                    chunk_legal_text(&content, &stem, &self.config.chunking);

                // Buscar metadata pelo seqDocumento (nome do arquivo sem .txt)
                let seq: Option<i64> = stem.parse().ok();
                let meta = seq.and_then(|s| metadata.get(&s));

                let doc = Document {
                    id: stem.clone(),
                    processo: meta
                        .and_then(|m| m.processo.as_deref())
                        .map(|s| s.trim().to_string()),
                    classe: None,
                    ministro: meta
                        .and_then(|m| m.ministro.clone()),
                    orgao_julgador: None,
                    data_publicacao: meta
                        .and_then(|m| m.data_publicacao)
                        .map(epoch_ms_to_date),
                    data_julgamento: None,
                    assuntos: meta.and_then(|m| m.assuntos.clone()),
                    teor: meta.and_then(|m| m.teor.clone()),
                    tipo: meta.and_then(|m| m.tipo_documento.clone()),
                    chunk_count: 0,
                    source_file: Some(source_name.clone()),
                };

                self.storage.insert_document(&doc)?;

                let chunks: Vec<Chunk> = chunk_output
                    .chunks
                    .iter()
                    .map(|c| Chunk {
                        id: c.id.clone(),
                        doc_id: stem.clone(),
                        chunk_index: c.chunk_index as i32,
                        content: c.content.clone(),
                        token_count: c.token_count as i32,
                    })
                    .collect();

                let n = chunks.len() as i32;
                self.storage.insert_chunks(&chunks)?;
                self.storage.update_document_chunk_count(&stem)?;

                doc_count += 1;
                total_chunks += n;
                pb.inc(1);
            }

            pb.finish_with_message(format!(
                "{source_name}: {doc_count} docs, {total_chunks} chunks"
            ));

            self.storage
                .set_ingest_status(source_name, "chunked", doc_count, total_chunks)?;
        }

        Ok(())
    }

    /// Placeholder para embedding.
    pub fn embed_pending(&self) -> Result<()> {
        info!("embedding not configured, skipping");
        Ok(())
    }

    /// Estatisticas do banco.
    pub fn stats(&self) -> Result<DbStats> {
        self.storage.stats()
    }

    /// Reset de um source para reprocessamento.
    pub fn reset(&self, source: &str) -> Result<()> {
        self.storage.reset_ingest(source)
    }
}

/// Converte epoch milliseconds para "YYYY-MM-DD".
fn epoch_ms_to_date(ms: i64) -> String {
    let secs = ms / 1000;
    let dt = chrono::DateTime::from_timestamp(secs, 0).unwrap_or_default();
    dt.format("%Y-%m-%d").to_string()
}

/// Carrega metadata JSON de um source.
fn load_metadata(
    metadata_dir: &Path,
    source_name: &str,
) -> Result<HashMap<i64, StjMetadata>> {
    let path = metadata_dir.join(format!("metadados{source_name}.json"));
    if !path.exists() {
        return Ok(HashMap::new());
    }
    let content = std::fs::read_to_string(&path)
        .with_context(|| format!("falha ao ler metadata {}", path.display()))?;
    let items: Vec<StjMetadata> = serde_json::from_str(&content)
        .with_context(|| format!("falha ao parsear metadata {}", path.display()))?;
    Ok(items.into_iter().map(|m| (m.seq_documento, m)).collect())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_epoch_ms_to_date() {
        // 2022-03-15 em epoch ms (aprox)
        assert_eq!(epoch_ms_to_date(1_647_302_400_000), "2022-03-15");
    }

    #[test]
    fn test_pipeline_scan_and_chunk() {
        let dir = tempdir().unwrap();
        let integras = dir.path().join("integras");
        let metadata = dir.path().join("metadata");
        fs::create_dir_all(integras.join("202203")).unwrap();
        fs::create_dir_all(&metadata).unwrap();

        // Criar 3 arquivos TXT fake
        for i in 1..=3 {
            fs::write(
                integras.join(format!("202203/{i}.txt")),
                "DECISAO<br>Texto do documento. Conteudo suficiente para passar o filtro de tokens minimo no chunker.",
            )
            .unwrap();
        }

        // Criar metadata JSON
        let meta_json = serde_json::json!([
            {"seqDocumento": 1, "processo": "REsp 123  ", "ministro": "NANCY", "tipoDocumento": "ACORDAO"},
            {"seqDocumento": 2, "processo": "AREsp 456", "ministro": "SALOMAO", "tipoDocumento": "DECISAO"}
        ]);
        fs::write(
            metadata.join("metadados202203.json"),
            meta_json.to_string(),
        )
        .unwrap();

        let config = AppConfig {
            data: stj_vec_core::config::DataConfig {
                integras_dir: integras.to_str().unwrap().into(),
                metadata_dir: metadata.to_str().unwrap().into(),
                db_path: dir.path().join("test.db").to_str().unwrap().into(),
            },
            chunking: stj_vec_core::config::ChunkingConfig {
                max_tokens: 512,
                overlap_tokens: 64,
                min_chunk_tokens: 10,
            },
            embedding: stj_vec_core::config::EmbeddingConfig {
                model: String::new(),
                dim: 0,
                provider: String::new(),
                modal: stj_vec_core::config::ModalConfig {
                    endpoint: String::new(),
                    batch_size: 0,
                },
                ollama: stj_vec_core::config::OllamaConfig {
                    url: String::new(),
                    model: String::new(),
                    timeout_secs: 10,
                },
            },
            server: stj_vec_core::config::ServerConfig {
                socket: String::new(),
                port: 0,
                max_results: 20,
                default_threshold: 0.3,
            },
        };

        let pipeline = Pipeline::new(config).unwrap();
        let sources = pipeline.scan().unwrap();
        assert_eq!(sources.len(), 1);

        pipeline.chunk_pending().unwrap();
        let stats = pipeline.stats().unwrap();
        assert_eq!(stats.document_count, 3);
        assert!(stats.chunk_count > 0);

        // Verificar que metadata foi aplicada (doc "1" tem processo trimado)
        let doc1 = pipeline.storage.get_document("1").unwrap().unwrap();
        assert_eq!(doc1.processo.as_deref(), Some("REsp 123"));
        assert_eq!(doc1.tipo.as_deref(), Some("ACORDAO"));
    }
}

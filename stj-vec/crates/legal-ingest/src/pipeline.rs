//! Pipeline de ingestao: scan -> chunk -> embed.

use anyhow::{Context, Result};
use indicatif::{ProgressBar, ProgressStyle};
use tracing::{info, warn};

use crate::chunker::chunk_document;
use crate::config::LegalConfig;
use crate::embedder::OllamaEmbedder;
use crate::scanner::{load_documents, scan_corpus};
use crate::storage::Storage;
use crate::types::{CorpusSource, DbStats};

/// Pipeline orquestra scan, chunking e embedding.
pub struct Pipeline {
    config: LegalConfig,
    storage: Storage,
}

impl Pipeline {
    /// Cria pipeline abrindo storage conforme config.
    pub fn new(config: LegalConfig) -> Result<Self> {
        let storage = Storage::open(&config.data.db_path, config.embedding.dim)
            .context("falha ao abrir storage")?;
        Ok(Self { config, storage })
    }

    /// Escaneia corpus e retorna fontes detectadas.
    pub fn scan(&self) -> Result<Vec<CorpusSource>> {
        let corpus_dir = std::path::Path::new(&self.config.data.corpus_dir);
        scan_corpus(corpus_dir)
    }

    /// Chunka todas as fontes pendentes.
    pub fn chunk_all(&self) -> Result<()> {
        let sources = self.scan()?;
        let pb = ProgressBar::new(sources.len() as u64);
        pb.set_style(
            ProgressStyle::default_bar()
                .template("[{elapsed_precise}] {bar:40} {pos}/{len} {msg}")
                .expect("template valido"),
        );

        for source in &sources {
            pb.set_message(source.name.clone());

            // Verificar status
            let status = self.storage.get_ingest_status(&source.name)?;
            if matches!(status.as_deref(), Some("chunked") | Some("done")) {
                info!(source = %source.name, "ja processado, pulando");
                pb.inc(1);
                continue;
            }

            self.storage
                .set_ingest_status(&source.name, "pending", 0, 0)?;

            let mut total_docs = 0i32;
            let mut total_chunks = 0i32;

            for file in &source.files {
                let docs = load_documents(file)?;
                self.storage
                    .insert_documents_batch(&docs, &source.name)?;
                total_docs += docs.len() as i32;

                for doc in &docs {
                    let chunks =
                        chunk_document(doc, &source.source_type, &self.config.chunking);
                    if !chunks.is_empty() {
                        total_chunks += chunks.len() as i32;
                        self.storage.insert_chunks(&chunks)?;
                    }
                }
            }

            self.storage
                .set_ingest_status(&source.name, "chunked", total_docs, total_chunks)?;
            info!(
                source = %source.name,
                docs = total_docs,
                chunks = total_chunks,
                "chunking completo"
            );
            pb.inc(1);
        }

        pb.finish_with_message("chunking finalizado");
        Ok(())
    }

    /// Gera embeddings para chunks pendentes.
    pub async fn embed_pending(&self) -> Result<()> {
        let ollama = &self.config.embedding.ollama;
        let embedder = OllamaEmbedder::new(
            ollama.url.clone(),
            ollama.model.clone(),
            self.config.embedding.dim,
            ollama.timeout_secs,
        );

        let pending = self.storage.chunks_without_embeddings()?;
        if pending.is_empty() {
            info!("nenhum chunk pendente de embedding");
            return Ok(());
        }

        info!(count = pending.len(), "chunks pendentes de embedding");

        let pb = ProgressBar::new(pending.len() as u64);
        pb.set_style(
            ProgressStyle::default_bar()
                .template("[{elapsed_precise}] {bar:40} {pos}/{len} embeddings")
                .expect("template valido"),
        );

        for chunk in &pending {
            match embedder.embed(&chunk.content).await {
                Ok(embedding) => {
                    if let Err(e) = self.storage.insert_embedding(&chunk.id, &embedding) {
                        warn!(chunk_id = %chunk.id, error = %e, "falha ao salvar embedding");
                    }
                }
                Err(e) => {
                    warn!(chunk_id = %chunk.id, error = %e, "falha ao gerar embedding");
                }
            }
            pb.inc(1);
        }

        pb.finish_with_message("embedding finalizado");
        Ok(())
    }

    /// Retorna estatisticas do banco.
    pub fn stats(&self) -> Result<DbStats> {
        self.storage.stats()
    }
}

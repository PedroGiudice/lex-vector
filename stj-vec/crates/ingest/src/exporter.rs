//! Exporta chunks do SQLite para JSONL (1 arquivo por source).
//! Destino: Modal Volume via `modal volume put`.

use anyhow::{Context, Result};
use std::io::Write;
use std::path::Path;

use stj_vec_core::storage::Storage;

/// Exporta chunks de sources com status "chunked" para JSONL.
/// Retorna (sources_exported, chunks_exported).
pub fn export_chunks_for_modal(
    storage: &Storage,
    output_dir: &Path,
    limit: Option<usize>,
) -> Result<(usize, usize)> {
    std::fs::create_dir_all(output_dir)
        .with_context(|| format!("falha ao criar {}", output_dir.display()))?;

    let sources = storage.list_ingest_by_status("chunked")?;
    let sources_to_process = match limit {
        Some(n) => &sources[..n.min(sources.len())],
        None => &sources,
    };

    let mut total_sources = 0;
    let mut total_chunks = 0;

    for source in sources_to_process {
        let out_path = output_dir.join(format!("{}.jsonl", source.source_file));

        let chunks = get_chunks_by_source(storage, &source.source_file)?;

        if chunks.is_empty() {
            tracing::warn!(source = %source.source_file, "no chunks found, skipping");
            continue;
        }

        let mut file = std::fs::File::create(&out_path)
            .with_context(|| format!("falha ao criar {}", out_path.display()))?;

        for (chunk_id, content) in &chunks {
            let line = serde_json::json!({"id": chunk_id, "content": content});
            writeln!(file, "{line}")?;
        }

        tracing::info!(
            source = %source.source_file,
            chunks = chunks.len(),
            path = %out_path.display(),
            "exported"
        );
        total_sources += 1;
        total_chunks += chunks.len();
    }

    Ok((total_sources, total_chunks))
}

/// Busca chunks de um source (via JOIN documents.source_file -> chunks.doc_id).
fn get_chunks_by_source(storage: &Storage, source: &str) -> Result<Vec<(String, String)>> {
    let docs = storage.list_documents_by_source(source)?;
    let mut all_chunks = Vec::new();

    for doc_id in &docs {
        let chunks = storage.get_chunks_by_doc(doc_id)?;
        for chunk in chunks {
            all_chunks.push((chunk.id, chunk.content));
        }
    }

    Ok(all_chunks)
}

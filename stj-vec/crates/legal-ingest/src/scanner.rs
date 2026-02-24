use crate::types::{CorpusSource, LegalDocument, SourceType};
use anyhow::{Context, Result};
use std::path::Path;
use tracing::info;

pub fn scan_corpus(corpus_dir: &Path) -> Result<Vec<CorpusSource>> {
    let mut sources = Vec::new();

    // abjur/
    let abjur_dir = corpus_dir.join("abjur");
    if abjur_dir.exists() {
        let cf_path = abjur_dir.join("constituicao_federal.json");
        if cf_path.exists() {
            let count = count_json_array(&cf_path)?;
            sources.push(CorpusSource {
                name: "abjur/constituicao_federal".into(),
                source_type: SourceType::Constituicao,
                files: vec![cf_path],
                doc_count: count,
            });
        }
    }

    // huggingface/
    let hf_dir = corpus_dir.join("huggingface");
    if hf_dir.exists() {
        let mut tcu_files = Vec::new();
        let mut tcu_count = 0;
        let mut tesemo_files = Vec::new();
        let mut tesemo_count = 0;

        for entry in std::fs::read_dir(&hf_dir)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if name.starts_with("tcu_batch_") && name.ends_with(".json") {
                tcu_count += count_json_array(&entry.path())?;
                tcu_files.push(entry.path());
            } else if name.starts_with("tesemo_batch_") && name.ends_with(".json") {
                tesemo_count += count_json_array(&entry.path())?;
                tesemo_files.push(entry.path());
            }
        }

        tcu_files.sort();
        tesemo_files.sort();

        if !tcu_files.is_empty() {
            sources.push(CorpusSource {
                name: "huggingface/tcu".into(),
                source_type: SourceType::AcordaoTcu,
                files: tcu_files,
                doc_count: tcu_count,
            });
        }
        if !tesemo_files.is_empty() {
            sources.push(CorpusSource {
                name: "huggingface/tesemo".into(),
                source_type: SourceType::DecretoTesemo,
                files: tesemo_files,
                doc_count: tesemo_count,
            });
        }
    }

    for s in &sources {
        info!(source = %s.name, files = s.files.len(), docs = s.doc_count, "detected corpus source");
    }

    Ok(sources)
}

fn count_json_array(path: &Path) -> Result<usize> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;
    let arr: Vec<serde_json::Value> = serde_json::from_str(&content)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    Ok(arr.len())
}

pub fn load_documents(path: &Path) -> Result<Vec<LegalDocument>> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;
    let docs: Vec<LegalDocument> = serde_json::from_str(&content)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    Ok(docs)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_scan_real_corpus() {
        let corpus = PathBuf::from("/home/opc/.claude/legal-knowledge-base/corpus");
        if !corpus.exists() { return; }
        let sources = scan_corpus(&corpus).unwrap();
        assert_eq!(sources.len(), 3);

        let cf = sources.iter().find(|s| s.source_type == SourceType::Constituicao).unwrap();
        assert_eq!(cf.doc_count, 368);

        let tcu = sources.iter().find(|s| s.source_type == SourceType::AcordaoTcu).unwrap();
        assert_eq!(tcu.doc_count, 5000);
        assert_eq!(tcu.files.len(), 10);

        let tesemo = sources.iter().find(|s| s.source_type == SourceType::DecretoTesemo).unwrap();
        assert_eq!(tesemo.doc_count, 10000);
        assert_eq!(tesemo.files.len(), 20);
    }

    #[test]
    fn test_load_cf_documents() {
        let path = PathBuf::from("/home/opc/.claude/legal-knowledge-base/corpus/abjur/constituicao_federal.json");
        if !path.exists() { return; }
        let docs = load_documents(&path).unwrap();
        assert_eq!(docs.len(), 368);
        assert_eq!(docs[0].id, "cf_art_1");
        assert_eq!(docs[0].tipo, "constituicao");
        assert!(!docs[0].texto.is_empty());
    }
}

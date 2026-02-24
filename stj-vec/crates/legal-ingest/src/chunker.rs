//! Chunker para documentos legais com estrategias por tipo de fonte.

use crate::config::ChunkingConfig;
use crate::types::{LegalChunk, LegalDocument, SourceType};

/// Estima tokens de um texto (aprox 1 token = 4 chars).
pub fn estimate_tokens(text: &str) -> usize {
    text.len() / 4
}

/// Gera ID deterministico para chunk.
fn chunk_id(doc_id: &str, chunk_index: usize) -> String {
    let input = format!("{doc_id}-{chunk_index}");
    format!("{:x}", md5::compute(input.as_bytes()))
}

/// Divide documento em chunks conforme tipo de fonte e config.
pub fn chunk_document(
    doc: &LegalDocument,
    source_type: &SourceType,
    config: &ChunkingConfig,
) -> Vec<LegalChunk> {
    match source_type {
        SourceType::Constituicao => chunk_article(doc, config),
        SourceType::AcordaoTcu | SourceType::DecretoTesemo => {
            chunk_paragraphs(doc, config)
        }
    }
}

/// Constituicao: cada artigo = 1 chunk (texto ja e atomico).
fn chunk_article(doc: &LegalDocument, config: &ChunkingConfig) -> Vec<LegalChunk> {
    let tokens = estimate_tokens(&doc.texto);
    if tokens < config.min_chunk_tokens {
        return Vec::new();
    }

    vec![LegalChunk {
        id: chunk_id(&doc.id, 0),
        doc_id: doc.id.clone(),
        chunk_index: 0,
        content: doc.texto.clone(),
        token_count: tokens as i32,
    }]
}

/// Paragrafo-based chunking com overlap para textos longos.
fn chunk_paragraphs(doc: &LegalDocument, config: &ChunkingConfig) -> Vec<LegalChunk> {
    let paragraphs: Vec<&str> = doc.texto.split('\n').collect();
    let mut chunks = Vec::new();
    let mut current = String::new();
    let mut current_tokens = 0usize;
    let mut chunk_index = 0usize;
    let mut prev_overlap;

    for para in &paragraphs {
        let para = para.trim();
        if para.is_empty() {
            continue;
        }
        let para_tokens = estimate_tokens(para);

        // Se adicionar este paragrafo excede max_tokens, finalizar chunk atual
        if current_tokens > 0 && current_tokens + para_tokens > config.max_tokens {
            let tokens = estimate_tokens(&current);
            if tokens >= config.min_chunk_tokens {
                chunks.push(LegalChunk {
                    id: chunk_id(&doc.id, chunk_index),
                    doc_id: doc.id.clone(),
                    chunk_index: chunk_index as i32,
                    content: current.clone(),
                    token_count: tokens as i32,
                });
                chunk_index += 1;
            }

            // Calcular overlap: pegar final do chunk atual
            let overlap_chars = config.overlap_tokens * 4;
            if overlap_chars > 0 && current.len() > overlap_chars {
                let start = current.len() - overlap_chars;
                let safe_start = current.ceil_char_boundary(start);
                prev_overlap = current[safe_start..].to_string();
            } else {
                prev_overlap = String::new();
            }

            current = prev_overlap.clone();
            current_tokens = estimate_tokens(&current);
        }

        if !current.is_empty() {
            current.push('\n');
        }
        current.push_str(para);
        current_tokens += para_tokens;
    }

    // Ultimo chunk
    if !current.is_empty() {
        let tokens = estimate_tokens(&current);
        if tokens >= config.min_chunk_tokens {
            chunks.push(LegalChunk {
                id: chunk_id(&doc.id, chunk_index),
                doc_id: doc.id.clone(),
                chunk_index: chunk_index as i32,
                content: current,
                token_count: tokens as i32,
            });
        }
    }

    chunks
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn make_doc(id: &str, texto: &str) -> LegalDocument {
        LegalDocument {
            id: id.into(),
            tipo: "test".into(),
            titulo: "Test".into(),
            texto: texto.into(),
            fonte: "test".into(),
            url: None,
            data_publicacao: None,
            metadata: json!({}),
        }
    }

    fn default_config() -> ChunkingConfig {
        ChunkingConfig {
            max_tokens: 128,
            overlap_tokens: 16,
            min_chunk_tokens: 10,
        }
    }

    #[test]
    fn test_estimate_tokens() {
        assert_eq!(estimate_tokens("1234567890123456"), 4); // 16 chars / 4
        assert_eq!(estimate_tokens(""), 0);
    }

    #[test]
    fn test_article_chunking_single() {
        let doc = make_doc("art5", &"a".repeat(200)); // 50 tokens
        let config = default_config();
        let chunks = chunk_document(&doc, &SourceType::Constituicao, &config);
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].chunk_index, 0);
        assert_eq!(chunks[0].doc_id, "art5");
    }

    #[test]
    fn test_article_too_small() {
        let doc = make_doc("art-tiny", "abc"); // < min_chunk_tokens
        let config = default_config();
        let chunks = chunk_document(&doc, &SourceType::Constituicao, &config);
        assert!(chunks.is_empty());
    }

    #[test]
    fn test_paragraph_chunking_multiple() {
        // 5 paragrafos de ~80 tokens cada = ~400 tokens, max_tokens=128
        let paragraphs: Vec<String> = (0..5)
            .map(|i| format!("Paragrafo {} {}", i, "x".repeat(300)))
            .collect();
        let texto = paragraphs.join("\n");
        let doc = make_doc("tcu1", &texto);
        let config = default_config();
        let chunks = chunk_document(&doc, &SourceType::AcordaoTcu, &config);
        assert!(chunks.len() > 1, "esperava multiplos chunks, got {}", chunks.len());
    }

    #[test]
    fn test_deterministic_ids() {
        let doc = make_doc("det", &"a".repeat(200));
        let config = default_config();
        let c1 = chunk_document(&doc, &SourceType::Constituicao, &config);
        let c2 = chunk_document(&doc, &SourceType::Constituicao, &config);
        assert_eq!(c1[0].id, c2[0].id);
    }

    #[test]
    fn test_chunk_id_format() {
        let id = chunk_id("doc1", 0);
        assert_eq!(id.len(), 32); // md5 hex
    }

    #[test]
    fn test_decreto_uses_paragraph_strategy() {
        let texto = (0..3)
            .map(|i| format!("Decreto item {} {}", i, "y".repeat(300)))
            .collect::<Vec<_>>()
            .join("\n");
        let doc = make_doc("dec1", &texto);
        let config = default_config();
        let chunks = chunk_document(&doc, &SourceType::DecretoTesemo, &config);
        assert!(!chunks.is_empty());
    }
}

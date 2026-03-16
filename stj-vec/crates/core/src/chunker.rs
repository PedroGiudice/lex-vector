use crate::config::ChunkingConfig;

/// Output do chunker: lista de chunks + doc_id
pub struct ChunkOutput {
    pub chunks: Vec<RawChunk>,
    pub doc_id: String,
}

/// Chunk bruto antes de persistir
pub struct RawChunk {
    pub id: String,
    pub content: String,
    pub chunk_index: usize,
    pub token_count: usize,
}

/// Remove tags HTML comuns em textos juridicos do STJ.
pub fn strip_html(text: &str) -> String {
    let mut result = text.to_string();

    // Tags conhecidas que viram newline
    result = result.replace("<br>", "\n");
    result = result.replace("<br/>", "\n");
    result = result.replace("<br />", "\n");
    result = result.replace("<BR>", "\n");
    result = result.replace("<p>", "\n");
    result = result.replace("<P>", "\n");
    result = result.replace("</p>", "\n");
    result = result.replace("</P>", "\n");

    // Remover qualquer tag HTML restante <...> ANTES de resolver entidades
    let mut no_tags = String::with_capacity(result.len());
    let mut in_tag = false;
    for ch in result.chars() {
        match ch {
            '<' => in_tag = true,
            '>' if in_tag => in_tag = false,
            _ if !in_tag => no_tags.push(ch),
            _ => {}
        }
    }

    // Entidades HTML (depois de remover tags, para nao confundir &lt; com tag)
    no_tags = no_tags.replace("&nbsp;", " ");
    no_tags = no_tags.replace("&amp;", "&");
    no_tags = no_tags.replace("&lt;", "<");
    no_tags = no_tags.replace("&gt;", ">");
    no_tags = no_tags.replace("&quot;", "\"");
    no_tags = no_tags.replace("&#39;", "'");

    no_tags
}

/// Estimativa de tokens: chars / 4 (aproximacao para portugues)
pub fn estimate_tokens(text: &str) -> usize {
    text.len() / 4
}

/// Converte texto juridico em chunks com overlap.
///
/// 1. Strip HTML
/// 2. Divide em paragrafos
/// 3. Acumula paragrafos ate max_tokens
/// 4. Overlap: ultimos overlap_tokens chars do chunk anterior
/// 5. Descarta chunks menores que min_chunk_tokens
/// 6. ID deterministico: md5(doc_id-chunk_index)
pub fn chunk_legal_text(text: &str, doc_id: &str, config: &ChunkingConfig) -> ChunkOutput {
    let clean = strip_html(text);
    let paragraphs = split_paragraphs(&clean);

    // Quebrar paragrafos muito longos em sub-paragrafos por sentenca
    let mut split_paras = Vec::new();
    for para in &paragraphs {
        if estimate_tokens(para) > config.max_tokens {
            // Quebrar por sentenca (". ")
            let mut remaining = para.as_str();
            while !remaining.is_empty() {
                let max_bytes = config.max_tokens * 4;
                if remaining.len() <= max_bytes {
                    split_paras.push(remaining.to_string());
                    break;
                }
                // Garantir que o limite cai em char boundary
                let safe_max = remaining.floor_char_boundary(max_bytes.min(remaining.len()));
                let search_range = &remaining[..safe_max];
                let split_at = search_range.rfind(". ").map(|i| i + 2).unwrap_or(safe_max);
                // split_at vem de rfind (sempre char boundary) ou safe_max (ja ajustado)
                split_paras.push(remaining[..split_at].to_string());
                remaining = &remaining[split_at..];
            }
        } else {
            split_paras.push(para.clone());
        }
    }

    let mut chunks = Vec::new();
    let mut current_text = String::new();
    let mut chunk_index = 0;

    for para in &split_paras {
        let para_tokens = estimate_tokens(para);
        let current_tokens = estimate_tokens(&current_text);

        // Se adicionar este paragrafo excede max_tokens, finalizar chunk atual
        if current_tokens > 0 && current_tokens + para_tokens > config.max_tokens {
            if estimate_tokens(&current_text) >= config.min_chunk_tokens {
                let id = format!("{:x}", md5::compute(format!("{}-{}", doc_id, chunk_index)));
                let token_count = estimate_tokens(&current_text);
                chunks.push(RawChunk {
                    id,
                    content: current_text.trim().to_string(),
                    chunk_index,
                    token_count,
                });
                chunk_index += 1;
            }

            // Overlap: pegar o final do chunk anterior
            let overlap_bytes = config.overlap_tokens * 4;
            if current_text.len() > overlap_bytes {
                let start = current_text.len() - overlap_bytes;
                // Avançar até encontrar char boundary válido
                let start = current_text.ceil_char_boundary(start);
                current_text = current_text[start..].to_string();
            }
            // Nao limpar current_text se for menor que overlap
        }

        if !current_text.is_empty() && !current_text.ends_with('\n') {
            current_text.push('\n');
        }
        current_text.push_str(para);
    }

    // Ultimo chunk
    if estimate_tokens(&current_text) >= config.min_chunk_tokens {
        let id = format!("{:x}", md5::compute(format!("{}-{}", doc_id, chunk_index)));
        let token_count = estimate_tokens(&current_text);
        chunks.push(RawChunk {
            id,
            content: current_text.trim().to_string(),
            chunk_index,
            token_count,
        });
    }

    ChunkOutput {
        chunks,
        doc_id: doc_id.to_string(),
    }
}

/// Divide texto em paragrafos, preservando linhas nao-vazias
fn split_paragraphs(text: &str) -> Vec<String> {
    text.split('\n')
        .map(|line| line.trim().to_string())
        .filter(|line| !line.is_empty())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_config() -> ChunkingConfig {
        ChunkingConfig {
            max_tokens: 512,
            overlap_tokens: 64,
            min_chunk_tokens: 10,
        }
    }

    #[test]
    fn test_strip_html_br() {
        assert_eq!(strip_html("A<br>B"), "A\nB");
        assert_eq!(strip_html("A<br/>B"), "A\nB");
        assert_eq!(strip_html("A<BR>B"), "A\nB");
    }

    #[test]
    fn test_strip_html_entities() {
        assert_eq!(strip_html("A&nbsp;B"), "A B");
        assert_eq!(strip_html("A&amp;B"), "A&B");
        assert_eq!(strip_html("&lt;tag&gt;"), "<tag>");
    }

    #[test]
    fn test_strip_html_tags() {
        assert_eq!(strip_html("<span>text</span>"), "text");
        assert_eq!(strip_html("<div class='x'>content</div>"), "content");
    }

    #[test]
    fn test_short_text_single_chunk() {
        let result = chunk_legal_text(
            "Texto curto de teste com conteudo suficiente para passar o filtro minimo de tokens.",
            "doc1",
            &default_config(),
        );
        assert_eq!(result.chunks.len(), 1);
        assert_eq!(result.doc_id, "doc1");
        assert_eq!(result.chunks[0].chunk_index, 0);
    }

    #[test]
    fn test_long_text_multiple_chunks() {
        let config = ChunkingConfig {
            max_tokens: 20,
            overlap_tokens: 5,
            min_chunk_tokens: 5,
        };
        let text = "A responsabilidade civil extracontratual. ".repeat(50);
        let result = chunk_legal_text(&text, "doc2", &config);
        assert!(result.chunks.len() > 1, "should produce multiple chunks");
        for (i, c) in result.chunks.iter().enumerate() {
            assert_eq!(c.chunk_index, i);
        }
    }

    #[test]
    fn test_real_stj_html() {
        let text = "DECISÃO<br>Trata-se de agravo.<br>É o relatório.<br>DECIDO.";
        let result = chunk_legal_text(text, "12345", &default_config());
        assert!(!result.chunks[0].content.contains("<br>"));
        assert!(result.chunks[0].content.contains("DECISÃO"));
    }

    #[test]
    fn test_deterministic_ids() {
        let text = "Conteudo juridico suficiente para gerar pelo menos um chunk valido neste teste de determinismo.";
        let r1 = chunk_legal_text(text, "doc1", &default_config());
        let r2 = chunk_legal_text(text, "doc1", &default_config());
        assert_eq!(r1.chunks[0].id, r2.chunks[0].id);
    }

    #[test]
    fn test_min_chunk_filter() {
        let config = ChunkingConfig {
            max_tokens: 512,
            overlap_tokens: 0,
            min_chunk_tokens: 100,
        };
        let result = chunk_legal_text("Curto.", "doc1", &config);
        assert_eq!(result.chunks.len(), 0, "should discard tiny chunk");
    }
}

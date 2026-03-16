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

/// Headers de secao em acordaos/decisoes do STJ.
/// Quando encontrado, forca quebra de chunk para nao misturar secoes.
const SECTION_HEADERS: &[&str] = &[
    "EMENTA",
    "ACÓRDÃO",
    "ACORDÃO",
    "RELATÓRIO",
    "RELATORIO",
    "VOTO",
    "DECISÃO",
    "DECISAO",
    "DECIDO",
];

/// Prefixos numerados usados no formato estruturado novo do STJ.
const NUMBERED_PREFIXES: &[&str] = &[
    "I. ",
    "II. ",
    "III. ",
    "IV. ",
    "V. ",
];

/// Verifica se uma linha e um header de secao juridica.
fn is_section_header(line: &str) -> bool {
    let trimmed = line.trim().trim_end_matches('.');
    if SECTION_HEADERS.iter().any(|h| trimmed.eq_ignore_ascii_case(h)) {
        return true;
    }
    // "É O RELATÓRIO" e variantes
    if trimmed.to_uppercase().starts_with("É O RELATÓRIO")
        || trimmed.to_uppercase().starts_with("E O RELATORIO")
    {
        return true;
    }
    // Formato numerado: "I. CASO EM EXAME", "II. QUESTÃO EM DISCUSSÃO", etc.
    let upper = trimmed.to_uppercase();
    NUMBERED_PREFIXES
        .iter()
        .any(|prefix| upper.starts_with(prefix) && trimmed.len() < 60)
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
        let section_break = is_section_header(para);

        // Finalizar chunk atual se: excede max_tokens OU encontrou header de secao
        let should_flush =
            (current_tokens > 0 && current_tokens + para_tokens > config.max_tokens)
                || (section_break && current_tokens > 0);

        if should_flush {
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

            if section_break {
                // Sem overlap entre secoes -- corte limpo
                current_text = String::new();
            } else {
                // Overlap: pegar o final do chunk anterior
                let overlap_bytes = config.overlap_tokens * 4;
                if current_text.len() > overlap_bytes {
                    let start = current_text.len() - overlap_bytes;
                    let start = current_text.ceil_char_boundary(start);
                    current_text = current_text[start..].to_string();
                }
            }
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
        let text = "DECISÃO<br>Trata-se de agravo interposto contra decisao que inadmitiu recurso especial fundamentado no art. 105 da CF.<br>É o relatório.<br>DECIDO.";
        let result = chunk_legal_text(text, "12345", &default_config());
        assert!(!result.chunks.is_empty(), "should produce at least 1 chunk");
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

    #[test]
    fn test_is_section_header() {
        assert!(is_section_header("EMENTA"));
        assert!(is_section_header("VOTO"));
        assert!(is_section_header("DECISÃO"));
        assert!(is_section_header("DECIDO."));
        assert!(is_section_header("RELATÓRIO"));
        assert!(is_section_header("ACÓRDÃO"));
        assert!(is_section_header("I. CASO EM EXAME"));
        assert!(is_section_header("II. QUESTÃO EM DISCUSSÃO"));
        assert!(is_section_header("III. RAZÕES DE DECIDIR"));
        assert!(is_section_header("IV. DISPOSITIVO E TESE"));
        assert!(is_section_header("É o relatório. Segue a fundamentação"));
        // Nao deve ser header
        assert!(!is_section_header("O relator votou pela procedencia do recurso."));
        assert!(!is_section_header("Este e um paragrafo normal de texto juridico com conteudo longo."));
    }

    #[test]
    fn test_section_aware_chunking_no_cross_section() {
        let config = ChunkingConfig {
            max_tokens: 512,
            overlap_tokens: 64,
            min_chunk_tokens: 10,
        };
        // Simula texto com EMENTA seguida de VOTO -- devem estar em chunks separados
        let text = format!(
            "EMENTA\n{}\nVOTO\n{}",
            "Trata-se de recurso especial interposto contra acordao do tribunal de origem. ".repeat(3),
            "Acompanho o relator no entendimento de que o recurso merece provimento. ".repeat(3),
        );
        let result = chunk_legal_text(&text, "doc1", &config);
        assert!(result.chunks.len() >= 2, "should have at least 2 chunks, got {}", result.chunks.len());

        // Nenhum chunk deve conter EMENTA + VOTO juntos
        for chunk in &result.chunks {
            let has_ementa_content = chunk.content.contains("recurso especial");
            let has_voto_content = chunk.content.contains("Acompanho o relator");
            assert!(
                !(has_ementa_content && has_voto_content),
                "chunk should not mix EMENTA and VOTO content: {}",
                &chunk.content[..chunk.content.len().min(100)]
            );
        }
    }

    #[test]
    fn test_section_aware_real_stj_format() {
        let config = ChunkingConfig {
            max_tokens: 512,
            overlap_tokens: 64,
            min_chunk_tokens: 10,
        };
        let text = [
            "DECISÃO",
            "Trata-se de agravo interposto contra decisao que inadmitiu recurso especial.",
            "O recorrente sustenta violacao ao art. 1.022 do CPC.",
            "I. CASO EM EXAME",
            "Agravo em recurso especial interposto contra acordao do tribunal de origem.",
            "II. QUESTÃO EM DISCUSSÃO",
            "Verificar se houve violacao ao art. 1.022 do CPC.",
            "III. RAZÕES DE DECIDIR",
            "O recurso nao merece prosperar pois o acordao recorrido analisou todas as questoes.",
            "IV. DISPOSITIVO E TESE",
            "Ante o exposto, nego provimento ao agravo.",
        ]
        .join("\n");

        let result = chunk_legal_text(&text, "doc1", &config);
        // Deve ter pelo menos 3 chunks (DECISAO, I+II, III+IV ou similar)
        assert!(result.chunks.len() >= 2, "expected >= 2 chunks, got {}", result.chunks.len());

        // DECISAO e RAZOES DE DECIDIR nao devem estar no mesmo chunk
        for chunk in &result.chunks {
            let has_decisao = chunk.content.starts_with("DECISÃO")
                || chunk.content.contains("\nDECISÃO");
            let has_razoes = chunk.content.contains("RAZÕES DE DECIDIR");
            assert!(
                !(has_decisao && has_razoes),
                "DECISAO and RAZOES should be in separate chunks"
            );
        }
    }

    #[test]
    fn test_section_break_no_overlap() {
        let config = ChunkingConfig {
            max_tokens: 100,
            overlap_tokens: 20,
            min_chunk_tokens: 10,
        };
        let text = format!(
            "EMENTA\n{}\nVOTO\n{}",
            "Conteudo da ementa com palavras suficientes para testar. ".repeat(2),
            "Conteudo do voto com texto diferente para validar. ".repeat(2),
        );
        let result = chunk_legal_text(&text, "doc1", &config);
        assert!(result.chunks.len() >= 2);

        // O chunk do VOTO nao deve conter texto da EMENTA (sem overlap entre secoes)
        let voto_chunk = result.chunks.iter().find(|c| c.content.contains("VOTO")).unwrap();
        assert!(
            !voto_chunk.content.contains("ementa"),
            "VOTO chunk should not contain EMENTA text (no cross-section overlap)"
        );
    }
}

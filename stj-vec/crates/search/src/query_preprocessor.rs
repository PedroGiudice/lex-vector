use std::collections::HashMap;
use std::path::Path;

use regex::Regex;
use serde::{Deserialize, Serialize};

use crate::config::PreprocessingConfig;

/// Query preprocessada com filtros extraidos e termos expandidos.
#[derive(Debug, Clone, Serialize)]
pub struct PreprocessedQuery {
    /// Query residual para embedding (sem metadados extraidos).
    pub semantic_query: String,
    /// Filtros extraidos automaticamente da query.
    pub extracted_filters: ExtractedFilters,
    /// Debug: cada extracao individual.
    pub extractions: Vec<Extraction>,
    /// Termos adicionados por expansao de dicionario.
    pub expanded_terms: Vec<String>,
}

/// Filtros extraidos por regex da query do usuario.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ExtractedFilters {
    /// Classe processual (REsp, HC, etc).
    pub classe: Option<String>,
    /// Nome do ministro normalizado.
    pub ministro: Option<String>,
    /// Data inicial do filtro de ano.
    pub ano_from: Option<String>,
    /// Data final do filtro de ano.
    pub ano_to: Option<String>,
    /// Numero completo do processo (classe + numero).
    pub processo: Option<String>,
}

impl ExtractedFilters {
    pub fn is_empty(&self) -> bool {
        self.classe.is_none()
            && self.ministro.is_none()
            && self.ano_from.is_none()
            && self.ano_to.is_none()
            && self.processo.is_none()
    }
}

/// Registro de uma extracao individual (para debug/log).
#[derive(Debug, Clone, Serialize)]
pub struct Extraction {
    pub field: String,
    pub matched: String,
    pub value: String,
}

/// Dicionario de expansao juridica carregado de JSON.
#[derive(Debug, Clone, Deserialize)]
pub struct ExpansionDictionary {
    #[allow(dead_code)]
    pub version: u32,
    pub expansions: HashMap<String, Vec<String>>,
}

impl ExpansionDictionary {
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("falha ao ler dicionario de expansao {}: {e}", path.display()))?;
        let dict: Self = serde_json::from_str(&content)
            .map_err(|e| anyhow::anyhow!("JSON invalido no dicionario de expansao: {e}"))?;
        Ok(dict)
    }
}

/// Siglas de classes processuais do STJ.
const CLASSES: &[&str] = &[
    "REsp", "AREsp", "HC", "RHC", "MS", "RMS", "Rcl", "CC", "AgInt",
    "EDcl", "EAREsp", "EREsp", "APn", "AR", "Pet", "RO", "Inq", "MC", "PUIL",
    "AgRg",
];

/// Stopwords juridicas que nao agregam valor semantico ao embedding.
const STOPWORDS: &[&str] = &[
    "jurisprudencia", "jurisprudência",
    "entendimento", "posicionamento",
    "acordao", "acórdão",
    "decisao", "decisão",
    "julgado", "julgados",
    "precedente", "precedentes",
    "tribunal", "corte",
];

/// Executa o pipeline completo de preprocessing na query.
///
/// Ordem: processo completo -> classe isolada -> ano -> ministro -> stopwords -> expansao.
pub fn preprocess(
    query: &str,
    config: &PreprocessingConfig,
    ministros: &[String],
) -> PreprocessedQuery {
    let mut text = normalize_whitespace(query);
    let mut extractions = Vec::new();
    let mut filters = ExtractedFilters::default();

    if config.extract_metadata {
        // 1. Numero de processo completo (classe + numero)
        extract_processo(&mut text, &mut filters, &mut extractions);

        // 2. Classe processual isolada (sem numero)
        if filters.processo.is_none() {
            extract_classe(&mut text, &mut filters, &mut extractions);
        }

        // 3. Ano
        extract_ano(&mut text, &mut filters, &mut extractions);

        // 4. Ministro
        extract_ministro(&mut text, &mut filters, &mut extractions, ministros);
    }

    // Normalizar espacos apos extracoes
    text = normalize_whitespace(&text);

    // 5. Stopwords
    if config.remove_stopwords {
        text = remove_stopwords(&text);
    }

    // 6. Expansao
    let mut expanded_terms = Vec::new();
    if config.expand_query {
        if let Some(ref dict) = config.expansion_dict {
            expanded_terms = expand_query(&text, dict, config.max_expansion_tokens);
        }
    }

    // Montar semantic_query com expansoes
    let semantic_query = if expanded_terms.is_empty() {
        text.clone()
    } else {
        let mut full = text.clone();
        for term in &expanded_terms {
            full.push(' ');
            full.push_str(term);
        }
        // Truncar se exceder limite de tokens
        truncate_by_tokens(&full, config.max_expansion_tokens)
    };

    PreprocessedQuery {
        semantic_query,
        extracted_filters: filters,
        extractions,
        expanded_terms,
    }
}

/// Extrai numero de processo completo (classe + numero).
fn extract_processo(
    text: &mut String,
    filters: &mut ExtractedFilters,
    extractions: &mut Vec<Extraction>,
) {
    let classes_pattern = CLASSES.join("|");
    let pattern = format!(r"(?i)\b({classes_pattern})\s+(\d{{4,}})\b");
    let re = Regex::new(&pattern).expect("regex de processo invalido");

    if let Some(caps) = re.captures(text) {
        let full_match = caps.get(0).expect("match grupo 0");
        let classe = caps.get(1).expect("match grupo 1").as_str();
        let numero = caps.get(2).expect("match grupo 2").as_str();

        let processo_str = format!("{classe} {numero}");
        filters.processo = Some(processo_str.clone());
        filters.classe = Some(normalize_classe(classe));

        extractions.push(Extraction {
            field: "processo".to_string(),
            matched: full_match.as_str().to_string(),
            value: processo_str,
        });

        // Remover da query
        *text = re.replace(text.as_str(), " ").to_string();
    }
}

/// Extrai classe processual isolada (sem numero).
fn extract_classe(
    text: &mut String,
    filters: &mut ExtractedFilters,
    extractions: &mut Vec<Extraction>,
) {
    let classes_pattern = CLASSES.join("|");
    let pattern = format!(r"(?i)\b({classes_pattern})\b");
    let re = Regex::new(&pattern).expect("regex de classe invalido");

    if let Some(caps) = re.captures(text) {
        let full_match = caps.get(0).expect("match grupo 0");
        let classe = full_match.as_str();
        let normalized = normalize_classe(classe);

        filters.classe = Some(normalized.clone());

        extractions.push(Extraction {
            field: "classe".to_string(),
            matched: classe.to_string(),
            value: normalized,
        });

        *text = re.replace(text.as_str(), " ").to_string();
    }
}

/// Extrai ano (2010-2029) e converte em range de datas.
fn extract_ano(
    text: &mut String,
    filters: &mut ExtractedFilters,
    extractions: &mut Vec<Extraction>,
) {
    let re = Regex::new(r"\b(20[12]\d)\b").expect("regex de ano invalido");

    if let Some(caps) = re.captures(text) {
        let full_match = caps.get(0).expect("match grupo 0");
        let ano = full_match.as_str();

        filters.ano_from = Some(format!("{ano}-01-01"));
        filters.ano_to = Some(format!("{ano}-12-31"));

        extractions.push(Extraction {
            field: "ano".to_string(),
            matched: ano.to_string(),
            value: ano.to_string(),
        });

        *text = re.replace(text.as_str(), " ").to_string();
    }
}

/// Extrai nome de ministro comparando tokens da query contra a lista conhecida.
fn extract_ministro(
    text: &mut String,
    filters: &mut ExtractedFilters,
    extractions: &mut Vec<Extraction>,
    ministros: &[String],
) {
    if ministros.is_empty() {
        return;
    }

    let text_upper = remove_accents(&text.to_uppercase());
    let text_tokens: Vec<&str> = text_upper.split_whitespace().collect();

    // Tentar match por sobrenome (cada token da query contra ultimo nome de cada ministro)
    let mut matches: Vec<(String, String)> = Vec::new(); // (nome_completo, token_matchado)

    for token in &text_tokens {
        let token_normalized = token.to_string();
        let mut token_matches = Vec::new();

        for ministro in ministros {
            let ministro_normalized = remove_accents(&ministro.to_uppercase());
            let parts: Vec<&str> = ministro_normalized.split_whitespace().collect();

            // Match exato no sobrenome (ultimo nome)
            if let Some(sobrenome) = parts.last() {
                if *sobrenome == token_normalized {
                    token_matches.push(ministro.clone());
                }
            }
        }

        // So aceitar se o match for unico (nao ambiguo)
        if token_matches.len() == 1 {
            matches.push((token_matches[0].clone(), token.to_string()));
        }
    }

    // Tambem tentar match por nome completo (multiplos tokens consecutivos)
    for ministro in ministros {
        let ministro_normalized = remove_accents(&ministro.to_uppercase());
        if text_upper.contains(&ministro_normalized) {
            // Match exato por nome completo tem prioridade
            filters.ministro = Some(ministro.clone());

            extractions.push(Extraction {
                field: "ministro".to_string(),
                matched: ministro.clone(),
                value: ministro.clone(),
            });

            // Remover da query (case-insensitive)
            let re = Regex::new(&format!(r"(?i){}", regex::escape(ministro)))
                .expect("regex de ministro invalido");
            *text = re.replace(text.as_str(), " ").to_string();
            return;
        }
    }

    // Fallback: match por sobrenome unico
    if matches.len() == 1 {
        let (nome_completo, token_matchado) = &matches[0];
        filters.ministro = Some(nome_completo.clone());

        extractions.push(Extraction {
            field: "ministro".to_string(),
            matched: token_matchado.clone(),
            value: nome_completo.clone(),
        });

        // Remover token da query
        let re = Regex::new(&format!(r"(?i)\b{}\b", regex::escape(token_matchado)))
            .expect("regex de token de ministro invalido");
        *text = re.replace(text.as_str(), " ").to_string();
    }
}

/// Remove stopwords juridicas da query, protegendo contra query vazia.
fn remove_stopwords(text: &str) -> String {
    let mut result = text.to_string();

    for &word in STOPWORDS {
        let pattern = format!(r"(?i)\b{}\b", regex::escape(word));
        let re = Regex::new(&pattern).expect("regex de stopword invalido");
        let candidate = re.replace_all(&result, " ").to_string();
        let candidate = normalize_whitespace(&candidate);

        // Protecao: nao remover se ficaria vazio
        if !candidate.is_empty() {
            result = candidate;
        } else {
            return result;
        }
    }

    result
}

/// Expande termos da query usando o dicionario. Retorna lista de termos expandidos.
fn expand_query(
    text: &str,
    dict: &ExpansionDictionary,
    max_tokens: usize,
) -> Vec<String> {
    let text_lower = text.to_lowercase();
    let mut expanded = Vec::new();
    let base_token_count = text.split_whitespace().count();
    let mut added_tokens = 0;

    // Ordenar chaves por tamanho decrescente para match de multi-word primeiro
    let mut keys: Vec<&String> = dict.expansions.keys().collect();
    keys.sort_by(|a, b| b.len().cmp(&a.len()));

    for key in keys {
        let key_lower = key.to_lowercase();

        // Verificar se o termo aparece na query (word boundary)
        let pattern = format!(r"(?i)\b{}\b", regex::escape(&key_lower));
        let re = match Regex::new(&pattern) {
            Ok(r) => r,
            Err(_) => continue,
        };

        if !re.is_match(&text_lower) {
            continue;
        }

        if let Some(expansions) = dict.expansions.get(key) {
            // Limitar a 2 expansoes por termo
            for expansion in expansions.iter().take(2) {
                let expansion_tokens = expansion.split_whitespace().count();
                if base_token_count + added_tokens + expansion_tokens <= max_tokens {
                    expanded.push(expansion.clone());
                    added_tokens += expansion_tokens;
                } else {
                    return expanded;
                }
            }
        }
    }

    expanded
}

/// Normaliza classe processual para formato canonico.
fn normalize_classe(classe: &str) -> String {
    let upper = classe.to_uppercase();
    // Mapear variantes comuns
    match upper.as_str() {
        "RESP" => "REsp".to_string(),
        "ARESP" => "AREsp".to_string(),
        "EARESP" => "EAREsp".to_string(),
        "ERESP" => "EREsp".to_string(),
        "AGINT" => "AgInt".to_string(),
        "EDCL" => "EDcl".to_string(),
        "AGRG" => "AgRg".to_string(),
        _ => upper,
    }
}

/// Remove acentos de uma string (simplificado para comparacao).
fn remove_accents(s: &str) -> String {
    s.chars()
        .map(|c| match c {
            '\u{00E1}' | '\u{00E0}' | '\u{00E2}' | '\u{00E3}' => 'A', // a com acentos -> A
            '\u{00C1}' | '\u{00C0}' | '\u{00C2}' | '\u{00C3}' => 'A', // A com acentos
            '\u{00E9}' | '\u{00E8}' | '\u{00EA}' => 'E',               // e com acentos -> E
            '\u{00C9}' | '\u{00C8}' | '\u{00CA}' => 'E',               // E com acentos
            '\u{00ED}' | '\u{00EC}' | '\u{00EE}' => 'I',               // i com acentos -> I
            '\u{00CD}' | '\u{00CC}' | '\u{00CE}' => 'I',               // I com acentos
            '\u{00F3}' | '\u{00F2}' | '\u{00F4}' | '\u{00F5}' => 'O', // o com acentos -> O
            '\u{00D3}' | '\u{00D2}' | '\u{00D4}' | '\u{00D5}' => 'O', // O com acentos
            '\u{00FA}' | '\u{00F9}' | '\u{00FB}' => 'U',               // u com acentos -> U
            '\u{00DA}' | '\u{00D9}' | '\u{00DB}' => 'U',               // U com acentos
            '\u{00E7}' => 'C',                                          // c cedilha
            '\u{00C7}' => 'C',                                          // C cedilha
            other => other,
        })
        .collect()
}

/// Normaliza espacos multiplos e trim.
fn normalize_whitespace(s: &str) -> String {
    s.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Trunca string por contagem de tokens (whitespace-split).
fn truncate_by_tokens(s: &str, max_tokens: usize) -> String {
    let tokens: Vec<&str> = s.split_whitespace().collect();
    if tokens.len() <= max_tokens {
        s.to_string()
    } else {
        tokens[..max_tokens].join(" ")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_config() -> PreprocessingConfig {
        PreprocessingConfig {
            enabled: true,
            extract_metadata: true,
            remove_stopwords: true,
            expand_query: false,
            expansions_file: None,
            max_expansion_tokens: 200,
            expansion_dict: None,
        }
    }

    fn config_with_dict() -> PreprocessingConfig {
        let mut expansions = HashMap::new();
        expansions.insert(
            "CDC".to_string(),
            vec![
                "Codigo de Defesa do Consumidor".to_string(),
                "Lei 8.078".to_string(),
            ],
        );
        expansions.insert(
            "CC".to_string(),
            vec!["Codigo Civil".to_string(), "Lei 10.406".to_string()],
        );
        expansions.insert(
            "dano moral".to_string(),
            vec![
                "responsabilidade civil".to_string(),
                "indenizacao por danos morais".to_string(),
            ],
        );

        let dict = ExpansionDictionary {
            version: 1,
            expansions,
        };

        PreprocessingConfig {
            enabled: true,
            extract_metadata: true,
            remove_stopwords: true,
            expand_query: true,
            expansions_file: None,
            max_expansion_tokens: 200,
            expansion_dict: Some(dict),
        }
    }

    fn sample_ministros() -> Vec<String> {
        vec![
            "NANCY ANDRIGHI".to_string(),
            "HERMAN BENJAMIN".to_string(),
            "LUIS FELIPE SALOMAO".to_string(),
            "ROGERIO SCHIETTI CRUZ".to_string(),
            "MARCO BUZZI".to_string(),
            "MARCO AURELIO BELLIZZE".to_string(),
        ]
    }

    #[test]
    fn test_extract_classe() {
        let config = default_config();
        let result = preprocess("REsp dano moral", &config, &[]);
        assert_eq!(result.extracted_filters.classe.as_deref(), Some("REsp"));
        assert_eq!(result.semantic_query, "dano moral");
    }

    #[test]
    fn test_extract_processo_completo() {
        let config = default_config();
        let result = preprocess("REsp 1234567 dano moral", &config, &[]);
        assert_eq!(
            result.extracted_filters.processo.as_deref(),
            Some("REsp 1234567")
        );
        assert_eq!(result.extracted_filters.classe.as_deref(), Some("REsp"));
        assert!(result.semantic_query.contains("dano moral"));
        assert!(!result.semantic_query.contains("1234567"));
    }

    #[test]
    fn test_extract_ano() {
        let config = default_config();
        let result = preprocess("dano moral 2023", &config, &[]);
        assert_eq!(
            result.extracted_filters.ano_from.as_deref(),
            Some("2023-01-01")
        );
        assert_eq!(
            result.extracted_filters.ano_to.as_deref(),
            Some("2023-12-31")
        );
        assert_eq!(result.semantic_query, "dano moral");
    }

    #[test]
    fn test_extract_combined() {
        let config = default_config();
        let ministros = sample_ministros();
        let result = preprocess("REsp Nancy Andrighi dano moral 2023", &config, &ministros);

        assert_eq!(result.extracted_filters.classe.as_deref(), Some("REsp"));
        assert_eq!(
            result.extracted_filters.ministro.as_deref(),
            Some("NANCY ANDRIGHI")
        );
        assert!(result.extracted_filters.ano_from.is_some());
        assert_eq!(result.semantic_query, "dano moral");
    }

    #[test]
    fn test_stopwords_removal() {
        let config = default_config();
        let result = preprocess("jurisprudencia sobre dano moral", &config, &[]);
        assert_eq!(result.semantic_query, "sobre dano moral");
    }

    #[test]
    fn test_stopwords_empty_protection() {
        let config = default_config();
        let result = preprocess("jurisprudencia acordao", &config, &[]);
        // Nao deve ficar vazio -- protecao ativada
        assert!(!result.semantic_query.is_empty());
    }

    #[test]
    fn test_expansion_cdc() {
        let config = config_with_dict();
        let result = preprocess("CDC dano moral", &config, &[]);
        assert!(result.expanded_terms.iter().any(|t| t.contains("Consumidor")));
    }

    #[test]
    fn test_cc_ambiguity_with_number() {
        let config = config_with_dict();
        let result = preprocess("CC 12345", &config, &[]);
        // CC + numero -> classe processual (Conflito de Competencia)
        assert_eq!(result.extracted_filters.classe.as_deref(), Some("CC"));
        assert!(result
            .extracted_filters
            .processo
            .as_deref()
            .is_some_and(|p| p.contains("12345")));
        // CC foi removido pela extracao de processo, nao deve expandir
        assert!(
            !result
                .expanded_terms
                .iter()
                .any(|t| t.contains("Codigo Civil"))
        );
    }

    #[test]
    fn test_cc_isolated_expands() {
        let config = config_with_dict();
        // CC isolado (sem numero) -> extraido como classe, mas tambem nao expande
        // porque extract_metadata remove "CC" da query antes da expansao
        let mut config_no_meta = config.clone();
        config_no_meta.extract_metadata = false;
        let result = preprocess("CC responsabilidade", &config_no_meta, &[]);
        // Sem extracao de metadados, CC fica na query e expande
        assert!(result
            .expanded_terms
            .iter()
            .any(|t| t.contains("Codigo Civil")));
    }

    #[test]
    fn test_ministro_by_sobrenome() {
        let config = default_config();
        let ministros = sample_ministros();
        let result = preprocess("dano moral Andrighi", &config, &ministros);
        assert_eq!(
            result.extracted_filters.ministro.as_deref(),
            Some("NANCY ANDRIGHI")
        );
    }

    #[test]
    fn test_ministro_ambiguous_marco() {
        let config = default_config();
        let ministros = sample_ministros();
        // "Marco" aparece em MARCO BUZZI e MARCO AURELIO BELLIZZE -> ambiguo
        let result = preprocess("dano moral Marco", &config, &ministros);
        // Nao deve extrair porque e ambiguo (2 matches para "Marco")
        assert!(result.extracted_filters.ministro.is_none());
    }

    #[test]
    fn test_no_extraction_when_disabled() {
        let config = PreprocessingConfig {
            enabled: true,
            extract_metadata: false,
            remove_stopwords: false,
            expand_query: false,
            expansions_file: None,
            max_expansion_tokens: 200,
            expansion_dict: None,
        };
        let result = preprocess("REsp dano moral 2023", &config, &[]);
        assert!(result.extracted_filters.is_empty());
        assert_eq!(result.semantic_query, "REsp dano moral 2023");
    }

    #[test]
    fn test_case_insensitive_classe() {
        let config = default_config();
        let result = preprocess("resp dano moral", &config, &[]);
        assert_eq!(result.extracted_filters.classe.as_deref(), Some("REsp"));
    }

    #[test]
    fn test_remove_accents() {
        // remove_accents so substitui caracteres acentuados, nao muda case
        assert_eq!(remove_accents("Salomao"), "Salomao"); // sem acentos, sem mudanca
        assert_eq!(remove_accents("Rogerio"), "Rogerio");
        assert_eq!(remove_accents("Salomão"), "SalomAo"); // ã -> A, o sem acento fica
        assert_eq!(remove_accents("Rogério"), "RogErio"); // é -> E
        // Usado junto com to_uppercase em extract_ministro
        assert_eq!(remove_accents(&"Salomão".to_uppercase()), "SALOMAO");
    }

    #[test]
    fn test_normalize_whitespace() {
        assert_eq!(normalize_whitespace("  foo   bar  "), "foo bar");
    }

    #[test]
    fn test_truncate_by_tokens() {
        let s = "a b c d e f g";
        assert_eq!(truncate_by_tokens(s, 3), "a b c");
        assert_eq!(truncate_by_tokens(s, 100), s);
    }

    #[test]
    fn test_hc_extraction() {
        let config = default_config();
        let result = preprocess("HC liberdade provisoria", &config, &[]);
        assert_eq!(result.extracted_filters.classe.as_deref(), Some("HC"));
        assert_eq!(result.semantic_query, "liberdade provisoria");
    }

    #[test]
    fn test_multiple_stopwords() {
        let config = default_config();
        let result = preprocess("jurisprudencia sobre precedente de dano moral", &config, &[]);
        assert!(!result.semantic_query.contains("jurisprudencia"));
        assert!(!result.semantic_query.contains("precedente"));
        assert!(result.semantic_query.contains("dano moral"));
    }

    #[test]
    fn test_expansion_limit() {
        let mut expansions = HashMap::new();
        // Criar expansao que excederia 200 tokens
        let big_expansion = (0..100).map(|i| format!("token{i}")).collect::<Vec<_>>().join(" ");
        expansions.insert("teste".to_string(), vec![big_expansion.clone(), big_expansion]);

        let dict = ExpansionDictionary {
            version: 1,
            expansions,
        };

        let config = PreprocessingConfig {
            enabled: true,
            extract_metadata: false,
            remove_stopwords: false,
            expand_query: true,
            expansions_file: None,
            max_expansion_tokens: 50,
            expansion_dict: Some(dict),
        };

        let result = preprocess("teste query", &config, &[]);
        // Deve respeitar o limite de tokens
        let total_tokens: usize = result.semantic_query.split_whitespace().count();
        assert!(total_tokens <= 50);
    }
}

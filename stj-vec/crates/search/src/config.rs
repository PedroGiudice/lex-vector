use std::path::Path;

use serde::Deserialize;

use crate::query_preprocessor::ExpansionDictionary;

#[derive(Debug, Deserialize, Clone)]
pub struct SearchConfig {
    pub server: ServerConfig,
    pub model: ModelConfig,
    pub qdrant: QdrantConfig,
    pub sqlite: SqliteConfig,
    pub search: SearchDefaults,
    #[serde(default)]
    pub preprocessing: PreprocessingConfig,
    pub reranker: Option<RerankerConfig>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ServerConfig {
    pub port: u16,
    pub static_dir: String,
    #[serde(default)]
    pub cors_origins: Vec<String>,
}

#[derive(Debug, Deserialize, Clone)]
pub struct ModelConfig {
    pub dir: String,
    #[serde(default = "default_threads")]
    pub threads: usize,
}

#[derive(Debug, Deserialize, Clone)]
pub struct QdrantConfig {
    pub url: String,
    pub collection: String,
    #[serde(default = "default_top_k")]
    pub dense_top_k: u64,
    #[serde(default = "default_top_k")]
    pub sparse_top_k: u64,
    #[serde(default = "default_rrf_k")]
    pub rrf_k: f64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct SqliteConfig {
    pub path: String,
    #[serde(default = "default_pool_size")]
    pub pool_size: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct SearchDefaults {
    #[serde(default = "default_max_results")]
    pub max_results: usize,
    #[serde(default = "default_limit")]
    pub default_limit: usize,
    #[serde(default = "default_overfetch")]
    pub overfetch_factor: usize,
    #[serde(default = "default_weight")]
    pub dense_weight: f64,
    #[serde(default = "default_weight")]
    pub sparse_weight: f64,
}

/// Configuracao do preprocessing de queries.
#[derive(Debug, Deserialize, Clone)]
pub struct PreprocessingConfig {
    #[serde(default = "default_true")]
    pub enabled: bool,
    #[serde(default = "default_true")]
    pub extract_metadata: bool,
    #[serde(default = "default_true")]
    pub remove_stopwords: bool,
    #[serde(default = "default_true")]
    pub expand_query: bool,
    #[serde(default)]
    pub expansions_file: Option<String>,
    #[serde(default = "default_max_expansion_tokens")]
    pub max_expansion_tokens: usize,
    /// Dicionario carregado em runtime (nao vem do TOML).
    #[serde(skip)]
    pub expansion_dict: Option<ExpansionDictionary>,
}

impl Default for PreprocessingConfig {
    fn default() -> Self {
        Self {
            enabled: true,
            extract_metadata: true,
            remove_stopwords: true,
            expand_query: true,
            expansions_file: None,
            max_expansion_tokens: 200,
            expansion_dict: None,
        }
    }
}

impl PreprocessingConfig {
    /// Carrega o dicionario de expansao do arquivo configurado.
    pub fn load_expansion_dict(&mut self, base_dir: &Path) -> anyhow::Result<()> {
        if !self.expand_query {
            return Ok(());
        }
        if let Some(ref file) = self.expansions_file {
            let path = base_dir.join(file);
            if path.exists() {
                let dict = ExpansionDictionary::load(&path)?;
                tracing::info!(
                    path = %path.display(),
                    terms = dict.expansions.len(),
                    "dicionario de expansao carregado"
                );
                self.expansion_dict = Some(dict);
            } else {
                tracing::warn!(
                    path = %path.display(),
                    "arquivo de expansao nao encontrado, expansao desabilitada"
                );
            }
        }
        Ok(())
    }
}

/// Configuracao do reranker ONNX (cross-encoder).
#[derive(Debug, Deserialize, Clone)]
pub struct RerankerConfig {
    #[serde(default)]
    pub enabled: bool,
    pub model_dir: Option<String>,
    #[serde(default = "default_reranker_threads")]
    pub threads: usize,
    #[serde(default = "default_rerank_top_k")]
    pub top_k: usize,
    #[serde(default = "default_rerank_return")]
    pub return_top: usize,
}

fn default_reranker_threads() -> usize {
    4
}
fn default_rerank_top_k() -> usize {
    20
}
fn default_rerank_return() -> usize {
    10
}

fn default_threads() -> usize {
    8
}
fn default_top_k() -> u64 {
    200
}
fn default_rrf_k() -> f64 {
    60.0
}
fn default_pool_size() -> u32 {
    4
}
fn default_max_results() -> usize {
    50
}
fn default_limit() -> usize {
    20
}
fn default_overfetch() -> usize {
    3
}
fn default_weight() -> f64 {
    1.0
}
fn default_true() -> bool {
    true
}
fn default_max_expansion_tokens() -> usize {
    200
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_parse() {
        let toml_str = r#"
[server]
port = 8421
static_dir = "frontend/dist"

[model]
dir = "models/bge-m3-onnx"

[qdrant]
url = "http://localhost:6334"
collection = "stj"

[sqlite]
path = "db/stj-vec.db"

[search]
"#;
        let config: SearchConfig = toml::from_str(toml_str).unwrap();
        assert_eq!(config.server.port, 8421);
        assert_eq!(config.model.threads, 8); // default
        assert_eq!(config.qdrant.dense_top_k, 200); // default
        assert_eq!(config.search.default_limit, 20); // default
        assert!((config.search.dense_weight - 1.0).abs() < f64::EPSILON); // default
        assert!((config.search.sparse_weight - 1.0).abs() < f64::EPSILON); // default
        assert!(config.preprocessing.enabled); // default
    }
}

use serde::Deserialize;

#[derive(Debug, Deserialize, Clone)]
pub struct SearchConfig {
    pub server: ServerConfig,
    pub model: ModelConfig,
    pub qdrant: QdrantConfig,
    pub sqlite: SqliteConfig,
    pub search: SearchDefaults,
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
    }
}

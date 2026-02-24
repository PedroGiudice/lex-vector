use serde::Deserialize;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct LegalConfig {
    pub data: DataConfig,
    pub chunking: ChunkingConfig,
    pub embedding: EmbeddingConfig,
}

#[derive(Debug, Deserialize)]
pub struct DataConfig {
    pub corpus_dir: String,
    pub db_path: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ChunkingConfig {
    pub max_tokens: usize,
    pub overlap_tokens: usize,
    pub min_chunk_tokens: usize,
}

#[derive(Debug, Deserialize)]
pub struct EmbeddingConfig {
    pub model: String,
    pub dim: usize,
    pub provider: String,
    pub ollama: OllamaConfig,
}

#[derive(Debug, Deserialize)]
pub struct OllamaConfig {
    pub url: String,
    pub model: String,
    pub timeout_secs: u64,
}

impl LegalConfig {
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("failed to read config {}: {}", path.display(), e))?;
        let config: Self = toml::from_str(&content)
            .map_err(|e| anyhow::anyhow!("failed to parse config: {}", e))?;
        Ok(config)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_config() {
        let toml_str = r#"
[data]
corpus_dir = "/tmp/corpus"
db_path = "db/test.db"

[chunking]
max_tokens = 512
overlap_tokens = 64
min_chunk_tokens = 50

[embedding]
model = "bge-m3"
dim = 1024
provider = "ollama"

[embedding.ollama]
url = "http://localhost:11434/api/embeddings"
model = "bge-m3"
timeout_secs = 10
"#;
        let config: LegalConfig = toml::from_str(toml_str).unwrap();
        assert_eq!(config.data.corpus_dir, "/tmp/corpus");
        assert_eq!(config.embedding.dim, 1024);
        assert_eq!(config.chunking.max_tokens, 512);
    }
}

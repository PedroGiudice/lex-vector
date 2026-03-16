use serde::Deserialize;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct AppConfig {
    pub data: DataConfig,
    pub chunking: ChunkingConfig,
    pub embedding: EmbeddingConfig,
    pub server: ServerConfig,
    /// Configuracao CKAN (opcional -- necessaria apenas para download/enrich)
    #[serde(default)]
    pub ckan: Option<CkanConfig>,
}

#[derive(Debug, Deserialize)]
pub struct DataConfig {
    pub integras_dir: String,
    pub metadata_dir: String,
    pub db_path: String,
    /// Diretorio dos JSONs de espelhos de acordaos (por orgao julgador)
    #[serde(default)]
    pub espelhos_dir: Option<String>,
    /// Diretorio para downloads brutos (ZIPs, manifests)
    #[serde(default)]
    pub downloads_dir: Option<String>,
}

/// Configuracao do portal CKAN do STJ (dados abertos)
#[derive(Debug, Clone, Deserialize)]
pub struct CkanConfig {
    /// URL base da API CKAN
    #[serde(default = "CkanConfig::default_base_url")]
    pub base_url: String,
    /// Dataset ID das integras
    #[serde(default = "CkanConfig::default_integras_dataset")]
    pub integras_dataset: String,
    /// Lista de dataset IDs dos espelhos (um por orgao julgador)
    #[serde(default = "CkanConfig::default_espelhos_datasets")]
    pub espelhos_datasets: Vec<String>,
    /// Timeout em segundos para downloads
    #[serde(default = "CkanConfig::default_timeout")]
    pub download_timeout_secs: u64,
    /// Maximo de downloads simultaneos
    #[serde(default = "CkanConfig::default_max_concurrent")]
    pub max_concurrent_downloads: usize,
}

impl CkanConfig {
    fn default_base_url() -> String {
        "https://dadosabertos.web.stj.jus.br".into()
    }

    fn default_integras_dataset() -> String {
        "integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica".into()
    }

    fn default_espelhos_datasets() -> Vec<String> {
        vec![
            "espelhos-de-acordaos-corte-especial".into(),
            "espelhos-de-acordaos-primeira-secao".into(),
            "espelhos-de-acordaos-segunda-secao".into(),
            "espelhos-de-acordaos-terceira-secao".into(),
            "espelhos-de-acordaos-primeira-turma".into(),
            "espelhos-de-acordaos-segunda-turma".into(),
            "espelhos-de-acordaos-terceira-turma".into(),
            "espelhos-de-acordaos-quarta-turma".into(),
            "espelhos-de-acordaos-quinta-turma".into(),
            "espelhos-de-acordaos-sexta-turma".into(),
        ]
    }

    fn default_timeout() -> u64 {
        300
    }

    fn default_max_concurrent() -> usize {
        2
    }
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
    pub modal: ModalConfig,
    pub ollama: OllamaConfig,
}

#[derive(Debug, Deserialize)]
pub struct ModalConfig {
    pub endpoint: String,
    pub batch_size: usize,
}

#[derive(Debug, Deserialize)]
pub struct OllamaConfig {
    pub url: String,
    pub model: String,
    pub timeout_secs: u64,
}

#[derive(Debug, Clone, Deserialize)]
pub struct ServerConfig {
    pub socket: String,
    pub port: u16,
    pub max_results: usize,
    pub default_threshold: f64,
}

impl AppConfig {
    /// Carrega config de um arquivo TOML
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("failed to read config {}: {}", path.display(), e))?;
        let config: Self = toml::from_str(&content)
            .map_err(|e| anyhow::anyhow!("failed to parse config: {}", e))?;
        Ok(config)
    }

    /// Retorna true se embedding esta configurado (dim > 0 e provider definido)
    pub fn embedding_enabled(&self) -> bool {
        self.embedding.dim > 0 && !self.embedding.provider.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_config() {
        let toml_str = r#"
[data]
integras_dir = "/tmp/integras"
metadata_dir = "/tmp/metadata"
db_path = "db/test.db"

[chunking]
max_tokens = 512
overlap_tokens = 64
min_chunk_tokens = 50

[embedding]
model = ""
dim = 0
provider = ""

[embedding.modal]
endpoint = ""
batch_size = 0

[embedding.ollama]
url = "http://localhost:11434/api/embeddings"
model = "bge-m3"
timeout_secs = 10

[server]
socket = "/tmp/stj-vec.sock"
port = 8421
max_results = 20
default_threshold = 0.3
"#;
        let config: AppConfig = toml::from_str(toml_str).unwrap();
        assert_eq!(config.data.integras_dir, "/tmp/integras");
        assert_eq!(config.chunking.max_tokens, 512);
        assert_eq!(config.embedding.dim, 0);
        assert!(!config.embedding_enabled());
        assert_eq!(config.server.port, 8421);
    }
}

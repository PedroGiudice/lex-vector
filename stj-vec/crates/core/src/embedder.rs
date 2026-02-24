use anyhow::Result;
use async_trait::async_trait;

/// Trait para providers de embedding.
///
/// Implementacoes concretas serao adicionadas quando Modal estiver configurado.
/// Por ora, apenas `NoopEmbedder` (placeholder) esta disponivel.
#[async_trait]
pub trait Embedder: Send + Sync {
    /// Gera embedding de um texto
    async fn embed(&self, text: &str) -> Result<Vec<f32>>;

    /// Gera embeddings em batch
    async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>>;

    /// Dimensao dos vetores gerados
    fn dim(&self) -> usize;

    /// Nome do modelo usado
    fn model_name(&self) -> &str;
}

/// Placeholder -- retorna erro informando que embedding nao esta configurado.
/// Usado quando config.embedding.dim == 0 ou provider vazio.
pub struct NoopEmbedder;

#[async_trait]
impl Embedder for NoopEmbedder {
    async fn embed(&self, _text: &str) -> Result<Vec<f32>> {
        anyhow::bail!("embedding not configured (dim=0, provider empty)")
    }

    async fn embed_batch(&self, _texts: &[String]) -> Result<Vec<Vec<f32>>> {
        anyhow::bail!("embedding not configured (dim=0, provider empty)")
    }

    fn dim(&self) -> usize {
        0
    }

    fn model_name(&self) -> &str {
        "noop"
    }
}

// PLACEHOLDER: ModalEmbedder sera implementado quando Modal estiver configurado.
// pub struct ModalEmbedder { config: ModalConfig, client: reqwest::Client }

// PLACEHOLDER: OllamaEmbedder como fallback (mesmo do cogmem).
// pub struct OllamaEmbedder { url: String, model: String, client: reqwest::Client }

#[derive(serde::Deserialize)]
struct OllamaResponse {
    embedding: Vec<f32>,
}

/// Embedder que usa Ollama local/remoto via HTTP API.
pub struct OllamaEmbedder {
    url: String,
    model: String,
    dim: usize,
    client: reqwest::Client,
}

impl OllamaEmbedder {
    /// Cria embedder com parametros explicitos.
    ///
    /// # Panics
    ///
    /// Panics se o cliente HTTP nao puder ser construido (TLS indisponivel).
    #[must_use]
    pub fn new(url: &str, model: &str, dim: usize, timeout_secs: u64) -> Self {
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(timeout_secs))
            .build()
            .expect("failed to build reqwest client — TLS backend unavailable");
        Self {
            url: url.to_owned(),
            model: model.to_owned(),
            dim,
            client,
        }
    }

    /// Cria embedder a partir de `OllamaConfig`.
    #[must_use]
    pub fn from_config(config: &crate::config::OllamaConfig, dim: usize) -> Self {
        Self::new(&config.url, &config.model, dim, config.timeout_secs)
    }
}

#[async_trait]
impl Embedder for OllamaEmbedder {
    async fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let body = serde_json::json!({
            "model": self.model,
            "prompt": text,
        });

        let resp = self
            .client
            .post(&self.url)
            .json(&body)
            .send()
            .await
            .map_err(|e| anyhow::anyhow!("ollama request failed: {e}"))?;

        let status = resp.status();
        if !status.is_success() {
            let text = resp.text().await.unwrap_or_default();
            anyhow::bail!("ollama returned {status}: {text}");
        }

        let parsed: OllamaResponse = resp
            .json()
            .await
            .map_err(|e| anyhow::anyhow!("ollama response parse failed: {e}"))?;

        if parsed.embedding.len() != self.dim {
            anyhow::bail!(
                "embedding dimension mismatch: expected {}, got {}",
                self.dim,
                parsed.embedding.len()
            );
        }

        Ok(parsed.embedding)
    }

    async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        let mut results = Vec::with_capacity(texts.len());
        for text in texts {
            results.push(self.embed(text).await?);
        }
        Ok(results)
    }

    fn dim(&self) -> usize {
        self.dim
    }

    fn model_name(&self) -> &str {
        &self.model
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_noop_embed_fails() {
        let embedder = NoopEmbedder;
        let result = embedder.embed("test").await;
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("not configured"));
    }

    #[tokio::test]
    async fn test_noop_batch_fails() {
        let embedder = NoopEmbedder;
        let result = embedder.embed_batch(&["test".into()]).await;
        assert!(result.is_err());
    }

    #[test]
    fn test_noop_dim_zero() {
        let embedder = NoopEmbedder;
        assert_eq!(embedder.dim(), 0);
        assert_eq!(embedder.model_name(), "noop");
    }
}

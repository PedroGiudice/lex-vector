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

/// Embedder que usa TEI (Text Embeddings Inference) via HTTP API.
///
/// Suporta sub-batching para respeitar `max_client_batch_size` do TEI.
pub struct TeiEmbedder {
    url: String,
    dim: usize,
    sub_batch_size: usize,
    client: reqwest::Client,
}

#[derive(serde::Serialize)]
struct TeiRequest {
    inputs: Vec<String>,
}

impl TeiEmbedder {
    /// Cria embedder TEI com parametros explicitos.
    ///
    /// # Panics
    ///
    /// Panics se o cliente HTTP nao puder ser construido (TLS indisponivel).
    #[must_use]
    pub fn new(url: &str, dim: usize, timeout_secs: u64, sub_batch_size: usize) -> Self {
        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(timeout_secs))
            .build()
            .expect("failed to build reqwest client — TLS backend unavailable");
        Self {
            url: url.to_owned(),
            dim,
            sub_batch_size,
            client,
        }
    }

    /// Cria embedder TEI com defaults: localhost:8080, 1024d, 120s timeout, batch 32.
    #[must_use]
    pub fn default_local() -> Self {
        let url = std::env::var("TEI_URL")
            .unwrap_or_else(|_| "http://127.0.0.1:8080/embed".to_string());
        let batch_size: usize = std::env::var("TEI_BATCH_SIZE")
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(4);
        Self::new(&url, 1024, 120, batch_size)
    }
}

#[async_trait]
impl Embedder for TeiEmbedder {
    async fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let req = TeiRequest {
            inputs: vec![text.to_string()],
        };

        let resp = self
            .client
            .post(&self.url)
            .json(&req)
            .send()
            .await
            .map_err(|e| anyhow::anyhow!("TEI request failed: {e}"))?;

        let status = resp.status();
        if !status.is_success() {
            let body = resp.text().await.unwrap_or_default();
            anyhow::bail!("TEI returned {status}: {body}");
        }

        let data: Vec<Vec<f32>> = resp
            .json()
            .await
            .map_err(|e| anyhow::anyhow!("TEI response parse failed: {e}"))?;

        let embedding = data
            .into_iter()
            .next()
            .ok_or_else(|| anyhow::anyhow!("TEI returned empty response"))?;

        if embedding.len() != self.dim {
            anyhow::bail!(
                "embedding dimension mismatch: expected {}, got {}",
                self.dim,
                embedding.len()
            );
        }

        Ok(embedding)
    }

    async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        if texts.is_empty() {
            return Ok(vec![]);
        }

        let mut all_results = Vec::with_capacity(texts.len());

        for sub_batch in texts.chunks(self.sub_batch_size) {
            let req = TeiRequest {
                inputs: sub_batch.to_vec(),
            };

            let resp = self
                .client
                .post(&self.url)
                .json(&req)
                .send()
                .await
                .map_err(|e| anyhow::anyhow!("TEI batch request failed: {e}"))?;

            let status = resp.status();
            if !status.is_success() {
                let body = resp.text().await.unwrap_or_default();
                anyhow::bail!("TEI returned {status}: {body}");
            }

            let data: Vec<Vec<f32>> = resp
                .json()
                .await
                .map_err(|e| anyhow::anyhow!("TEI batch response parse failed: {e}"))?;

            for (i, emb) in data.iter().enumerate() {
                if emb.len() != self.dim {
                    anyhow::bail!(
                        "embedding dimension mismatch at index {i}: expected {}, got {}",
                        self.dim,
                        emb.len()
                    );
                }
            }

            all_results.extend(data);
        }

        Ok(all_results)
    }

    fn dim(&self) -> usize {
        self.dim
    }

    fn model_name(&self) -> &str {
        "bge-m3"
    }
}

// --- Legacy OllamaEmbedder kept for backwards compatibility ---

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

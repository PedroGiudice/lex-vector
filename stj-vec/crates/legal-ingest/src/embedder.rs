//! Cliente de embeddings via Ollama API.

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::time::Duration;

#[derive(Serialize)]
struct EmbedRequest<'a> {
    model: &'a str,
    prompt: &'a str,
}

#[derive(Deserialize)]
struct EmbedResponse {
    embedding: Vec<f32>,
}

/// Cliente para gerar embeddings via Ollama.
pub struct OllamaEmbedder {
    client: reqwest::Client,
    url: String,
    model: String,
    dim: usize,
}

impl OllamaEmbedder {
    pub fn new(url: String, model: String, dim: usize, timeout_secs: u64) -> Self {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(timeout_secs))
            .build()
            .expect("failed to build reqwest client");
        Self {
            client,
            url,
            model,
            dim,
        }
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Gera embedding para um texto.
    pub async fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let req = EmbedRequest {
            model: &self.model,
            prompt: text,
        };

        let resp = self
            .client
            .post(&self.url)
            .json(&req)
            .send()
            .await
            .context("falha ao conectar com Ollama")?;

        let status = resp.status();
        if !status.is_success() {
            let body = resp.text().await.unwrap_or_default();
            anyhow::bail!("Ollama retornou {status}: {body}");
        }

        let data: EmbedResponse = resp
            .json()
            .await
            .context("falha ao deserializar resposta Ollama")?;

        Ok(data.embedding)
    }

    /// Gera embeddings em batch (sequencial, 1 por request).
    pub async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        let mut results = Vec::with_capacity(texts.len());
        for text in texts {
            results.push(self.embed(text).await?);
        }
        Ok(results)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embedder_creation() {
        let e = OllamaEmbedder::new(
            "http://localhost:11434/api/embeddings".into(),
            "bge-m3".into(),
            1024,
            10,
        );
        assert_eq!(e.dim(), 1024);
    }

    // Teste de integracao comentado - requer Ollama rodando
    // #[tokio::test]
    // async fn test_embed_real() {
    //     let e = OllamaEmbedder::new(
    //         "http://100.114.203.28:11434/api/embeddings".into(),
    //         "bge-m3".into(), 1024, 10,
    //     );
    //     let v = e.embed("teste").await.unwrap();
    //     assert_eq!(v.len(), 1024);
    // }
}

use anyhow::Result;
use async_trait::async_trait;

/// Trait para providers de embedding.
///
/// Implementacoes concretas serao adicionadas quando Modal estiver configurado.
/// Por ora, apenas NoopEmbedder (placeholder) esta disponivel.
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

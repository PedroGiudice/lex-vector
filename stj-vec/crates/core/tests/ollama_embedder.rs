use stj_vec_core::embedder::{Embedder, OllamaEmbedder};

const OLLAMA_URL: &str = "http://100.114.203.28:11434/api/embeddings";
const MODEL: &str = "bge-m3";
const DIM: usize = 1024;

#[test]
fn test_ollama_embedder_dim() {
    let embedder = OllamaEmbedder::new(OLLAMA_URL, MODEL, DIM, 30);
    assert_eq!(embedder.dim(), DIM);
    assert_eq!(embedder.model_name(), MODEL);
}

#[tokio::test]
#[ignore]
async fn test_ollama_embedder_embed() {
    let embedder = OllamaEmbedder::new(OLLAMA_URL, MODEL, DIM, 30);
    let result = embedder.embed("direito constitucional brasileiro").await;
    let vec = result.expect("embed deve retornar Ok");
    assert_eq!(vec.len(), DIM);
    assert!(vec.iter().any(|&v| v != 0.0), "embedding nao deve ser todo zero");
}

#[tokio::test]
#[ignore]
async fn test_ollama_embedder_batch() {
    let embedder = OllamaEmbedder::new(OLLAMA_URL, MODEL, DIM, 30);
    let texts = vec![
        "recurso especial provido".to_owned(),
        "agravo interno desprovido".to_owned(),
    ];
    let result = embedder.embed_batch(&texts).await;
    let vecs = result.expect("embed_batch deve retornar Ok");
    assert_eq!(vecs.len(), 2);
    assert_eq!(vecs[0].len(), DIM);
    assert_eq!(vecs[1].len(), DIM);
}

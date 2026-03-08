# stj-vec-search Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** MVP de busca hibrida (dense+sparse+RRF) sobre 13.5M chunks STJ, com frontend React e backend Rust, servindo via web standalone.

**Architecture:** Crate Rust `stj-vec-search` (axum) que embeda queries via ONNX Runtime (BGE-M3), busca no Qdrant via gRPC (duas queries paralelas + fusao RRF local), enriquece com metadados SQLite, e serve frontend React como static files.

**Tech Stack:** Rust (axum 0.8, ort 2, qdrant-client 1, rusqlite 0.33, r2d2), React 19, Vite 7, Tailwind 4, TanStack Query, Zustand.

**Design Doc:** `stj-vec/docs/plans/2026-03-08-stj-vec-search-design.md` (fonte de verdade para decisoes, API contracts, e arquitetura).

---

## Task 1: Exportar BGE-M3 para ONNX

**Files:**
- Create: `stj-vec/scripts/export_onnx.py`
- Create: `stj-vec/models/bge-m3-onnx/` (model.onnx, tokenizer.json -- fora do Git)
- Modify: `stj-vec/.gitignore`

**Step 1: Instalar dependencias**

```bash
cd /home/opc/lex-vector/stj-vec
uv pip install --python .venv/bin/python optimum[exporters] onnx onnxruntime transformers
```

**Step 2: Escrever script de exportacao**

```python
#!/usr/bin/env python3
"""Exporta BGE-M3 para ONNX via optimum."""
from optimum.exporters.onnx import main_export
from pathlib import Path

OUTPUT_DIR = Path("models/bge-m3-onnx")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

main_export(
    "BAAI/bge-m3",
    str(OUTPUT_DIR),
    task="feature-extraction",
    opset=17,
)

print(f"Modelo exportado em {OUTPUT_DIR}")
for f in sorted(OUTPUT_DIR.iterdir()):
    size_mb = f.stat().st_size / 1024 / 1024
    print(f"  {f.name}: {size_mb:.1f} MB")
```

**Step 3: Executar e validar**

```bash
cd /home/opc/lex-vector/stj-vec
.venv/bin/python scripts/export_onnx.py
ls -lh models/bge-m3-onnx/
```

Expected: `model.onnx` (~2.2GB), `tokenizer.json` (~14MB), `config.json`.

**Step 4: Validar que embedding funciona via ONNX**

```bash
.venv/bin/python -c "
import onnxruntime as ort
from transformers import AutoTokenizer
import numpy as np

sess = ort.InferenceSession('models/bge-m3-onnx/model.onnx')
tok = AutoTokenizer.from_pretrained('models/bge-m3-onnx')
inputs = tok('dano moral bancario', return_tensors='np', padding=True, truncation=True, max_length=512)
ort_inputs = {k: v for k, v in inputs.items() if k in [i.name for i in sess.get_inputs()]}
outputs = sess.run(None, ort_inputs)
print(f'Output shape: {outputs[0].shape}')  # Esperado: (1, seq_len, 1024)
dense = outputs[0].mean(axis=1)  # mean pooling
print(f'Dense shape: {dense.shape}')  # (1, 1024)
print(f'Dense norm: {np.linalg.norm(dense):.4f}')
print('OK: ONNX embedding funciona')
"
```

**Step 5: Adicionar models/ ao .gitignore**

```bash
echo "models/" >> stj-vec/.gitignore
```

**Step 6: Commit**

```bash
git add stj-vec/scripts/export_onnx.py stj-vec/.gitignore
git commit -m "feat(stj-vec): script de exportacao BGE-M3 para ONNX"
```

---

## Task 2: Scaffold do crate stj-vec-search

**Files:**
- Create: `stj-vec/crates/search/Cargo.toml`
- Create: `stj-vec/crates/search/src/main.rs`
- Create: `stj-vec/crates/search/src/config.rs`
- Create: `stj-vec/crates/search/src/error.rs`
- Create: `stj-vec/crates/search/src/types.rs`
- Create: `stj-vec/crates/search/src/lib.rs`
- Create: `stj-vec/search-config.toml`

**Step 1: Criar Cargo.toml**

```toml
[package]
name = "stj-vec-search"
version = "0.1.0"
edition = "2021"

[dependencies]
# Web framework
axum = { workspace = true }
tower-http = { version = "0.6", features = ["cors", "fs"] }
tokio = { workspace = true }

# Serialization
serde = { workspace = true }
serde_json = { workspace = true }
toml = { workspace = true }

# Logging
tracing = { workspace = true }
tracing-subscriber = { workspace = true }

# CLI
clap = { workspace = true }

# ONNX Runtime (embedding)
ort = { version = "2", features = ["load-dynamic"] }
tokenizers = "0.21"
ndarray = "0.16"

# Qdrant
qdrant-client = "1"

# SQLite
rusqlite = { workspace = true }
r2d2 = "0.8"
r2d2_sqlite = "0.25"

# Utils
anyhow = { workspace = true }
thiserror = { workspace = true }
uuid = { workspace = true }
```

**Step 2: Criar config.rs**

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct SearchConfig {
    pub server: ServerConfig,
    pub model: ModelConfig,
    pub qdrant: QdrantConfig,
    pub sqlite: SqliteConfig,
    pub search: SearchDefaults,
}

#[derive(Debug, Deserialize)]
pub struct ServerConfig {
    pub port: u16,
    pub static_dir: String,
    #[serde(default)]
    pub cors_origins: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct ModelConfig {
    pub dir: String,
    #[serde(default = "default_threads")]
    pub threads: usize,
}

#[derive(Debug, Deserialize)]
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

#[derive(Debug, Deserialize)]
pub struct SqliteConfig {
    pub path: String,
    #[serde(default = "default_pool_size")]
    pub pool_size: u32,
}

#[derive(Debug, Deserialize)]
pub struct SearchDefaults {
    #[serde(default = "default_max_results")]
    pub max_results: usize,
    #[serde(default = "default_limit")]
    pub default_limit: usize,
    #[serde(default = "default_overfetch")]
    pub overfetch_factor: usize,
}

fn default_threads() -> usize { 8 }
fn default_top_k() -> u64 { 200 }
fn default_rrf_k() -> f64 { 60.0 }
fn default_pool_size() -> u32 { 4 }
fn default_max_results() -> usize { 50 }
fn default_limit() -> usize { 20 }
fn default_overfetch() -> usize { 3 }
```

**Step 3: Criar types.rs**

Structs `SearchRequest`, `SearchResponse`, `SearchResultItem`, `Scores`, `QueryInfo`, `SearchFilters`, `DocumentResponse`, `DocumentChunk`, `DocumentMeta`, `HealthResponse`, `FiltersResponse`. Todos com `Serialize`/`Deserialize`. Ver design doc secao 7 para os JSON contracts exatos.

**Step 4: Criar error.rs**

```rust
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};

#[derive(Debug, thiserror::Error)]
pub enum SearchError {
    #[error("embedding failed: {0}")]
    Embedding(#[from] anyhow::Error),
    #[error("qdrant error: {0}")]
    Qdrant(String),
    #[error("sqlite error: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("not found: {0}")]
    NotFound(String),
    #[error("r2d2 pool error: {0}")]
    Pool(#[from] r2d2::Error),
}

impl IntoResponse for SearchError {
    fn into_response(self) -> Response {
        let status = match &self {
            SearchError::NotFound(_) => StatusCode::NOT_FOUND,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };
        (status, self.to_string()).into_response()
    }
}
```

**Step 5: Criar lib.rs (re-exports)**

```rust
pub mod config;
pub mod error;
pub mod types;
```

**Step 6: Criar main.rs minimal**

```rust
use clap::Parser;
use std::path::PathBuf;

#[derive(Parser)]
struct Cli {
    #[arg(long, default_value = "search-config.toml")]
    config: PathBuf,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    let cli = Cli::parse();
    let config_str = std::fs::read_to_string(&cli.config)?;
    let config: stj_vec_search::config::SearchConfig = toml::from_str(&config_str)?;
    tracing::info!("Config loaded from {:?}", cli.config);
    tracing::info!("Server would start on port {}", config.server.port);
    Ok(())
}
```

**Step 7: Criar search-config.toml**

Conteudo conforme design doc secao 9.1.

**Step 8: Verificar compilacao**

```bash
cd /home/opc/lex-vector/stj-vec
cargo check -p stj-vec-search
```

Expected: compila sem erros.

**Step 9: Commit**

```bash
git add stj-vec/crates/search/ stj-vec/search-config.toml
git commit -m "feat(stj-vec): scaffold do crate stj-vec-search (config, types, error)"
```

---

## Task 3: OnnxEmbedder -- embedding de queries

**Files:**
- Create: `stj-vec/crates/search/src/embedder.rs`
- Modify: `stj-vec/crates/search/src/lib.rs`

**Prerequisite:** Task 1 completa (modelo ONNX em `models/bge-m3-onnx/`).

**Step 1: Escrever teste de integracao**

```rust
// No final de embedder.rs ou em tests/
#[cfg(test)]
mod tests {
    use super::*;
    use std::path::Path;

    #[test]
    fn test_embed_produces_1024d_dense() {
        let model_dir = Path::new("models/bge-m3-onnx");
        if !model_dir.exists() {
            eprintln!("Skipping: model dir not found");
            return;
        }
        let embedder = OnnxEmbedder::load(model_dir, 4).unwrap();
        let output = embedder.embed("dano moral bancario").unwrap();
        assert_eq!(output.dense.len(), 1024);
        assert!(output.elapsed_ms < 5000);
    }

    #[test]
    fn test_embed_sparse_not_empty() {
        let model_dir = Path::new("models/bge-m3-onnx");
        if !model_dir.exists() {
            eprintln!("Skipping: model dir not found");
            return;
        }
        let embedder = OnnxEmbedder::load(model_dir, 4).unwrap();
        let output = embedder.embed("responsabilidade civil objetiva").unwrap();
        assert!(!output.sparse.is_empty(), "sparse weights should not be empty");
    }

    #[test]
    fn test_embed_deterministic() {
        let model_dir = Path::new("models/bge-m3-onnx");
        if !model_dir.exists() {
            eprintln!("Skipping: model dir not found");
            return;
        }
        let embedder = OnnxEmbedder::load(model_dir, 4).unwrap();
        let a = embedder.embed("teste").unwrap();
        let b = embedder.embed("teste").unwrap();
        assert_eq!(a.dense, b.dense);
    }
}
```

**Step 2: Run tests to verify they fail**

```bash
cargo test -p stj-vec-search -- embedder --nocapture
```

Expected: FAIL (OnnxEmbedder not defined).

**Step 3: Implementar OnnxEmbedder**

```rust
use std::collections::HashMap;
use std::path::Path;
use std::time::Instant;
use anyhow::{Context, Result};

pub struct OnnxEmbedder {
    session: ort::Session,
    tokenizer: tokenizers::Tokenizer,
}

pub struct EmbeddingOutput {
    pub dense: Vec<f32>,
    pub sparse: HashMap<u32, f32>,
    pub elapsed_ms: u64,
}

impl OnnxEmbedder {
    pub fn load(model_dir: &Path, threads: usize) -> Result<Self> {
        let model_path = model_dir.join("model.onnx");
        let tokenizer_path = model_dir.join("tokenizer.json");

        let session = ort::Session::builder()?
            .with_intra_threads(threads)?
            .commit_from_file(&model_path)
            .context("Failed to load ONNX model")?;

        let tokenizer = tokenizers::Tokenizer::from_file(&tokenizer_path)
            .map_err(|e| anyhow::anyhow!("Failed to load tokenizer: {}", e))?;

        Ok(Self { session, tokenizer })
    }

    pub fn embed(&self, text: &str) -> Result<EmbeddingOutput> {
        let start = Instant::now();

        // Tokenize
        let encoding = self.tokenizer.encode(text, true)
            .map_err(|e| anyhow::anyhow!("Tokenization failed: {}", e))?;

        let input_ids: Vec<i64> = encoding.get_ids().iter().map(|&id| id as i64).collect();
        let attention_mask: Vec<i64> = encoding.get_attention_mask().iter().map(|&m| m as i64).collect();
        let token_type_ids: Vec<i64> = encoding.get_type_ids().iter().map(|&t| t as i64).collect();
        let seq_len = input_ids.len();

        // Create tensors
        let ids_array = ndarray::Array2::from_shape_vec((1, seq_len), input_ids)?;
        let mask_array = ndarray::Array2::from_shape_vec((1, seq_len), attention_mask.clone())?;
        let types_array = ndarray::Array2::from_shape_vec((1, seq_len), token_type_ids)?;

        // Run inference
        let outputs = self.session.run(ort::inputs![ids_array, mask_array, types_array]?)?;

        // Extract dense: mean pooling of last_hidden_state
        let hidden_state = outputs[0].try_extract_tensor::<f32>()?;
        let hidden_view = hidden_state.view();
        // Shape: (1, seq_len, 1024)
        let dim = hidden_view.shape()[2];
        let mut dense = vec![0.0f32; dim];
        let mut count = 0.0f32;
        for t in 0..seq_len {
            if attention_mask[t] == 1 {
                for d in 0..dim {
                    dense[d] += hidden_view[[0, t, d]];
                }
                count += 1.0;
            }
        }
        for d in dense.iter_mut() {
            *d /= count;
        }
        // L2 normalize
        let norm: f32 = dense.iter().map(|x| x * x).sum::<f32>().sqrt();
        if norm > 0.0 {
            for d in dense.iter_mut() {
                *d /= norm;
            }
        }

        // Extract sparse: per-token max weight from hidden state
        // Simplified approach: use token IDs as dimensions, max-pool weights
        let mut sparse = HashMap::new();
        for t in 1..seq_len.saturating_sub(1) { // skip [CLS] and [SEP]
            if attention_mask[t] == 1 {
                let token_id = encoding.get_ids()[t];
                let weight: f32 = (0..dim).map(|d| hidden_view[[0, t, d]]).fold(0.0f32, f32::max);
                let weight = weight.max(0.0); // ReLU
                if weight > 0.01 { // threshold
                    sparse.entry(token_id)
                        .and_modify(|w: &mut f32| *w = w.max(weight))
                        .or_insert(weight);
                }
            }
        }

        let elapsed_ms = start.elapsed().as_millis() as u64;
        Ok(EmbeddingOutput { dense, sparse, elapsed_ms })
    }
}
```

**NOTA IMPORTANTE:** A geracao de sparse embeddings acima e uma aproximacao simplificada. O BGE-M3 real usa uma camada `sparse_linear` treinada que pode nao estar exposta no ONNX default. Se os sparse weights forem de baixa qualidade, o fallback documentado no design doc e usar TF (term frequency) simples via token IDs. Testar empiricamente comparando com o output do FlagEmbedding Python.

**Step 4: Run tests to verify they pass**

```bash
cd /home/opc/lex-vector/stj-vec
cargo test -p stj-vec-search -- embedder --nocapture
```

Expected: 3 tests pass.

**Step 5: Commit**

```bash
git add stj-vec/crates/search/src/embedder.rs stj-vec/crates/search/src/lib.rs
git commit -m "feat(stj-vec): OnnxEmbedder com dense+sparse BGE-M3 via ONNX Runtime"
```

---

## Task 4: QdrantSearcher -- busca gRPC + fusao RRF

**Files:**
- Create: `stj-vec/crates/search/src/searcher.rs`
- Modify: `stj-vec/crates/search/src/lib.rs`

**Step 1: Escrever teste unitario para fuse_rrf**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rrf_both_sides() {
        let dense = vec![
            ("a".into(), 0.9f32),
            ("b".into(), 0.8),
            ("c".into(), 0.7),
        ];
        let sparse = vec![
            ("b".into(), 15.0f32),
            ("d".into(), 12.0),
            ("a".into(), 10.0),
        ];
        let fused = fuse_rrf(&dense, &sparse, 10, 60.0);
        // "b" deve ter maior RRF: rank 2 dense + rank 1 sparse
        assert_eq!(fused[0].chunk_id, "b");
        assert_eq!(fused[0].dense_rank, 2);
        assert_eq!(fused[0].sparse_rank, 1);
    }

    #[test]
    fn test_rrf_single_side_only() {
        let dense = vec![("x".into(), 0.5f32)];
        let sparse: Vec<(String, f32)> = vec![];
        let fused = fuse_rrf(&dense, &sparse, 10, 60.0);
        assert_eq!(fused.len(), 1);
        assert_eq!(fused[0].chunk_id, "x");
        assert_eq!(fused[0].sparse_rank, 0); // nao apareceu no sparse
    }

    #[test]
    fn test_rrf_respects_limit() {
        let dense: Vec<(String, f32)> = (0..100).map(|i| (format!("d{i}"), 1.0 - i as f32 * 0.01)).collect();
        let sparse: Vec<(String, f32)> = (0..100).map(|i| (format!("s{i}"), 50.0 - i as f32 * 0.5)).collect();
        let fused = fuse_rrf(&dense, &sparse, 5, 60.0);
        assert_eq!(fused.len(), 5);
    }
}
```

**Step 2: Run tests to verify they fail**

```bash
cargo test -p stj-vec-search -- searcher --nocapture
```

Expected: FAIL (fuse_rrf not defined).

**Step 3: Implementar fuse_rrf**

```rust
pub struct RankedResult {
    pub chunk_id: String,
    pub dense_score: f32,
    pub sparse_score: f32,
    pub dense_rank: usize,
    pub sparse_rank: usize,
    pub rrf_score: f64,
}

pub fn fuse_rrf(
    dense: &[(String, f32)],
    sparse: &[(String, f32)],
    limit: usize,
    rrf_k: f64,
) -> Vec<RankedResult> {
    let mut scores: HashMap<String, RankedResult> = HashMap::new();

    for (rank, (cid, score)) in dense.iter().enumerate() {
        scores.entry(cid.clone()).or_insert_with(|| RankedResult {
            chunk_id: cid.clone(),
            dense_score: 0.0, sparse_score: 0.0,
            dense_rank: 0, sparse_rank: 0, rrf_score: 0.0,
        });
        let entry = scores.get_mut(cid).unwrap();
        entry.dense_score = *score;
        entry.dense_rank = rank + 1;
        entry.rrf_score += 1.0 / (rrf_k + (rank + 1) as f64);
    }

    for (rank, (cid, score)) in sparse.iter().enumerate() {
        scores.entry(cid.clone()).or_insert_with(|| RankedResult {
            chunk_id: cid.clone(),
            dense_score: 0.0, sparse_score: 0.0,
            dense_rank: 0, sparse_rank: 0, rrf_score: 0.0,
        });
        let entry = scores.get_mut(cid).unwrap();
        entry.sparse_score = *score;
        entry.sparse_rank = rank + 1;
        entry.rrf_score += 1.0 / (rrf_k + (rank + 1) as f64);
    }

    let mut results: Vec<RankedResult> = scores.into_values().collect();
    results.sort_by(|a, b| b.rrf_score.partial_cmp(&a.rrf_score).unwrap());
    results.truncate(limit);
    results
}
```

**Step 4: Run RRF tests to verify they pass**

```bash
cargo test -p stj-vec-search -- searcher::tests --nocapture
```

Expected: 3 tests pass.

**Step 5: Implementar QdrantSearcher**

```rust
use qdrant_client::Qdrant;
use qdrant_client::qdrant::{SearchPointsBuilder, with_payload_selector::SelectorOptions, WithPayloadSelector, PayloadIncludeSelector};
use std::collections::HashMap;

pub struct QdrantSearcher {
    client: Qdrant,
    collection: String,
    dense_top_k: u64,
    sparse_top_k: u64,
    rrf_k: f64,
}

impl QdrantSearcher {
    pub async fn new(url: &str, collection: &str, dense_top_k: u64, sparse_top_k: u64, rrf_k: f64) -> Result<Self> {
        let client = Qdrant::from_url(url).build()?;
        Ok(Self {
            client,
            collection: collection.to_string(),
            dense_top_k, sparse_top_k, rrf_k,
        })
    }

    pub async fn search(
        &self,
        dense_vec: &[f32],
        sparse: &HashMap<u32, f32>,
        limit: usize,
    ) -> Result<Vec<RankedResult>> {
        let (indices, values): (Vec<u32>, Vec<f32>) = sparse.iter().map(|(&k, &v)| (k, v)).unzip();

        // Two parallel gRPC queries
        let (dense_res, sparse_res) = tokio::join!(
            self.search_dense(dense_vec),
            self.search_sparse(&indices, &values)
        );

        let dense_results = Self::extract_results(dense_res?);
        let sparse_results = Self::extract_results(sparse_res?);

        Ok(fuse_rrf(&dense_results, &sparse_results, limit, self.rrf_k))
    }

    // search_dense and search_sparse use qdrant_client API
    // extract_results maps ScoredPoint -> (chunk_id, score)
}
```

Implementacao completa dos metodos privados `search_dense`, `search_sparse`, `extract_results` usando a API do `qdrant-client` crate. O `chunk_id` e extraido do payload de cada ponto.

**Step 6: Teste de integracao (requer Qdrant)**

```rust
#[tokio::test]
#[ignore] // requer Qdrant local com collection stj
async fn test_qdrant_search_integration() {
    let searcher = QdrantSearcher::new(
        "http://localhost:6334", "stj", 200, 200, 60.0
    ).await.unwrap();
    let dummy_dense = vec![0.1f32; 1024];
    let dummy_sparse = HashMap::from([(1u32, 1.0f32), (100, 0.5)]);
    let results = searcher.search(&dummy_dense, &dummy_sparse, 10).await.unwrap();
    assert!(!results.is_empty(), "should return results from Qdrant");
    // Verificar que chunk_ids sao strings nao-vazias
    for r in &results {
        assert!(!r.chunk_id.is_empty());
    }
}
```

**Step 7: Run integration test**

```bash
cargo test -p stj-vec-search -- qdrant_search_integration --ignored --nocapture
```

Expected: PASS (Qdrant rodando em localhost:6334).

**Step 8: Commit**

```bash
git add stj-vec/crates/search/src/searcher.rs stj-vec/crates/search/src/lib.rs
git commit -m "feat(stj-vec): QdrantSearcher com busca paralela gRPC + fusao RRF local"
```

---

## Task 5: MetadataStore -- SQLite read-only

**Files:**
- Create: `stj-vec/crates/search/src/metadata.rs`
- Modify: `stj-vec/crates/search/src/lib.rs`

**Step 1: Escrever testes**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_open_readonly() {
        let store = MetadataStore::open("../db/stj-vec.db", 2);
        assert!(store.is_ok(), "should open stj-vec.db read-only");
    }

    #[test]
    fn test_get_filter_values() {
        let store = MetadataStore::open("../db/stj-vec.db", 2).unwrap();
        let filters = store.get_filter_values().unwrap();
        assert!(!filters.ministros.is_empty());
        assert!(!filters.tipos.is_empty());
    }

    #[test]
    fn test_get_document_chunks() {
        let store = MetadataStore::open("../db/stj-vec.db", 2).unwrap();
        // Buscar um doc_id real
        let conn = store.pool.get().unwrap();
        let doc_id: String = conn.query_row(
            "SELECT id FROM documents LIMIT 1", [], |row| row.get(0)
        ).unwrap();
        let doc_resp = store.get_document_chunks(&doc_id).unwrap();
        assert!(!doc_resp.chunks.is_empty());
    }
}
```

**Step 2: Run tests to verify they fail**

```bash
cargo test -p stj-vec-search -- metadata --nocapture
```

**Step 3: Implementar MetadataStore**

```rust
use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;
use rusqlite::params;

pub struct MetadataStore {
    pool: Pool<SqliteConnectionManager>,
}

impl MetadataStore {
    pub fn open(path: &str, pool_size: u32) -> Result<Self> {
        let manager = SqliteConnectionManager::file(path)
            .with_flags(rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY);
        let pool = Pool::builder()
            .max_size(pool_size)
            .build(manager)?;
        Ok(Self { pool })
    }

    pub fn get_chunks_with_metadata(&self, chunk_ids: &[String]) -> Result<HashMap<String, ChunkWithMetadata>> {
        let conn = self.pool.get()?;
        // Build IN clause with bind params
        let placeholders: String = chunk_ids.iter().map(|_| "?").collect::<Vec<_>>().join(",");
        let sql = format!(
            "SELECT c.id, c.content, c.chunk_index, c.doc_id, \
             d.processo, d.classe, d.ministro, d.orgao_julgador, \
             d.data_julgamento, d.tipo, d.assuntos \
             FROM chunks c JOIN documents d ON d.id = c.doc_id \
             WHERE c.id IN ({})", placeholders
        );
        let mut stmt = conn.prepare(&sql)?;
        let params: Vec<&dyn rusqlite::types::ToSql> = chunk_ids.iter().map(|s| s as &dyn rusqlite::types::ToSql).collect();
        let rows = stmt.query_map(params.as_slice(), |row| { /* map to ChunkWithMetadata */ })?;
        // Collect into HashMap
    }

    pub fn get_document_chunks(&self, doc_id: &str) -> Result<DocumentResponse> {
        // SELECT from documents + chunks WHERE doc_id = ? ORDER BY chunk_index
    }

    pub fn get_filter_values(&self) -> Result<FiltersResponse> {
        // SELECT DISTINCT ministro, classe, tipo, orgao_julgador
    }

    pub fn filter_chunk_ids(&self, chunk_ids: &[String], filters: &SearchFilters) -> Result<Vec<String>> {
        // JOIN + WHERE clause with optional filters, return subset of chunk_ids
    }
}
```

**Step 4: Run tests**

```bash
cargo test -p stj-vec-search -- metadata --nocapture
```

Expected: 3 tests pass.

**Step 5: Commit**

```bash
git add stj-vec/crates/search/src/metadata.rs stj-vec/crates/search/src/lib.rs
git commit -m "feat(stj-vec): MetadataStore read-only com pool r2d2 e batch queries"
```

---

## Task 6: Rotas axum e integracao do pipeline

**Files:**
- Create: `stj-vec/crates/search/src/routes.rs`
- Modify: `stj-vec/crates/search/src/main.rs`
- Modify: `stj-vec/crates/search/src/lib.rs`

**Step 1: Definir AppState**

```rust
use std::sync::Arc;
use std::time::Instant;

pub struct AppState {
    pub embedder: Arc<OnnxEmbedder>,
    pub searcher: Arc<QdrantSearcher>,
    pub metadata: Arc<MetadataStore>,
    pub filters_cache: Arc<FiltersResponse>,
    pub config: SearchConfig,
    pub start_time: Instant,
}
```

**Step 2: Implementar handlers**

```rust
pub async fn search_handler(
    State(state): State<Arc<AppState>>,
    Json(req): Json<SearchRequest>,
) -> Result<Json<SearchResponse>, SearchError> {
    let total_start = Instant::now();

    // 1. Embed
    let embed_start = Instant::now();
    let embedding = state.embedder.embed(&req.query)?;
    let embedding_ms = embed_start.elapsed().as_millis() as u64;

    // 2. Search Qdrant
    let search_start = Instant::now();
    let limit = req.limit.unwrap_or(state.config.search.default_limit);
    let qdrant_limit = if req.filters.is_some() { limit * state.config.search.overfetch_factor } else { limit };
    let ranked = state.searcher.search(&embedding.dense, &embedding.sparse, qdrant_limit).await?;
    let search_ms = search_start.elapsed().as_millis() as u64;

    // 3. Get metadata
    let meta_start = Instant::now();
    let chunk_ids: Vec<String> = ranked.iter().map(|r| r.chunk_id.clone()).collect();
    let metadata_map = state.metadata.get_chunks_with_metadata(&chunk_ids)?;
    let metadata_ms = meta_start.elapsed().as_millis() as u64;

    // 4. Apply filters if present + build response
    // 5. Truncate to limit

    let total_ms = total_start.elapsed().as_millis() as u64;
    // Return SearchResponse with results + query_info
}

pub async fn document_handler(/* ... */) -> Result<Json<DocumentResponse>, SearchError> { /* ... */ }
pub async fn health_handler(/* ... */) -> Result<Json<HealthResponse>, SearchError> { /* ... */ }
pub async fn filters_handler(/* ... */) -> Json<FiltersResponse> { /* ... */ }
```

**Step 3: Implementar main.rs completo**

Startup sequence conforme design doc secao 9.2:
1. Load config
2. Open SQLite pool
3. Load ONNX model
4. Connect Qdrant, verify collection
5. Cache filter values
6. Create router (API routes + static files via ServeDir)
7. Start axum server

**Step 4: Teste manual end-to-end**

```bash
# Terminal 1: start server
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-search -- --config search-config.toml

# Terminal 2: test endpoints
curl http://localhost:8421/api/health | python3 -m json.tool
curl -X POST http://localhost:8421/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "dano moral bancario", "limit": 5}' | python3 -m json.tool
curl http://localhost:8421/api/filters | python3 -m json.tool
```

Expected: health retorna ok, search retorna resultados com scores, filters retorna listas.

**Step 5: Commit**

```bash
git add stj-vec/crates/search/src/routes.rs stj-vec/crates/search/src/main.rs stj-vec/crates/search/src/lib.rs
git commit -m "feat(stj-vec): rotas axum com pipeline completo (embed -> qdrant -> metadata)"
```

---

## Task 7: Scaffold do frontend React

**Files:**
- Create: `stj-vec/frontend/` (package.json, vite.config.ts, tsconfig*.json, index.html, src/)
- Template: copiar e adaptar de `/home/opc/.claude/claude-memory-frontend/`

**Step 1: Copiar estrutura base do template**

Copiar: package.json, vite.config.ts, tsconfig.json, tsconfig.app.json, tsconfig.node.json, index.html, src/main.tsx, src/styles/globals.css. Adaptar nomes e paths.

**Step 2: Criar types.ts espelhando API**

```typescript
// src/api/types.ts
export interface SearchRequest {
  query: string;
  limit?: number;
  filters?: SearchFilters;
}

export interface SearchFilters {
  ministro?: string;
  tipo?: string;
  classe?: string;
  orgao_julgador?: string;
  data_from?: string;
  data_to?: string;
}

export interface Scores {
  dense: number;
  sparse: number;
  rrf: number;
  dense_rank: number;
  sparse_rank: number;
}

export interface SearchResultItem {
  chunk_id: string;
  content: string;
  chunk_index: number;
  doc_id: string;
  processo: string;
  classe: string;
  ministro: string;
  orgao_julgador: string;
  data_julgamento: string;
  tipo: string;
  assuntos: string;
  scores: Scores;
}

export interface QueryInfo {
  embedding_ms: number;
  search_ms: number;
  metadata_ms: number;
  total_ms: number;
  dense_candidates: number;
  sparse_candidates: number;
  pre_filter_count: number;
  post_filter_count: number;
}

export interface SearchResponse {
  results: SearchResultItem[];
  query_info: QueryInfo;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  content: string;
  token_count: number;
}

export interface DocumentMeta {
  id: string;
  processo: string;
  classe: string;
  ministro: string;
  orgao_julgador: string;
  data_julgamento: string;
  data_publicacao: string;
  tipo: string;
  assuntos: string;
}

export interface DocumentResponse {
  document: DocumentMeta;
  chunks: DocumentChunk[];
  total_chunks: number;
}

export interface HealthResponse {
  status: string;
  qdrant: boolean;
  sqlite: boolean;
  model_loaded: boolean;
  collection_points: number;
  uptime_secs: number;
}

export interface FiltersResponse {
  ministros: string[];
  classes: string[];
  tipos: string[];
  orgaos_julgadores: string[];
}
```

**Step 3: Criar client.ts**

```typescript
const API_BASE = import.meta.env.VITE_API_URL ?? '';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export const api = {
  search: (body: SearchRequest) =>
    fetchJson<SearchResponse>('/api/search', { method: 'POST', body: JSON.stringify(body) }),
  document: (docId: string) =>
    fetchJson<DocumentResponse>(`/api/document/${docId}`),
  health: () => fetchJson<HealthResponse>('/api/health'),
  filters: () => fetchJson<FiltersResponse>('/api/filters'),
};
```

**Step 4: Criar App.tsx e main.tsx minimos**

App.tsx com QueryClientProvider, SearchView placeholder.

**Step 5: bun install + verificar dev server**

```bash
cd /home/opc/lex-vector/stj-vec/frontend
bun install
bun run dev
```

Expected: dev server roda em localhost:5173.

**Step 6: Commit**

```bash
git add stj-vec/frontend/
git commit -m "feat(stj-vec): scaffold frontend React 19 + Vite 7 + Tailwind 4"
```

---

## Task 8: Hooks, store e componentes base

**Files:**
- Create: `stj-vec/frontend/src/hooks/use-search.ts`
- Create: `stj-vec/frontend/src/hooks/use-document.ts`
- Create: `stj-vec/frontend/src/hooks/use-filters.ts`
- Create: `stj-vec/frontend/src/hooks/use-health.ts`
- Create: `stj-vec/frontend/src/store/app-store.ts`
- Create: `stj-vec/frontend/src/components/indicators/MatchingLog.tsx`
- Copy+adapt: ScoreBar, Skeleton, ApertureSpinner from template

**Step 1: Implementar hooks TanStack Query**

```typescript
// use-search.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/api/client';
import type { SearchFilters } from '@/api/types';

export function useSearch(query: string, filters?: SearchFilters, limit?: number) {
  return useQuery({
    queryKey: ['search', query, filters, limit],
    queryFn: () => api.search({ query, limit, filters }),
    enabled: query.length > 2,
    staleTime: 5 * 60 * 1000,
  });
}
```

Idem para use-document, use-filters, use-health.

**Step 2: Implementar store Zustand**

```typescript
import { create } from 'zustand';

interface AppState {
  query: string;
  submittedQuery: string;
  filters: SearchFilters;
  selectedChunkId: string | null;
  selectedDocId: string | null;
  setQuery: (q: string) => void;
  submitQuery: () => void;
  setFilter: (key: string, value: string | null) => void;
  selectResult: (chunkId: string, docId: string) => void;
  clearSelection: () => void;
}
```

**Step 3: Criar MatchingLog.tsx**

```tsx
interface MatchingLogProps {
  scores: Scores;
}

// Renderiza: D: 0.847 #3  |  S: 12.34 #7  |  RRF: 0.033
// Cor indica forca relativa (verde = top, amarelo = mid, cinza = low)
```

**Step 4: Copiar e adaptar indicadores do template**

ScoreBar (adaptar escala RRF), Skeleton, ApertureSpinner.

**Step 5: Commit**

```bash
git add stj-vec/frontend/src/hooks/ stj-vec/frontend/src/store/ stj-vec/frontend/src/components/indicators/
git commit -m "feat(stj-vec): hooks TanStack Query, store Zustand, componentes indicadores"
```

---

## Task 9: SearchView completo

**Files:**
- Create: `stj-vec/frontend/src/components/views/SearchView.tsx`
- Create: `stj-vec/frontend/src/components/layout/FilterPanel.tsx`
- Modify: `stj-vec/frontend/src/App.tsx`

**Step 1: Implementar FilterPanel**

Dropdowns para ministro, tipo, classe, orgao_julgador. Date pickers para data_from/data_to. Usa dados de `useFilters()`.

**Step 2: Implementar SearchView**

Layout conforme design doc secao 8.3:
- Input de busca (topo)
- Filter bar
- Resultados (esquerda): card com processo, ministro, trecho, MatchingLog
- Preview (direita): documento expandido via `/api/document/:doc_id`, chunk matchado destacado

Adaptar do template `SearchView.tsx` (estrutura split-panel ja existe). Diferenca principal: metadados juridicos em vez de sessao/timestamp, e MatchingLog em vez de ScoreBar simples.

**Step 3: Conectar App.tsx ao SearchView**

**Step 4: Teste visual**

```bash
# Backend rodando (Task 6)
cd stj-vec/frontend && bun run dev
# Abrir localhost:5173, fazer query, verificar resultados
```

**Step 5: Commit**

```bash
git add stj-vec/frontend/src/components/views/ stj-vec/frontend/src/components/layout/ stj-vec/frontend/src/App.tsx
git commit -m "feat(stj-vec): SearchView com filtros, resultados juridicos e MatchingLog"
```

---

## Task 10: Build de producao e servir via axum

**Files:**
- Modify: `stj-vec/frontend/vite.config.ts` (build outDir)
- Verify: `stj-vec/crates/search/src/main.rs` (ServeDir)

**Step 1: Configurar build para dist/**

```typescript
// vite.config.ts
export default defineConfig({
  build: { outDir: 'dist' },
  server: { proxy: { '/api': 'http://localhost:8421' } },
});
```

**Step 2: Build**

```bash
cd stj-vec/frontend
bun run build
ls -la dist/
```

Expected: index.html + assets/ com JS/CSS.

**Step 3: Verificar que axum serve o frontend**

```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-search -- --config search-config.toml
# Abrir http://localhost:8421 no browser
```

Expected: frontend carrega, busca funciona end-to-end.

**Step 4: Commit**

```bash
git add stj-vec/frontend/
git commit -m "feat(stj-vec): build de producao do frontend servido via axum"
```

---

## Dependencias entre Tasks

```
Task 1 (ONNX export) ──────┐
                            v
Task 2 (scaffold crate) ──> Task 3 (embedder) ──> Task 6 (routes)
                            Task 4 (searcher)  ──> Task 6
                            Task 5 (metadata)  ──> Task 6
                                                      |
Task 7 (scaffold frontend) ──> Task 8 (hooks) ──> Task 9 (SearchView) ──> Task 10 (build)
                                                      |
                                                   Task 6 (backend pronto)
```

**Paralelismo possivel:**
- Tasks 3, 4, 5 podem rodar em paralelo (depois de Task 2)
- Tasks 7, 8 podem rodar em paralelo com Tasks 3-5 (frontend independe do backend)
- Task 9 depende de Task 6 (backend) + Task 8 (hooks)
- Task 10 depende de Task 9 + Task 6

# stj-vec Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rust workspace for semantic vector search over ~2M STJ legal documents, with incremental ingestion pipeline and daemon server.

**Architecture:** Cargo workspace with 3 crates -- core (lib: types, storage, chunker, embedder trait), server (bin: axum daemon with socket+HTTP), ingest (bin: CLI pipeline scan->chunk->embed->done). SQLite + sqlite-vec for storage. Embedding model/dim are config placeholders (Modal TBD).

**Tech Stack:** Rust stable, tokio, axum, rusqlite + sqlite-vec, serde, clap v4, tracing, thiserror, zip crate

**Design doc:** `docs/plans/2026-02-23-stj-vec-design.md`

---

## Data Format Reference

**Textos:** `/home/opc/juridico-data/stj/integras/textos/{YYYYMM ou YYYYMMDD}/{seqDocumento}.txt`
- 857 subdiretorios, ~59k arquivos por consolidado mensal
- Conteudo: texto com HTML inline (`<br>`, `&nbsp;` etc), encoding UTF-8
- Nome do arquivo = seqDocumento (ID unico)

**Metadados:** `/home/opc/juridico-data/stj/integras/metadata/metadados{YYYYMM ou YYYYMMDD}.json`
- JSON array de objetos com: seqDocumento, processo, ministro, tipoDocumento, dataPublicacao (epoch ms), assuntos, teor, recurso

---

### Task 1: Scaffold workspace e crates

**Files:**
- Create: `stj-vec/Cargo.toml`
- Create: `stj-vec/.gitignore`
- Create: `stj-vec/config.toml`
- Create: `stj-vec/crates/core/Cargo.toml`
- Create: `stj-vec/crates/core/src/lib.rs`
- Create: `stj-vec/crates/server/Cargo.toml`
- Create: `stj-vec/crates/server/src/main.rs`
- Create: `stj-vec/crates/ingest/Cargo.toml`
- Create: `stj-vec/crates/ingest/src/main.rs`
- Create: `stj-vec/scripts/export-for-modal.sh`
- Create: `stj-vec/scripts/import-from-modal.sh`

**Step 1: Create workspace Cargo.toml**

```toml
[workspace]
resolver = "2"
members = ["crates/*"]

[workspace.dependencies]
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
anyhow = "1"
thiserror = "2"
clap = { version = "4", features = ["derive"] }
rusqlite = { version = "0.33", features = ["bundled"] }
sqlite-vec = "0.1.7-alpha.2"
zerocopy = "0.7"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
axum = "0.8"
tower-http = { version = "0.6", features = ["cors"] }
toml = "0.8"
uuid = { version = "1", features = ["v4"] }
md5 = "0.7"
chrono = { version = "0.4", features = ["serde"] }
indicatif = "0.17"
reqwest = { version = "0.12", features = ["json"] }
zip = "2"
async-trait = "0.1"
```

**Step 2: Create crate Cargo.tomls**

core/Cargo.toml:
```toml
[package]
name = "stj-vec-core"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
anyhow = { workspace = true }
thiserror = { workspace = true }
rusqlite = { workspace = true }
sqlite-vec = { workspace = true }
zerocopy = { workspace = true }
toml = { workspace = true }
uuid = { workspace = true }
md5 = { workspace = true }
chrono = { workspace = true }
async-trait = { workspace = true }
tracing = { workspace = true }
```

server/Cargo.toml:
```toml
[package]
name = "stj-vec-server"
version = "0.1.0"
edition = "2021"

[dependencies]
stj-vec-core = { path = "../core" }
tokio = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
anyhow = { workspace = true }
clap = { workspace = true }
axum = { workspace = true }
tower-http = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
reqwest = { workspace = true }
async-trait = { workspace = true }
tokio-util = "0.7"
```

ingest/Cargo.toml:
```toml
[package]
name = "stj-vec-ingest"
version = "0.1.0"
edition = "2021"

[dependencies]
stj-vec-core = { path = "../core" }
tokio = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
anyhow = { workspace = true }
clap = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
indicatif = { workspace = true }
zip = { workspace = true }
chrono = { workspace = true }
```

**Step 3: Create minimal src files (hello world)**

core/src/lib.rs:
```rust
pub mod config;
pub mod error;
pub mod types;
pub mod storage;
pub mod chunker;
pub mod embedder;
```

server/src/main.rs:
```rust
fn main() {
    println!("stj-vec-server");
}
```

ingest/src/main.rs:
```rust
fn main() {
    println!("stj-vec-ingest");
}
```

**Step 4: Create config.toml, .gitignore, placeholder scripts**

config.toml: copiar do design doc.

.gitignore:
```
/target
/db/
```

scripts/export-for-modal.sh e import-for-modal.sh:
```bash
#!/bin/bash
# PLACEHOLDER -- implementar quando Modal estiver configurado
echo "TODO: Modal integration"
exit 1
```

**Step 5: Verify workspace compiles**

Run: `cd /home/opc/lex-vector/stj-vec && cargo check`
Expected: compiles (com erros de modulos faltantes no core, ok)

**Step 6: Commit**

```bash
git add stj-vec/
git commit -m "feat(stj-vec): scaffold workspace with 3 crates"
```

---

### Task 2: Core -- types.rs e error.rs

**Files:**
- Create: `stj-vec/crates/core/src/types.rs`
- Create: `stj-vec/crates/core/src/error.rs`

**Step 1: Write types.rs**

```rust
use serde::{Deserialize, Serialize};

/// Documento STJ (metadados do acordao/decisao)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Document {
    pub id: String,
    pub processo: Option<String>,
    pub classe: Option<String>,
    pub ministro: Option<String>,
    pub orgao_julgador: Option<String>,
    pub data_publicacao: Option<String>,
    pub data_julgamento: Option<String>,
    pub assuntos: Option<String>,
    pub teor: Option<String>,
    pub tipo: Option<String>,
    pub chunk_count: i32,
    pub source_file: Option<String>,
}

/// Chunk de texto com posicao no documento
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Chunk {
    pub id: String,
    pub doc_id: String,
    pub chunk_index: i32,
    pub content: String,
    pub token_count: i32,
}

/// Resultado de busca: chunk + score + metadados do documento
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub score: f64,
    pub chunk: Chunk,
    pub document: Document,
}

/// Filtros opcionais para busca
#[derive(Debug, Default, Clone, Serialize, Deserialize)]
pub struct SearchFilters {
    pub ministro: Option<String>,
    pub tipo: Option<String>,
    pub orgao_julgador: Option<String>,
    pub data_from: Option<String>,
    pub data_to: Option<String>,
}

/// Estatisticas do banco
#[derive(Debug, Serialize, Deserialize)]
pub struct DbStats {
    pub document_count: i64,
    pub chunk_count: i64,
    pub embedding_count: i64,
    pub ingest_pending: i64,
    pub ingest_chunked: i64,
    pub ingest_done: i64,
}

/// Status de ingestion de um arquivo
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IngestStatus {
    pub source_file: String,
    pub status: String,
    pub doc_count: i32,
    pub chunk_count: i32,
    pub error: Option<String>,
}

/// Metadado bruto do JSON do STJ
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StjMetadata {
    pub seq_documento: i64,
    pub data_publicacao: Option<i64>,
    pub tipo_documento: Option<String>,
    pub numero_registro: Option<String>,
    pub processo: Option<String>,
    pub ministro: Option<String>,
    pub recurso: Option<String>,
    pub teor: Option<String>,
    pub assuntos: Option<String>,
}
```

**Step 2: Write error.rs**

```rust
#[derive(Debug, thiserror::Error)]
pub enum StjVecError {
    #[error("storage error: {0}")]
    Storage(#[from] rusqlite::Error),

    #[error("embedding not configured (dim=0)")]
    EmbeddingNotConfigured,

    #[error("embedding failed: {message}")]
    EmbeddingFailed { message: String },

    #[error("document not found: {id}")]
    DocumentNotFound { id: String },

    #[error("config error: {0}")]
    Config(String),

    #[error("io error: {0}")]
    Io(#[from] std::io::Error),

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}
```

**Step 3: Verify compiles**

Run: `cd /home/opc/lex-vector/stj-vec && cargo check -p stj-vec-core`
Expected: PASS

**Step 4: Commit**

```bash
git add stj-vec/crates/core/src/types.rs stj-vec/crates/core/src/error.rs
git commit -m "feat(stj-vec): add types and error definitions"
```

---

### Task 3: Core -- config.rs

**Files:**
- Create: `stj-vec/crates/core/src/config.rs`

**Step 1: Write test**

```rust
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
        assert_eq!(config.server.port, 8421);
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd /home/opc/lex-vector/stj-vec && cargo test -p stj-vec-core test_parse_config`
Expected: FAIL (AppConfig not defined)

**Step 3: Write config.rs implementation**

```rust
use serde::Deserialize;
use std::path::Path;

#[derive(Debug, Deserialize)]
pub struct AppConfig {
    pub data: DataConfig,
    pub chunking: ChunkingConfig,
    pub embedding: EmbeddingConfig,
    pub server: ServerConfig,
}

#[derive(Debug, Deserialize)]
pub struct DataConfig {
    pub integras_dir: String,
    pub metadata_dir: String,
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

#[derive(Debug, Deserialize)]
pub struct ServerConfig {
    pub socket: String,
    pub port: u16,
    pub max_results: usize,
    pub default_threshold: f64,
}

impl AppConfig {
    pub fn load(path: &Path) -> anyhow::Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| anyhow::anyhow!("failed to read config {}: {}", path.display(), e))?;
        let config: Self = toml::from_str(&content)
            .map_err(|e| anyhow::anyhow!("failed to parse config: {}", e))?;
        Ok(config)
    }

    /// Returns true if embedding is configured (dim > 0 and provider set)
    pub fn embedding_enabled(&self) -> bool {
        self.embedding.dim > 0 && !self.embedding.provider.is_empty()
    }
}
```

**Step 4: Run test to verify it passes**

Run: `cd /home/opc/lex-vector/stj-vec && cargo test -p stj-vec-core test_parse_config`
Expected: PASS

**Step 5: Commit**

```bash
git add stj-vec/crates/core/src/config.rs
git commit -m "feat(stj-vec): add config deserialization"
```

---

### Task 4: Core -- storage.rs (schema + documents + chunks)

**Files:**
- Create: `stj-vec/crates/core/src/storage.rs`

**Step 1: Write tests**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::Document;

    #[test]
    fn test_open_and_stats() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();
        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 0);
        assert_eq!(stats.chunk_count, 0);
    }

    #[test]
    fn test_insert_document() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let doc = Document {
            id: "12345".into(),
            processo: Some("REsp 1234567".into()),
            classe: Some("RECURSO ESPECIAL".into()),
            ministro: Some("NANCY ANDRIGHI".into()),
            orgao_julgador: None,
            data_publicacao: Some("2024-03-15".into()),
            data_julgamento: None,
            assuntos: Some("11806".into()),
            teor: Some("Dando provimento".into()),
            tipo: Some("ACORDAO".into()),
            chunk_count: 0,
            source_file: Some("202403.zip".into()),
        };
        storage.insert_document(&doc).unwrap();

        let fetched = storage.get_document("12345").unwrap().unwrap();
        assert_eq!(fetched.processo.unwrap(), "REsp 1234567");
        assert_eq!(fetched.ministro.unwrap(), "NANCY ANDRIGHI");
    }

    #[test]
    fn test_insert_and_get_chunks() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        let chunks = vec![
            Chunk { id: "c1".into(), doc_id: "d1".into(), chunk_index: 0, content: "primeiro chunk".into(), token_count: 2 },
            Chunk { id: "c2".into(), doc_id: "d1".into(), chunk_index: 1, content: "segundo chunk".into(), token_count: 2 },
        ];
        storage.insert_chunks(&chunks).unwrap();

        let fetched = storage.get_chunks_by_doc("d1").unwrap();
        assert_eq!(fetched.len(), 2);
        assert_eq!(fetched[0].chunk_index, 0);
        assert_eq!(fetched[1].chunk_index, 1);
    }

    #[test]
    fn test_ingest_log() {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), 0).unwrap();

        storage.set_ingest_status("202203", "pending", 0, 0).unwrap();
        let status = storage.get_ingest_status("202203").unwrap().unwrap();
        assert_eq!(status.status, "pending");

        storage.set_ingest_status("202203", "chunked", 100, 500).unwrap();
        let status = storage.get_ingest_status("202203").unwrap().unwrap();
        assert_eq!(status.status, "chunked");
        assert_eq!(status.doc_count, 100);
    }
}
```

**Step 2: Run tests to verify they fail**

Run: `cd /home/opc/lex-vector/stj-vec && cargo test -p stj-vec-core`
Expected: FAIL (Storage not defined)

**Step 3: Write storage.rs implementation**

Full implementation following cogmem pattern: `Mutex<Connection>`, register_sqlite_vec, SCHEMA_SQL constant, all CRUD methods for documents, chunks, ingest_log. Stats query across all tables. No vec_chunks operations yet (dim=0 skips vec table creation).

Key: `Storage::open(path, dim)` -- if dim > 0, creates vec_chunks table with that dimension. If dim = 0, skips it entirely.

Add `tempfile = "3"` to core dev-dependencies for tests.

**Step 4: Run tests to verify they pass**

Run: `cd /home/opc/lex-vector/stj-vec && cargo test -p stj-vec-core`
Expected: all PASS

**Step 5: Commit**

```bash
git add stj-vec/crates/core/src/storage.rs stj-vec/crates/core/Cargo.toml
git commit -m "feat(stj-vec): add storage layer with documents, chunks, ingest_log"
```

---

### Task 5: Core -- chunker.rs

**Files:**
- Create: `stj-vec/crates/core/src/chunker.rs`

**Step 1: Write tests**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_strip_html() {
        let input = "Texto com<br>quebra e &nbsp; espaco";
        let clean = strip_html(input);
        assert_eq!(clean, "Texto com\nquebra e   espaco");
    }

    #[test]
    fn test_chunk_short_text() {
        let config = ChunkingConfig { max_tokens: 512, overlap_tokens: 64, min_chunk_tokens: 10 };
        let result = chunk_legal_text("Texto curto de teste.", "doc1", &config);
        assert_eq!(result.chunks.len(), 1);
        assert_eq!(result.doc_id, "doc1");
    }

    #[test]
    fn test_chunk_long_text() {
        let config = ChunkingConfig { max_tokens: 20, overlap_tokens: 5, min_chunk_tokens: 5 };
        // ~100 words
        let text = "A responsabilidade civil. ".repeat(100);
        let result = chunk_legal_text(&text, "doc2", &config);
        assert!(result.chunks.len() > 1, "should produce multiple chunks");
        // Verify indices are sequential
        for (i, chunk) in result.chunks.iter().enumerate() {
            assert_eq!(chunk.chunk_index, i);
        }
    }

    #[test]
    fn test_chunk_real_stj_format() {
        let text = "DECISÃO<br>Trata-se de agravo interposto por FULANO contra a decisão que inadmitiu recurso especial.<br>Nas razões do presente recurso, o agravante argumentou que inaplicáveis os óbices.<br>É o relatório.<br>DECIDO.<br>A irresignação não merece prosperar.";
        let config = ChunkingConfig { max_tokens: 512, overlap_tokens: 64, min_chunk_tokens: 10 };
        let result = chunk_legal_text(text, "109122800", &config);
        assert_eq!(result.chunks.len(), 1); // short enough for 1 chunk
        assert!(!result.chunks[0].content.contains("<br>"), "HTML should be stripped");
        assert!(result.chunks[0].content.contains("DECISÃO"), "content preserved");
    }
}
```

**Step 2: Run tests, verify fail**

Run: `cd /home/opc/lex-vector/stj-vec && cargo test -p stj-vec-core chunker`
Expected: FAIL

**Step 3: Implement chunker.rs**

Key functions:
- `strip_html(text) -> String` -- remove `<br>`, `<br/>`, `&nbsp;`, `&amp;` etc
- `estimate_tokens(text) -> usize` -- chars/4 approximation (good enough for chunking)
- `chunk_legal_text(text, doc_id, config) -> ChunkOutput` -- split on paragraph boundaries (double newline), merge paragraphs into chunks up to max_tokens, overlap by including last N tokens of previous chunk
- Chunk ID: `md5(doc_id + chunk_index)` (deterministic, dedup-safe)

**Step 4: Run tests, verify pass**

Run: `cd /home/opc/lex-vector/stj-vec && cargo test -p stj-vec-core chunker`
Expected: PASS

**Step 5: Commit**

```bash
git add stj-vec/crates/core/src/chunker.rs
git commit -m "feat(stj-vec): add legal text chunker with HTML cleanup"
```

---

### Task 6: Core -- embedder.rs (trait + NoopEmbedder)

**Files:**
- Create: `stj-vec/crates/core/src/embedder.rs`

**Step 1: Write embedder trait and Noop implementation**

```rust
use anyhow::Result;
use async_trait::async_trait;

/// Trait para providers de embedding.
/// Implementacoes concretas: NoopEmbedder (placeholder), futuro ModalEmbedder, OllamaEmbedder.
#[async_trait]
pub trait Embedder: Send + Sync {
    async fn embed(&self, text: &str) -> Result<Vec<f32>>;
    async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>>;
    fn dim(&self) -> usize;
    fn model_name(&self) -> &str;
}

/// Placeholder -- retorna erro informando que embedding nao esta configurado.
/// Usado quando config.embedding.dim == 0.
pub struct NoopEmbedder;

#[async_trait]
impl Embedder for NoopEmbedder {
    async fn embed(&self, _text: &str) -> Result<Vec<f32>> {
        anyhow::bail!("embedding not configured (dim=0, provider empty)")
    }

    async fn embed_batch(&self, _texts: &[String]) -> Result<Vec<Vec<f32>>> {
        anyhow::bail!("embedding not configured (dim=0, provider empty)")
    }

    fn dim(&self) -> usize { 0 }
    fn model_name(&self) -> &str { "noop" }
}

// PLACEHOLDER: ModalEmbedder e OllamaEmbedder serao adicionados quando Modal estiver configurado
```

**Step 2: Verify compiles**

Run: `cd /home/opc/lex-vector/stj-vec && cargo check -p stj-vec-core`
Expected: PASS

**Step 3: Commit**

```bash
git add stj-vec/crates/core/src/embedder.rs
git commit -m "feat(stj-vec): add embedder trait with noop placeholder"
```

---

### Task 7: Ingest -- scanner.rs

**Files:**
- Create: `stj-vec/crates/ingest/src/scanner.rs`

**Step 1: Write tests**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::tempdir;

    #[test]
    fn test_scan_finds_subdirs() {
        let dir = tempdir().unwrap();
        // Simulate integras structure
        fs::create_dir_all(dir.path().join("202203")).unwrap();
        fs::write(dir.path().join("202203/12345.txt"), "content").unwrap();
        fs::create_dir_all(dir.path().join("20220502")).unwrap();
        fs::write(dir.path().join("20220502/67890.txt"), "content").unwrap();

        let sources = scan_integras_dir(dir.path()).unwrap();
        assert_eq!(sources.len(), 2);
    }

    #[test]
    fn test_scan_counts_files() {
        let dir = tempdir().unwrap();
        fs::create_dir_all(dir.path().join("202203")).unwrap();
        for i in 0..5 {
            fs::write(dir.path().join(format!("202203/{}.txt", i)), "content").unwrap();
        }

        let sources = scan_integras_dir(dir.path()).unwrap();
        assert_eq!(sources[0].file_count, 5);
    }
}
```

**Step 2: Implement scanner.rs**

Scan `/integras/textos/` directory. Each subdirectory (YYYYMM or YYYYMMDD) is one "source". Returns `Vec<SourceDir>` with path, name, file_count. Cross-references with `ingest_log` to find new sources.

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git commit -m "feat(stj-vec): add integras directory scanner"
```

---

### Task 8: Ingest -- pipeline.rs (scan + chunk phases)

**Files:**
- Create: `stj-vec/crates/ingest/src/pipeline.rs`
- Create: `stj-vec/crates/ingest/src/progress.rs`

**Step 1: Implement Pipeline struct**

Pipeline orchestrates:
1. `scan()` -- call scanner, register new sources in ingest_log as "pending"
2. `chunk_pending()` -- for each "pending" source: read TXT files, strip HTML, chunk, insert chunks + documents into storage, mark "chunked"
3. `embed_pending()` -- PLACEHOLDER: log "embedding not configured, skipping"
4. `stats()` -- print ingest_log summary with indicatif

Key: read corresponding metadata JSON (`metadata/metadados{source_name}.json`) to populate documents table. If metadata JSON not found, insert document with only id and source_file.

**Step 2: Write integration test with real data sample**

```rust
#[tokio::test]
async fn test_pipeline_chunk_single_source() {
    // Create temp dir with 3 fake TXT files
    // Run scan + chunk_pending
    // Verify: documents table has 3 entries, chunks table has entries, ingest_log status = "chunked"
}
```

**Step 3: Run tests, verify pass**

**Step 4: Commit**

```bash
git commit -m "feat(stj-vec): add ingestion pipeline with scan and chunk phases"
```

---

### Task 9: Ingest -- main.rs (CLI with clap)

**Files:**
- Modify: `stj-vec/crates/ingest/src/main.rs`

**Step 1: Implement clap CLI**

```rust
#[derive(Parser)]
#[command(name = "stj-vec-ingest", version, about = "STJ vector ingestion pipeline")]
struct Cli {
    #[arg(short, long, default_value = "config.toml")]
    config: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Scan integras dir for new sources
    Scan,
    /// Chunk pending sources
    Chunk,
    /// Generate embeddings (PLACEHOLDER)
    Embed,
    /// Run full pipeline: scan + chunk + embed
    Full,
    /// Show ingest stats
    Stats,
    /// Reset a source for reprocessing
    Reset { source: String },
}
```

**Step 2: Wire subcommands to pipeline methods**

**Step 3: Test manually with real data**

Run: `cd /home/opc/lex-vector/stj-vec && cargo run -p stj-vec-ingest -- --config config.toml scan`
Expected: lists sources found in integras/textos/

Run: `cd /home/opc/lex-vector/stj-vec && cargo run -p stj-vec-ingest -- --config config.toml stats`
Expected: shows ingest_log summary

**Step 4: Commit**

```bash
git commit -m "feat(stj-vec): add ingest CLI with subcommands"
```

---

### Task 10: Server -- routes.rs e context.rs

**Files:**
- Create: `stj-vec/crates/server/src/routes.rs`
- Create: `stj-vec/crates/server/src/context.rs`

**Step 1: Implement AppState**

```rust
pub struct AppState {
    pub storage: Arc<Storage>,
    pub embedder: Arc<dyn Embedder>,
    pub config: ServerConfig,
}
```

**Step 2: Implement routes**

- `GET /health` -- `{"status": "ok"}`
- `GET /stats` -- delegates to storage.stats()
- `GET /doc/:id` -- delegates to storage.get_document()
- `GET /doc/:id/chunks` -- delegates to storage.get_chunks_by_doc()
- `POST /search` -- embed query, search storage, join documents. If embedding not configured, return error.

**Step 3: Write test for /health and /stats routes**

Use `axum::test::TestClient` or direct handler calls.

**Step 4: Commit**

```bash
git commit -m "feat(stj-vec): add server routes and app state"
```

---

### Task 11: Server -- main.rs (socket + HTTP daemon)

**Files:**
- Modify: `stj-vec/crates/server/src/main.rs`

**Step 1: Implement daemon**

- Parse args with clap (--config, --port, --socket, --db-path)
- Load config
- Open storage readonly
- Create embedder from config (NoopEmbedder if dim=0)
- Build axum router with routes
- Spawn HTTP listener on port
- Spawn Unix socket listener (same protocol as cogmem: JSON line in, JSON line out)
- Graceful shutdown via CancellationToken + ctrl_c signal

**Step 2: Test manually**

Run: `cd /home/opc/lex-vector/stj-vec && cargo run -p stj-vec-server -- --config config.toml`
Then: `curl http://localhost:8421/health`
Expected: `{"status":"ok"}`

Then: `echo '{"action":"ping"}' | nc -U /tmp/stj-vec.sock`
Expected: `{"status":"ok"}`

**Step 3: Commit**

```bash
git commit -m "feat(stj-vec): add server daemon with socket + HTTP"
```

---

### Task 12: Smoke test com dados reais (scan + chunk de 1 source)

**Files:** none (manual test)

**Step 1: Run scan**

```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-ingest -- --config config.toml scan
```

Expected: lists 857 sources

**Step 2: Chunk 1 source only**

Temporarily modify pipeline to process only first pending source, or add `--limit 1` flag.

```bash
cargo run --release -p stj-vec-ingest -- --config config.toml chunk
```

Expected: processes 1 source (e.g. 202203 with ~59k files), creates documents + chunks, marks "chunked" in ingest_log.

**Step 3: Verify via server**

```bash
cargo run -p stj-vec-server -- --config config.toml &
curl http://localhost:8421/stats
```

Expected: document_count > 0, chunk_count > 0, embedding_count = 0

**Step 4: Test doc retrieval**

```bash
curl http://localhost:8421/doc/109122800
```

Expected: returns document metadata

**Step 5: Commit if any fixes were needed**

```bash
git commit -m "fix(stj-vec): adjustments from smoke test with real data"
```

---

### Task 13: Skill /stj-search

**Files:**
- Create: `~/.claude/skills/stj-search/SKILL.md`

**Step 1: Write skill**

Same imperative pattern as `/mem-search`:

```markdown
---
name: stj-search
description: Buscar na base vetorial de jurisprudencia do STJ...
---

## Execucao OBRIGATORIA

echo '{"action":"search","query":"TERMOS","limit":10}' | nc -U /tmp/stj-vec.sock
```

**Step 2: Commit**

```bash
git commit -m "feat(stj-vec): add /stj-search skill for Claude Code"
```

---

## Ordem de Execucao

| Task | Depende de | Estimativa |
|------|-----------|------------|
| 1. Scaffold | - | 10min |
| 2. types + error | 1 | 10min |
| 3. config | 1 | 10min |
| 4. storage | 2, 3 | 30min |
| 5. chunker | 2 | 20min |
| 6. embedder trait | 2 | 5min |
| 7. scanner | 2 | 15min |
| 8. pipeline | 4, 5, 6, 7 | 30min |
| 9. ingest CLI | 8 | 15min |
| 10. server routes | 4, 6 | 20min |
| 11. server daemon | 10 | 20min |
| 12. smoke test | 9, 11 | 15min |
| 13. skill | 11 | 5min |

**Total estimado: ~3.5 horas**

**Paralelizavel:** Tasks 5, 6, 7 podem rodar em paralelo. Tasks 10-11 podem rodar em paralelo com 7-9.

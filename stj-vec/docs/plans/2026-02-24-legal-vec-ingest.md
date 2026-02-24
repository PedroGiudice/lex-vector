# legal-vec-ingest Implementation Plan

> **For Claude — EXECUTION PROTOCOL:**
> 1. Invoke `Skill(skill="superpowers:executing-plans")` para carregar o protocolo de execucao task-by-task.
> 2. Invoke `Skill(skill="superpowers:subagent-driven-development")` para despachar subagentes por task com review entre eles.
> 3. Cada subagente recebe UMA task completa (com codigo) e executa com `isolation: "worktree"`.
> 4. Apos cada task, review do resultado antes de despachar a proxima.
> 5. Invoke `Skill(skill="superpowers:verification-before-completion")` antes de declarar o plano concluido.

**Goal:** Novo crate `legal-vec-ingest` que ingere o corpus legal (CF, acordaos TCU, decretos TESEMO) em banco sqlite-vec proprio, independente do stj-vec.

**Architecture:** Crate standalone em `crates/legal-ingest/` no workspace stj-vec. Storage, embedder, chunker, scanner e types proprios -- replica a logica do stj-vec-ingest mas com schema para documentos legais. Banco em `db/legal-vec.db`. Embedding via Ollama (bge-m3, 1024d). CLI com clap: scan, chunk, embed, full, stats.

**Tech Stack:** Rust 2021, tokio, rusqlite + sqlite-vec, reqwest (Ollama), clap v4, serde, tracing, indicatif.

---

## Corpus (dados reais verificados)

| Fonte | Dir | Docs | Avg texto | Max texto | Schema |
|-------|-----|------|-----------|-----------|--------|
| abjur/CF | `corpus/abjur/constituicao_federal.json` | 368 | 1052 chars | 13338 chars | `{id, tipo, titulo, texto, fonte, url, data_publicacao, metadata: {artigo, titulo, source_file}}` |
| HF/TCU | `corpus/huggingface/tcu_batch_*.json` (10) | 5000 | 2887 chars | 32045 chars | `{id, tipo, titulo, texto, fonte, url, data_publicacao, metadata: {subset, original_source}}` |
| HF/TESEMO | `corpus/huggingface/tesemo_batch_*.json` (20) | 10000 | 11631 chars | 32045 chars | mesmo schema |
| **Total** | | **15368** | | | |

Todas as fontes tem schema identico: `{id, tipo, titulo, texto, fonte, url, data_publicacao, metadata}`.

---

## Task 1: Scaffold do crate e types

**Files:**
- Create: `crates/legal-ingest/Cargo.toml`
- Create: `crates/legal-ingest/src/lib.rs`
- Create: `crates/legal-ingest/src/types.rs`
- Create: `crates/legal-ingest/src/error.rs`
- Modify: `Cargo.toml` (workspace members)

**Step 1: Adicionar membro ao workspace**

Em `Cargo.toml` do workspace, `members = ["crates/*"]` ja cobre. Nada a mudar.

Criar `crates/legal-ingest/Cargo.toml`:

```toml
[package]
name = "legal-vec-ingest"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "legal-vec-ingest"
path = "src/main.rs"

[dependencies]
tokio = { workspace = true }
serde = { workspace = true }
serde_json = { workspace = true }
anyhow = { workspace = true }
thiserror = { workspace = true }
clap = { workspace = true }
rusqlite = { workspace = true }
sqlite-vec = { workspace = true }
zerocopy = { workspace = true }
tracing = { workspace = true }
tracing-subscriber = { workspace = true }
indicatif = { workspace = true }
reqwest = { workspace = true }
md5 = { workspace = true }
toml = { workspace = true }
uuid = { workspace = true }
chrono = { workspace = true }

[dev-dependencies]
tempfile = "3"
```

**Step 2: Criar types.rs**

```rust
use serde::{Deserialize, Serialize};

/// Documento legal do corpus (CF, acordaos TCU, decretos TESEMO)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LegalDocument {
    pub id: String,
    pub tipo: String,
    pub titulo: String,
    pub texto: String,
    pub fonte: String,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub data_publicacao: Option<String>,
    #[serde(default)]
    pub metadata: serde_json::Value,
}

/// Chunk de texto legal
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LegalChunk {
    pub id: String,
    pub doc_id: String,
    pub chunk_index: i32,
    pub content: String,
    pub token_count: i32,
}

/// Fonte detectada pelo scanner
#[derive(Debug, Clone)]
pub struct CorpusSource {
    pub name: String,
    pub source_type: SourceType,
    pub files: Vec<std::path::PathBuf>,
    pub doc_count: usize,
}

/// Tipo de fonte no corpus
#[derive(Debug, Clone, PartialEq)]
pub enum SourceType {
    /// Artigos da CF (abjur)
    Constituicao,
    /// Acordaos TCU (huggingface)
    AcordaoTcu,
    /// Decretos/tratados TESEMO (huggingface)
    DecretoTesemo,
}

/// Estatisticas do banco
#[derive(Debug, Serialize)]
pub struct DbStats {
    pub document_count: i64,
    pub chunk_count: i64,
    pub embedding_count: i64,
    pub sources: Vec<SourceStats>,
}

#[derive(Debug, Serialize)]
pub struct SourceStats {
    pub source: String,
    pub status: String,
    pub doc_count: i32,
    pub chunk_count: i32,
}
```

**Step 3: Criar error.rs**

```rust
use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
pub enum LegalVecError {
    #[error("storage error: {0}")]
    Storage(#[from] rusqlite::Error),

    #[error("embedding failed: {message}")]
    EmbeddingFailed { message: String },

    #[error("corpus not found: {path}")]
    CorpusNotFound { path: PathBuf },

    #[error("config error: {0}")]
    Config(String),

    #[error("io error at {path}")]
    Io { path: PathBuf, #[source] source: std::io::Error },

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}
```

**Step 4: Criar lib.rs**

```rust
pub mod config;
pub mod chunker;
pub mod embedder;
pub mod error;
pub mod pipeline;
pub mod scanner;
pub mod storage;
pub mod types;
```

**Step 5: Criar main.rs placeholder**

```rust
fn main() {
    println!("legal-vec-ingest: placeholder");
}
```

**Step 6: Verificar compilacao**

Run: `cargo build -p legal-vec-ingest`
Expected: compila (modulos declarados mas vazios dara erros -- criar stubs vazios para cada)

**Step 7: Commit**

```bash
git add crates/legal-ingest/
git commit -m "feat(legal-vec): scaffold crate with types and error"
```

---

## Task 2: Config

**Files:**
- Create: `crates/legal-ingest/src/config.rs`
- Create: `legal-vec.toml`

**Step 1: Criar config.rs**

```rust
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
```

**Step 2: Criar legal-vec.toml**

```toml
[data]
corpus_dir = "/home/opc/.claude/legal-knowledge-base/corpus"
db_path = "db/legal-vec.db"

[chunking]
max_tokens = 512
overlap_tokens = 64
min_chunk_tokens = 50

[embedding]
model = "bge-m3"
dim = 1024
provider = "ollama"

[embedding.ollama]
url = "http://100.114.203.28:11434/api/embeddings"
model = "bge-m3"
timeout_secs = 10
```

**Step 3: Teste unitario de parse**

Adicionar ao config.rs:

```rust
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
```

**Step 4: Rodar teste**

Run: `cargo test -p legal-vec-ingest config::tests`
Expected: PASS

**Step 5: Commit**

```bash
git add crates/legal-ingest/src/config.rs legal-vec.toml
git commit -m "feat(legal-vec): add config with TOML parsing"
```

---

## Task 3: Scanner

**Files:**
- Create: `crates/legal-ingest/src/scanner.rs`

O scanner detecta fontes no corpus_dir. Logica:
- `abjur/constituicao_federal.json` -> SourceType::Constituicao
- `huggingface/tcu_batch_*.json` -> SourceType::AcordaoTcu
- `huggingface/tesemo_batch_*.json` -> SourceType::DecretoTesemo

**Step 1: Implementar scanner**

```rust
use crate::types::{CorpusSource, LegalDocument, SourceType};
use anyhow::{Context, Result};
use std::path::Path;
use tracing::info;

/// Escaneia corpus_dir e retorna fontes detectadas
pub fn scan_corpus(corpus_dir: &Path) -> Result<Vec<CorpusSource>> {
    let mut sources = Vec::new();

    // abjur/
    let abjur_dir = corpus_dir.join("abjur");
    if abjur_dir.exists() {
        let cf_path = abjur_dir.join("constituicao_federal.json");
        if cf_path.exists() {
            let docs = load_json_array(&cf_path)?;
            sources.push(CorpusSource {
                name: "abjur/constituicao_federal".into(),
                source_type: SourceType::Constituicao,
                files: vec![cf_path],
                doc_count: docs,
            });
        }
    }

    // huggingface/
    let hf_dir = corpus_dir.join("huggingface");
    if hf_dir.exists() {
        // TCU batches
        let mut tcu_files = Vec::new();
        let mut tcu_count = 0;
        for entry in std::fs::read_dir(&hf_dir)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if name.starts_with("tcu_batch_") && name.ends_with(".json") {
                let count = load_json_array(&entry.path())?;
                tcu_count += count;
                tcu_files.push(entry.path());
            }
        }
        tcu_files.sort();
        if !tcu_files.is_empty() {
            sources.push(CorpusSource {
                name: "huggingface/tcu".into(),
                source_type: SourceType::AcordaoTcu,
                files: tcu_files,
                doc_count: tcu_count,
            });
        }

        // TESEMO batches
        let mut tesemo_files = Vec::new();
        let mut tesemo_count = 0;
        for entry in std::fs::read_dir(&hf_dir)? {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if name.starts_with("tesemo_batch_") && name.ends_with(".json") {
                let count = load_json_array(&entry.path())?;
                tesemo_count += count;
                tesemo_files.push(entry.path());
            }
        }
        tesemo_files.sort();
        if !tesemo_files.is_empty() {
            sources.push(CorpusSource {
                name: "huggingface/tesemo".into(),
                source_type: SourceType::DecretoTesemo,
                files: tesemo_files,
                doc_count: tesemo_count,
            });
        }
    }

    for s in &sources {
        info!(
            source = %s.name,
            files = s.files.len(),
            docs = s.doc_count,
            "detected corpus source"
        );
    }

    Ok(sources)
}

/// Conta docs num JSON array sem carregar todos na memoria
fn load_json_array(path: &Path) -> Result<usize> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;
    let arr: Vec<serde_json::Value> = serde_json::from_str(&content)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    Ok(arr.len())
}

/// Carrega documentos de um arquivo JSON
pub fn load_documents(path: &Path) -> Result<Vec<LegalDocument>> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read {}", path.display()))?;
    let docs: Vec<LegalDocument> = serde_json::from_str(&content)
        .with_context(|| format!("failed to parse {}", path.display()))?;
    Ok(docs)
}
```

**Step 2: Teste com corpus real (read-only)**

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    #[test]
    fn test_scan_real_corpus() {
        let corpus = PathBuf::from("/home/opc/.claude/legal-knowledge-base/corpus");
        if !corpus.exists() {
            return; // skip if corpus not available
        }
        let sources = scan_corpus(&corpus).unwrap();
        assert_eq!(sources.len(), 3);

        let cf = sources.iter().find(|s| s.source_type == SourceType::Constituicao).unwrap();
        assert_eq!(cf.doc_count, 368);

        let tcu = sources.iter().find(|s| s.source_type == SourceType::AcordaoTcu).unwrap();
        assert_eq!(tcu.doc_count, 5000);
        assert_eq!(tcu.files.len(), 10);

        let tesemo = sources.iter().find(|s| s.source_type == SourceType::DecretoTesemo).unwrap();
        assert_eq!(tesemo.doc_count, 10000);
        assert_eq!(tesemo.files.len(), 20);
    }

    #[test]
    fn test_load_cf_documents() {
        let path = PathBuf::from("/home/opc/.claude/legal-knowledge-base/corpus/abjur/constituicao_federal.json");
        if !path.exists() { return; }
        let docs = load_documents(&path).unwrap();
        assert_eq!(docs.len(), 368);
        assert_eq!(docs[0].id, "cf_art_1");
        assert_eq!(docs[0].tipo, "constituicao");
        assert!(!docs[0].texto.is_empty());
    }
}
```

**Step 3: Rodar testes**

Run: `cargo test -p legal-vec-ingest scanner::tests`
Expected: PASS

**Step 4: Commit**

```bash
git add crates/legal-ingest/src/scanner.rs
git commit -m "feat(legal-vec): scanner detects 3 corpus sources"
```

---

## Task 4: Storage (sqlite-vec)

**Files:**
- Create: `crates/legal-ingest/src/storage.rs`

Replica logica do core/storage.rs mas com schema para LegalDocument/LegalChunk.

**Step 1: Implementar storage**

```rust
use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use std::path::Path;
use std::sync::Mutex;
use zerocopy::AsBytes;

use crate::types::{DbStats, LegalChunk, LegalDocument, SourceStats};

const SCHEMA_SQL: &str = r#"
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    titulo TEXT,
    texto TEXT,
    fonte TEXT,
    url TEXT,
    data_publicacao TEXT,
    metadata TEXT,
    source_name TEXT
);

CREATE INDEX IF NOT EXISTS idx_docs_tipo ON documents(tipo);
CREATE INDEX IF NOT EXISTS idx_docs_fonte ON documents(fonte);
CREATE INDEX IF NOT EXISTS idx_docs_source ON documents(source_name);

CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

CREATE TABLE IF NOT EXISTS ingest_log (
    source_name TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    doc_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    error TEXT
);
"#;

pub struct Storage {
    conn: Mutex<Connection>,
    embedding_dim: usize,
}

fn register_sqlite_vec() {
    unsafe {
        rusqlite::ffi::sqlite3_auto_extension(Some(std::mem::transmute(
            sqlite_vec::sqlite3_vec_init as *const (),
        )));
    }
}

impl Storage {
    pub fn open(path: &str, embedding_dim: usize) -> Result<Self> {
        register_sqlite_vec();

        if let Some(parent) = Path::new(path).parent() {
            std::fs::create_dir_all(parent).ok();
        }

        let conn = Connection::open(path)
            .with_context(|| format!("falha ao abrir SQLite em {}", path))?;

        conn.execute_batch(SCHEMA_SQL)
            .context("falha ao aplicar schema")?;

        if embedding_dim > 0 {
            let vec_sql = format!(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
                    chunk_id TEXT PRIMARY KEY,
                    embedding float[{}] distance_metric=cosine
                )",
                embedding_dim
            );
            conn.execute_batch(&vec_sql)
                .context("falha ao criar vec_chunks")?;
        }

        Ok(Self {
            conn: Mutex::new(conn),
            embedding_dim,
        })
    }

    fn lock(&self) -> Result<std::sync::MutexGuard<'_, Connection>> {
        self.conn
            .lock()
            .map_err(|e| anyhow::anyhow!("mutex poisoned: {}", e))
    }

    // === Documents ===

    pub fn insert_document(&self, doc: &LegalDocument, source_name: &str) -> Result<()> {
        let conn = self.lock()?;
        conn.execute(
            "INSERT OR REPLACE INTO documents (id, tipo, titulo, texto, fonte, url, data_publicacao, metadata, source_name)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                doc.id, doc.tipo, doc.titulo, doc.texto, doc.fonte,
                doc.url, doc.data_publicacao,
                serde_json::to_string(&doc.metadata).unwrap_or_default(),
                source_name,
            ],
        )?;
        Ok(())
    }

    pub fn insert_documents_batch(&self, docs: &[LegalDocument], source_name: &str) -> Result<()> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "INSERT OR REPLACE INTO documents (id, tipo, titulo, texto, fonte, url, data_publicacao, metadata, source_name)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
        )?;
        for doc in docs {
            stmt.execute(params![
                doc.id, doc.tipo, doc.titulo, doc.texto, doc.fonte,
                doc.url, doc.data_publicacao,
                serde_json::to_string(&doc.metadata).unwrap_or_default(),
                source_name,
            ])?;
        }
        Ok(())
    }

    // === Chunks ===

    pub fn insert_chunks(&self, chunks: &[LegalChunk]) -> Result<()> {
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "INSERT OR IGNORE INTO chunks (id, doc_id, chunk_index, content, token_count)
             VALUES (?1, ?2, ?3, ?4, ?5)",
        )?;
        for chunk in chunks {
            stmt.execute(params![
                chunk.id, chunk.doc_id, chunk.chunk_index, chunk.content, chunk.token_count,
            ])?;
        }
        Ok(())
    }

    // === Embeddings ===

    pub fn insert_embedding(&self, chunk_id: &str, embedding: &[f32]) -> Result<()> {
        if self.embedding_dim == 0 {
            anyhow::bail!("embedding not configured (dim=0)");
        }
        let conn = self.lock()?;
        conn.execute(
            "INSERT OR REPLACE INTO vec_chunks (chunk_id, embedding) VALUES (?1, ?2)",
            params![chunk_id, embedding.as_bytes()],
        )?;
        Ok(())
    }

    pub fn insert_embeddings_batch(&self, pairs: &[(String, Vec<f32>)]) -> Result<()> {
        if self.embedding_dim == 0 {
            anyhow::bail!("embedding not configured (dim=0)");
        }
        let conn = self.lock()?;
        let mut stmt = conn.prepare(
            "INSERT OR REPLACE INTO vec_chunks (chunk_id, embedding) VALUES (?1, ?2)",
        )?;
        for (chunk_id, embedding) in pairs {
            stmt.execute(params![chunk_id, embedding.as_bytes()])?;
        }
        Ok(())
    }

    /// Retorna chunk_ids que ja tem embedding
    pub fn chunks_with_embeddings(&self) -> Result<Vec<String>> {
        if self.embedding_dim == 0 {
            return Ok(Vec::new());
        }
        let conn = self.lock()?;
        let mut stmt = conn.prepare("SELECT chunk_id FROM vec_chunks")?;
        let ids = stmt
            .query_map([], |row| row.get::<_, String>(0))?
            .filter_map(|r| r.ok())
            .collect();
        Ok(ids)
    }

    /// Retorna todos os chunks sem embedding
    pub fn chunks_without_embeddings(&self) -> Result<Vec<LegalChunk>> {
        let conn = self.lock()?;
        let sql = if self.embedding_dim > 0 {
            "SELECT c.id, c.doc_id, c.chunk_index, c.content, c.token_count
             FROM chunks c
             LEFT JOIN vec_chunks v ON v.chunk_id = c.id
             WHERE v.chunk_id IS NULL
             ORDER BY c.id"
        } else {
            "SELECT id, doc_id, chunk_index, content, token_count FROM chunks ORDER BY id"
        };
        let mut stmt = conn.prepare(sql)?;
        let chunks = stmt
            .query_map([], |row| {
                Ok(LegalChunk {
                    id: row.get(0)?,
                    doc_id: row.get(1)?,
                    chunk_index: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    content: row.get(3)?,
                    token_count: row.get::<_, Option<i32>>(4)?.unwrap_or(0),
                })
            })?
            .filter_map(|r| r.ok())
            .collect();
        Ok(chunks)
    }

    // === Ingest Log ===

    pub fn set_ingest_status(&self, source: &str, status: &str, doc_count: i32, chunk_count: i32) -> Result<()> {
        let conn = self.lock()?;
        conn.execute(
            "INSERT INTO ingest_log (source_name, status, doc_count, chunk_count)
             VALUES (?1, ?2, ?3, ?4)
             ON CONFLICT(source_name) DO UPDATE SET
             status = ?2, doc_count = ?3, chunk_count = ?4,
             completed_at = CASE WHEN ?2 = 'done' THEN datetime('now') ELSE completed_at END",
            params![source, status, doc_count, chunk_count],
        )?;
        Ok(())
    }

    pub fn get_ingest_status(&self, source: &str) -> Result<Option<String>> {
        let conn = self.lock()?;
        let result = conn.query_row(
            "SELECT status FROM ingest_log WHERE source_name = ?",
            params![source],
            |row| row.get::<_, String>(0),
        );
        match result {
            Ok(s) => Ok(Some(s)),
            Err(rusqlite::Error::QueryReturnedNoRows) => Ok(None),
            Err(e) => Err(e.into()),
        }
    }

    // === Stats ===

    pub fn stats(&self) -> Result<DbStats> {
        let conn = self.lock()?;

        let document_count: i64 = conn.query_row("SELECT COUNT(*) FROM documents", [], |row| row.get(0))?;
        let chunk_count: i64 = conn.query_row("SELECT COUNT(*) FROM chunks", [], |row| row.get(0))?;
        let embedding_count: i64 = if self.embedding_dim > 0 {
            conn.query_row("SELECT COUNT(*) FROM vec_chunks", [], |row| row.get(0)).unwrap_or(0)
        } else {
            0
        };

        let mut stmt = conn.prepare(
            "SELECT source_name, status, doc_count, chunk_count FROM ingest_log ORDER BY source_name"
        )?;
        let sources = stmt
            .query_map([], |row| {
                Ok(SourceStats {
                    source: row.get(0)?,
                    status: row.get(1)?,
                    doc_count: row.get::<_, Option<i32>>(2)?.unwrap_or(0),
                    chunk_count: row.get::<_, Option<i32>>(3)?.unwrap_or(0),
                })
            })?
            .filter_map(|r| r.ok())
            .collect();

        Ok(DbStats { document_count, chunk_count, embedding_count, sources })
    }
}
```

**Step 2: Testes unitarios**

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn tmp_storage(dim: usize) -> (tempfile::TempDir, Storage) {
        let dir = tempfile::tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        let storage = Storage::open(db_path.to_str().unwrap(), dim).unwrap();
        (dir, storage)
    }

    #[test]
    fn test_open_and_stats() {
        let (_dir, storage) = tmp_storage(0);
        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 0);
        assert_eq!(stats.chunk_count, 0);
    }

    #[test]
    fn test_insert_document_and_chunks() {
        let (_dir, storage) = tmp_storage(0);
        let doc = LegalDocument {
            id: "cf_art_1".into(), tipo: "constituicao".into(),
            titulo: "Art. 1".into(), texto: "Texto...".into(),
            fonte: "abjur".into(), url: None, data_publicacao: None,
            metadata: serde_json::json!({}),
        };
        storage.insert_document(&doc, "abjur/cf").unwrap();

        let chunks = vec![
            LegalChunk { id: "c1".into(), doc_id: "cf_art_1".into(), chunk_index: 0, content: "chunk text".into(), token_count: 10 },
        ];
        storage.insert_chunks(&chunks).unwrap();

        let stats = storage.stats().unwrap();
        assert_eq!(stats.document_count, 1);
        assert_eq!(stats.chunk_count, 1);
    }

    #[test]
    fn test_embedding_with_dim() {
        let (_dir, storage) = tmp_storage(4);
        let chunks = vec![
            LegalChunk { id: "c1".into(), doc_id: "d1".into(), chunk_index: 0, content: "text".into(), token_count: 1 },
        ];
        storage.insert_chunks(&chunks).unwrap();
        storage.insert_embedding("c1", &[0.1, 0.2, 0.3, 0.4]).unwrap();
        let stats = storage.stats().unwrap();
        assert_eq!(stats.embedding_count, 1);
    }

    #[test]
    fn test_ingest_log() {
        let (_dir, storage) = tmp_storage(0);
        storage.set_ingest_status("abjur/cf", "pending", 0, 0).unwrap();
        assert_eq!(storage.get_ingest_status("abjur/cf").unwrap(), Some("pending".into()));
        storage.set_ingest_status("abjur/cf", "chunked", 368, 368).unwrap();
        assert_eq!(storage.get_ingest_status("abjur/cf").unwrap(), Some("chunked".into()));
    }
}
```

**Step 3: Rodar testes**

Run: `cargo test -p legal-vec-ingest storage::tests`
Expected: PASS

**Step 4: Commit**

```bash
git add crates/legal-ingest/src/storage.rs
git commit -m "feat(legal-vec): storage with sqlite-vec for legal documents"
```

---

## Task 5: Chunker

**Files:**
- Create: `crates/legal-ingest/src/chunker.rs`

Logica de chunking:
- CF (Constituicao): cada artigo ja e um chunk (texto curto, avg 1052 chars)
- TCU/TESEMO (textos longos): chunking por paragrafo com overlap (mesma logica do core)

**Step 1: Implementar chunker**

```rust
use crate::config::ChunkingConfig;
use crate::types::{LegalChunk, LegalDocument, SourceType};

/// Estimativa de tokens: chars / 4
pub fn estimate_tokens(text: &str) -> usize {
    text.len() / 4
}

/// Chunkeia documento legal conforme o tipo da fonte
pub fn chunk_document(doc: &LegalDocument, source_type: &SourceType, config: &ChunkingConfig) -> Vec<LegalChunk> {
    match source_type {
        SourceType::Constituicao => chunk_by_article(doc),
        SourceType::AcordaoTcu | SourceType::DecretoTesemo => chunk_by_paragraph(doc, config),
    }
}

/// CF: cada artigo e um chunk unico (texto ja e atomico)
fn chunk_by_article(doc: &LegalDocument) -> Vec<LegalChunk> {
    let content = doc.texto.trim();
    if content.is_empty() {
        return Vec::new();
    }
    let id = format!("{:x}", md5::compute(format!("{}-0", doc.id)));
    vec![LegalChunk {
        id,
        doc_id: doc.id.clone(),
        chunk_index: 0,
        content: content.to_string(),
        token_count: estimate_tokens(content) as i32,
    }]
}

/// Textos longos: chunking por paragrafo com overlap
fn chunk_by_paragraph(doc: &LegalDocument, config: &ChunkingConfig) -> Vec<LegalChunk> {
    let paragraphs: Vec<&str> = doc.texto
        .split('\n')
        .map(|l| l.trim())
        .filter(|l| !l.is_empty())
        .collect();

    let mut chunks = Vec::new();
    let mut current_text = String::new();
    let mut chunk_index: i32 = 0;

    for para in &paragraphs {
        let para_tokens = estimate_tokens(para);
        let current_tokens = estimate_tokens(&current_text);

        if current_tokens > 0 && current_tokens + para_tokens > config.max_tokens {
            if estimate_tokens(&current_text) >= config.min_chunk_tokens {
                let id = format!("{:x}", md5::compute(format!("{}-{}", doc.id, chunk_index)));
                let token_count = estimate_tokens(&current_text) as i32;
                chunks.push(LegalChunk {
                    id,
                    doc_id: doc.id.clone(),
                    chunk_index,
                    content: current_text.trim().to_string(),
                    token_count,
                });
                chunk_index += 1;
            }

            // Overlap
            let overlap_bytes = config.overlap_tokens * 4;
            if current_text.len() > overlap_bytes {
                let start = current_text.ceil_char_boundary(current_text.len() - overlap_bytes);
                current_text = current_text[start..].to_string();
            }
        }

        if !current_text.is_empty() && !current_text.ends_with('\n') {
            current_text.push('\n');
        }
        current_text.push_str(para);
    }

    // Ultimo chunk
    if estimate_tokens(&current_text) >= config.min_chunk_tokens {
        let id = format!("{:x}", md5::compute(format!("{}-{}", doc.id, chunk_index)));
        let token_count = estimate_tokens(&current_text) as i32;
        chunks.push(LegalChunk {
            id,
            doc_id: doc.id.clone(),
            chunk_index,
            content: current_text.trim().to_string(),
            token_count,
        });
    }

    chunks
}

#[cfg(test)]
mod tests {
    use super::*;

    fn default_config() -> ChunkingConfig {
        ChunkingConfig { max_tokens: 512, overlap_tokens: 64, min_chunk_tokens: 10 }
    }

    #[test]
    fn test_chunk_cf_article() {
        let doc = LegalDocument {
            id: "cf_art_1".into(), tipo: "constituicao".into(),
            titulo: "Art. 1".into(),
            texto: "Art. 1 A Republica Federativa do Brasil...".into(),
            fonte: "abjur".into(), url: None, data_publicacao: None,
            metadata: serde_json::json!({}),
        };
        let chunks = chunk_document(&doc, &SourceType::Constituicao, &default_config());
        assert_eq!(chunks.len(), 1);
        assert_eq!(chunks[0].chunk_index, 0);
        assert_eq!(chunks[0].doc_id, "cf_art_1");
    }

    #[test]
    fn test_chunk_long_text() {
        let config = ChunkingConfig { max_tokens: 20, overlap_tokens: 5, min_chunk_tokens: 5 };
        let texto = "Paragrafo um com texto suficiente.\n".repeat(30);
        let doc = LegalDocument {
            id: "tcu_0".into(), tipo: "lei".into(), titulo: "T".into(),
            texto, fonte: "hf".into(), url: None, data_publicacao: None,
            metadata: serde_json::json!({}),
        };
        let chunks = chunk_document(&doc, &SourceType::AcordaoTcu, &config);
        assert!(chunks.len() > 1);
    }

    #[test]
    fn test_deterministic_ids() {
        let doc = LegalDocument {
            id: "d1".into(), tipo: "t".into(), titulo: "T".into(),
            texto: "Conteudo suficiente para gerar chunk valido de teste.".into(),
            fonte: "f".into(), url: None, data_publicacao: None,
            metadata: serde_json::json!({}),
        };
        let c1 = chunk_document(&doc, &SourceType::Constituicao, &default_config());
        let c2 = chunk_document(&doc, &SourceType::Constituicao, &default_config());
        assert_eq!(c1[0].id, c2[0].id);
    }
}
```

**Step 2: Rodar testes**

Run: `cargo test -p legal-vec-ingest chunker::tests`
Expected: PASS

**Step 3: Commit**

```bash
git add crates/legal-ingest/src/chunker.rs
git commit -m "feat(legal-vec): chunker with article and paragraph strategies"
```

---

## Task 6: OllamaEmbedder

**Files:**
- Create: `crates/legal-ingest/src/embedder.rs`

Implementacao standalone. Chama Ollama `/api/embeddings` com timeout configuravel.

**Step 1: Implementar embedder**

```rust
use anyhow::{Context, Result};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;
use tracing::{info, warn};

pub struct OllamaEmbedder {
    client: Client,
    url: String,
    model: String,
    dim: usize,
}

#[derive(Serialize)]
struct EmbedRequest<'a> {
    model: &'a str,
    prompt: &'a str,
}

#[derive(Deserialize)]
struct EmbedResponse {
    embedding: Vec<f32>,
}

impl OllamaEmbedder {
    pub fn new(url: String, model: String, dim: usize, timeout_secs: u64) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(timeout_secs))
            .build()
            .expect("failed to build reqwest client");
        Self { client, url, model, dim }
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    /// Gera embedding de um texto
    pub async fn embed(&self, text: &str) -> Result<Vec<f32>> {
        let req = EmbedRequest { model: &self.model, prompt: text };
        let resp = self.client
            .post(&self.url)
            .json(&req)
            .send()
            .await
            .context("ollama request failed")?;

        if !resp.status().is_success() {
            let status = resp.status();
            let body = resp.text().await.unwrap_or_default();
            anyhow::bail!("ollama returned {}: {}", status, body);
        }

        let data: EmbedResponse = resp.json().await.context("ollama response parse failed")?;
        Ok(data.embedding)
    }

    /// Gera embeddings em batch (sequencial, 1 request por texto)
    pub async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>> {
        let mut results = Vec::with_capacity(texts.len());
        for text in texts {
            let embedding = self.embed(text).await?;
            results.push(embedding);
        }
        Ok(results)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embedder_creation() {
        let embedder = OllamaEmbedder::new(
            "http://localhost:11434/api/embeddings".into(),
            "bge-m3".into(), 1024, 10,
        );
        assert_eq!(embedder.dim(), 1024);
    }

    // Integration test -- requer Ollama rodando
    // #[tokio::test]
    // async fn test_embed_real() {
    //     let embedder = OllamaEmbedder::new(
    //         "http://100.114.203.28:11434/api/embeddings".into(),
    //         "bge-m3".into(), 1024, 10,
    //     );
    //     let result = embedder.embed("teste de embedding").await.unwrap();
    //     assert_eq!(result.len(), 1024);
    // }
}
```

**Step 2: Rodar testes**

Run: `cargo test -p legal-vec-ingest embedder::tests`
Expected: PASS

**Step 3: Commit**

```bash
git add crates/legal-ingest/src/embedder.rs
git commit -m "feat(legal-vec): OllamaEmbedder for bge-m3 embeddings"
```

---

## Task 7: Pipeline

**Files:**
- Create: `crates/legal-ingest/src/pipeline.rs`

Orquestra scan -> chunk -> embed usando storage + embedder.

**Step 1: Implementar pipeline**

```rust
use crate::chunker;
use crate::config::LegalConfig;
use crate::embedder::OllamaEmbedder;
use crate::scanner;
use crate::storage::Storage;
use crate::types::{CorpusSource, DbStats};
use anyhow::Result;
use indicatif::{ProgressBar, ProgressStyle};
use std::path::Path;
use tracing::info;

pub struct Pipeline {
    config: LegalConfig,
    storage: Storage,
}

impl Pipeline {
    pub fn new(config: LegalConfig) -> Result<Self> {
        let storage = Storage::open(&config.data.db_path, config.embedding.dim)?;
        Ok(Self { config, storage })
    }

    pub fn scan(&self) -> Result<Vec<CorpusSource>> {
        let corpus_dir = Path::new(&self.config.data.corpus_dir);
        scanner::scan_corpus(corpus_dir)
    }

    pub fn chunk_all(&self) -> Result<()> {
        let sources = self.scan()?;

        for source in &sources {
            let status = self.storage.get_ingest_status(&source.name)?;
            if status.as_deref() == Some("chunked") || status.as_deref() == Some("done") {
                info!(source = %source.name, "already chunked, skipping");
                continue;
            }

            self.storage.set_ingest_status(&source.name, "pending", 0, 0)?;

            let pb = ProgressBar::new(source.files.len() as u64);
            pb.set_style(ProgressStyle::default_bar()
                .template("{msg} [{bar:40}] {pos}/{len} files")
                .expect("invalid template"));
            pb.set_message(source.name.clone());

            let mut total_docs = 0i32;
            let mut total_chunks = 0i32;

            for file in &source.files {
                let docs = scanner::load_documents(file)?;
                for doc in &docs {
                    let chunks = chunker::chunk_document(doc, &source.source_type, &self.config.chunking);
                    if !chunks.is_empty() {
                        self.storage.insert_chunks(&chunks)?;
                        total_chunks += chunks.len() as i32;
                    }
                    total_docs += 1;
                }
                self.storage.insert_documents_batch(&docs, &source.name)?;
                pb.inc(1);
            }

            pb.finish_with_message(format!("{}: {} docs, {} chunks", source.name, total_docs, total_chunks));
            self.storage.set_ingest_status(&source.name, "chunked", total_docs, total_chunks)?;
        }

        Ok(())
    }

    pub async fn embed_pending(&self) -> Result<()> {
        let embedder = OllamaEmbedder::new(
            self.config.embedding.ollama.url.clone(),
            self.config.embedding.ollama.model.clone(),
            self.config.embedding.dim,
            self.config.embedding.ollama.timeout_secs,
        );

        let pending = self.storage.chunks_without_embeddings()?;
        if pending.is_empty() {
            info!("no chunks pending embedding");
            return Ok(());
        }

        info!(count = pending.len(), "embedding pending chunks");
        let pb = ProgressBar::new(pending.len() as u64);
        pb.set_style(ProgressStyle::default_bar()
            .template("embedding [{bar:40}] {pos}/{len} ({eta})")
            .expect("invalid template"));

        for chunk in &pending {
            match embedder.embed(&chunk.content).await {
                Ok(embedding) => {
                    self.storage.insert_embedding(&chunk.id, &embedding)?;
                }
                Err(e) => {
                    tracing::warn!(chunk_id = %chunk.id, error = %e, "embedding failed, skipping");
                }
            }
            pb.inc(1);
        }

        pb.finish_with_message("embedding complete");
        Ok(())
    }

    pub fn stats(&self) -> Result<DbStats> {
        self.storage.stats()
    }
}
```

**Step 2: Compilar**

Run: `cargo build -p legal-vec-ingest`
Expected: compila sem erros

**Step 3: Commit**

```bash
git add crates/legal-ingest/src/pipeline.rs
git commit -m "feat(legal-vec): pipeline orchestrates scan/chunk/embed"
```

---

## Task 8: CLI (main.rs)

**Files:**
- Modify: `crates/legal-ingest/src/main.rs`

**Step 1: Implementar CLI com clap**

```rust
use clap::{Parser, Subcommand};
use std::path::PathBuf;
use tracing_subscriber::EnvFilter;

use legal_vec_ingest::config::LegalConfig;
use legal_vec_ingest::pipeline::Pipeline;

#[derive(Parser)]
#[command(name = "legal-vec-ingest", version, about = "Legal corpus vector ingestion")]
struct Cli {
    #[arg(short, long, default_value = "legal-vec.toml")]
    config: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Scan corpus directory for sources
    Scan,
    /// Chunk all pending sources
    Chunk,
    /// Generate embeddings via Ollama
    Embed,
    /// Run full pipeline: scan + chunk + embed
    Full,
    /// Show database stats
    Stats,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::from_default_env()
                .add_directive("legal_vec=info".parse()?),
        )
        .init();

    let cli = Cli::parse();
    let config = LegalConfig::load(&cli.config)?;
    let pipeline = Pipeline::new(config)?;

    match cli.command {
        Commands::Scan => {
            let sources = pipeline.scan()?;
            println!("{} sources found:", sources.len());
            for s in &sources {
                println!("  {} ({} files, {} docs)", s.name, s.files.len(), s.doc_count);
            }
        }
        Commands::Chunk => {
            pipeline.chunk_all()?;
            let stats = pipeline.stats()?;
            println!("Chunking complete. {} docs, {} chunks", stats.document_count, stats.chunk_count);
        }
        Commands::Embed => {
            pipeline.embed_pending().await?;
            let stats = pipeline.stats()?;
            println!("Embedding complete. {} embeddings", stats.embedding_count);
        }
        Commands::Full => {
            pipeline.scan()?;
            pipeline.chunk_all()?;
            pipeline.embed_pending().await?;
            let stats = pipeline.stats()?;
            println!("Pipeline complete:");
            println!("  Documents:  {}", stats.document_count);
            println!("  Chunks:     {}", stats.chunk_count);
            println!("  Embeddings: {}", stats.embedding_count);
            for s in &stats.sources {
                println!("  {} [{}]: {} docs, {} chunks", s.source, s.status, s.doc_count, s.chunk_count);
            }
        }
        Commands::Stats => {
            let stats = pipeline.stats()?;
            println!("Documents:  {}", stats.document_count);
            println!("Chunks:     {}", stats.chunk_count);
            println!("Embeddings: {}", stats.embedding_count);
            for s in &stats.sources {
                println!("  {} [{}]: {} docs, {} chunks", s.source, s.status, s.doc_count, s.chunk_count);
            }
        }
    }

    Ok(())
}
```

**Step 2: Build e testar scan**

Run: `cd /home/opc/lex-vector/stj-vec && cargo build -p legal-vec-ingest`
Expected: compila

Run: `cd /home/opc/lex-vector/stj-vec && cargo run -p legal-vec-ingest -- scan`
Expected: mostra 3 sources com contagens corretas

**Step 3: Testar chunk**

Run: `cd /home/opc/lex-vector/stj-vec && cargo run -p legal-vec-ingest -- chunk`
Expected: processa as 3 fontes, cria chunks

**Step 4: Testar stats**

Run: `cd /home/opc/lex-vector/stj-vec && cargo run -p legal-vec-ingest -- stats`
Expected: mostra contagens

**Step 5: Commit**

```bash
git add crates/legal-ingest/src/main.rs
git commit -m "feat(legal-vec): CLI with scan/chunk/embed/full/stats"
```

---

## Task 9: Testes completos e verificacao

**Step 1: Rodar todos os testes**

Run: `cargo test -p legal-vec-ingest`
Expected: todos passam

**Step 2: Clippy**

Run: `cargo clippy -p legal-vec-ingest -- -W clippy::pedantic`
Expected: sem warnings (ou warnings aceitaveis)

**Step 3: Build release**

Run: `cargo build -p legal-vec-ingest --release`
Expected: compila

**Step 4: Teste e2e: scan + chunk + stats**

```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p legal-vec-ingest -- -c legal-vec.toml scan
cargo run --release -p legal-vec-ingest -- -c legal-vec.toml chunk
cargo run --release -p legal-vec-ingest -- -c legal-vec.toml stats
```

Expected:
- scan: 3 sources (abjur/cf 368, hf/tcu 5000, hf/tesemo 10000)
- chunk: processa tudo
- stats: 15368 docs, chunks > 15368 (textos longos geram multiplos chunks)

**Step 5: Teste embed (subset pequeno)**

Nao automatizar -- requer Ollama acessivel. Testar manualmente com `embed` e verificar que `stats` mostra embeddings > 0.

**Step 6: Commit final**

```bash
git add -A
git commit -m "feat(legal-vec): complete legal corpus ingestion pipeline"
```

---

## Notas

- O Ollama endpoint esta em `http://100.114.203.28:11434/api/embeddings` (OCI via Tailscale)
- Banco em `db/legal-vec.db` (separado do `db/stj-vec.db`)
- Embedding e o passo mais lento: 15368 docs, estimativa ~2-4h em CPU
- Nao modifica nenhum arquivo do stj-vec-core, stj-vec-ingest ou stj-vec-server

# Design: stj-vec -- Busca Vetorial Semantica para Jurisprudencia STJ

**Data:** 2026-02-23
**Status:** Draft
**Repo:** lex-vector

---

## Objetivo

Daemon Rust de busca semantica sobre ~2M documentos juridicos do STJ (acordaos e decisoes terminativas). Dois modos de uso:

1. **Busca semantica** -- "acordaos sobre responsabilidade civil em contratos bancarios" retorna documentos rankeados por similaridade
2. **RAG** -- "qual o entendimento do STJ sobre dano moral em atraso de voo?" gera resposta sintetizada com citacoes, alimentada pelos chunks mais relevantes

O sistema estende a capacidade do Claude Code com um banco juridico denso e pesquisavel.

---

## Decisoes Arquiteturais

| Decisao | Escolha | Motivo |
|---------|---------|--------|
| Linguagem | Rust | Performance, mesmo stack do cogmem, type safety |
| Estrutura | Cargo workspace (3 crates) | Ingestion e serving desacoplados |
| Storage | SQLite + sqlite-vec | Proven no cogmem, WAL permite read/write concorrente |
| Embedding modelo | Placeholder (config) | Modal vai definir modelo e dimensao |
| Embedding provider | Placeholder (trait) | Modal como provider principal, Ollama como fallback |
| Localizacao | `lex-vector/stj-vec/` | Perto dos dados e do stj-dados-abertos |
| Dados fonte | `/home/opc/juridico-data/stj/integras/` | 33GB existentes, sem copiar |

---

## Estrutura de Diretorios

```
lex-vector/
  stj-vec/
    Cargo.toml                    # [workspace]
    config.toml                   # paths, limites, embedding config
    crates/
      core/
        Cargo.toml
        src/
          lib.rs                  # re-exports
          config.rs               # deserializa config.toml
          storage.rs              # SQLite + sqlite-vec (open, insert, search, stats)
          chunker.rs              # texto juridico -> chunks com overlap
          embedder.rs             # trait Embedder + impls placeholder
          types.rs                # Chunk, SearchResult, Document, IngestStats
          error.rs                # thiserror
      server/
        Cargo.toml                # depends on core
        src/
          main.rs                 # clap: --port, --socket, --db-path, --config
          routes.rs               # axum: /search, /doc/{id}, /stats, /health
          context.rs              # AppState (Storage readonly + Embedder)
      ingest/
        Cargo.toml                # depends on core
        src/
          main.rs                 # clap subcommands: scan, chunk, embed, full
          pipeline.rs             # orquestra fases: scan -> chunk -> embed -> store
          scanner.rs              # le integras/ do disco (ZIPs e TXTs)
          progress.rs             # indicatif progress bars
    db/                           # .gitignore'd, criado em runtime
      stj-vec.db
    scripts/
      export-for-modal.sh         # PLACEHOLDER: empacota chunks para Modal
      import-from-modal.sh        # PLACEHOLDER: importa embeddings do Modal
```

---

## Config

```toml
# stj-vec/config.toml

[data]
integras_dir = "/home/opc/juridico-data/stj/integras"
metadata_dir = "/home/opc/juridico-data/stj/metadata"
db_path = "db/stj-vec.db"

[chunking]
max_tokens = 512
overlap_tokens = 64
min_chunk_tokens = 50

[embedding]
# PLACEHOLDER -- definido quando Modal estiver configurado
model = ""
dim = 0
provider = ""  # "modal" | "ollama" | "local"

[embedding.modal]
# PLACEHOLDER
endpoint = ""
batch_size = 0

[embedding.ollama]
url = "http://100.114.203.28:11434/api/embeddings"
model = "bge-m3"
timeout_secs = 10

[server]
socket = "/tmp/stj-vec.sock"
port = 8421
max_results = 20
default_threshold = 0.3
```

---

## Schema SQLite

```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA synchronous=NORMAL;

-- Documentos originais do STJ (metadados do JSON)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,              -- seqDocumento
    processo TEXT,                    -- "HC 725007"
    classe TEXT,                      -- "HABEAS CORPUS"
    ministro TEXT,
    orgao_julgador TEXT,
    data_publicacao TEXT,
    data_julgamento TEXT,
    assuntos TEXT,                    -- codigos CNJ separados por ;
    teor TEXT,                        -- resumo do desfecho ("Concedendo")
    tipo TEXT,                        -- "ACORDAO" | "DECISAO_TERMINATIVA"
    chunk_count INTEGER DEFAULT 0,
    source_file TEXT                  -- "202203.zip" ou path TXT
);

CREATE INDEX IF NOT EXISTS idx_docs_processo ON documents(processo);
CREATE INDEX IF NOT EXISTS idx_docs_ministro ON documents(ministro);
CREATE INDEX IF NOT EXISTS idx_docs_data ON documents(data_publicacao);
CREATE INDEX IF NOT EXISTS idx_docs_tipo ON documents(tipo);

-- Chunks: unidade atomica de busca
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,              -- hash(doc_id + chunk_index)
    doc_id TEXT NOT NULL,             -- FK -> documents.id
    chunk_index INTEGER,              -- posicao dentro do documento
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);

-- Embeddings vetoriais (sqlite-vec)
-- Dimensao definida em runtime via config.toml
-- Tabela criada dinamicamente pelo storage.rs quando dim > 0
-- CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
--     chunk_id TEXT PRIMARY KEY,
--     embedding float[{dim}] distance_metric=cosine
-- );

-- Controle de ingestion (resume/idempotencia)
CREATE TABLE IF NOT EXISTS ingest_log (
    source_file TEXT PRIMARY KEY,     -- "20260122.zip" ou "202203/151595464.txt"
    status TEXT NOT NULL,             -- "pending" | "chunked" | "embedded" | "done"
    doc_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    started_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingest_status ON ingest_log(status);
```

---

## Data Flow

### Ingestion (stj-vec-ingest)

4 fases explicitas, cada uma idempotente e resumable:

```
FASE 1: SCAN
  /home/opc/juridico-data/stj/integras/*.zip
    |
    v
  scanner.rs: lista ZIPs, verifica ingest_log
    |
    v
  ingest_log (status: "pending") para cada ZIP novo

FASE 2: CHUNK
  ZIP -> extrair TXTs em memoria -> limpar HTML -> chunker.rs
    |
    v
  chunks table (content preenchido, sem embedding)
  documents table (metadados do JSON correspondente)
  ingest_log (status: "chunked")

FASE 3: EMBED
  [PLACEHOLDER -- Modal ou Ollama]
  chunks.content -> provider -> vetores
    |
    v
  vec_chunks table (embeddings)
  ingest_log (status: "embedded")

FASE 4: FINALIZE
  Atualizar contadores, validar integridade
    |
    v
  ingest_log (status: "done")
```

**Resume:** `stj-vec-ingest` le `ingest_log` no startup. Arquivos com status != "done" sao retomados da fase em que pararam.

**Incremental:** o pipeline e incremental por design. Atualizacoes periodicas (~40 dias) baixam novos ZIPs, que entram como "pending". Scan e chunk rodam localmente (minutos). Modal processa apenas o delta de chunks sem embedding -- nao reprocessa os anteriores. O contrato com Modal e sempre: `SELECT id, content FROM chunks WHERE id NOT IN (SELECT chunk_id FROM vec_chunks)`.

**Paralelismo:** scanner e chunker sao CPU-bound (spawn_blocking). Embedding e I/O-bound (async). Pipeline pode processar varios ZIPs em paralelo com bounded concurrency.

### Busca (stj-vec-server)

```
query (texto livre)
    |
    v
embedder.embed(query) -> vetor
    |
    v
vec_chunks MATCH (KNN, k = limit * 4)
    |
    v
JOIN chunks ON chunk_id
JOIN documents ON doc_id
    |
    v
filtros opcionais: ministro, orgao, data range, tipo
    |
    v
[{chunk, score, documento_metadados}]
```

---

## API do Server

### Socket Unix (/tmp/stj-vec.sock)

Mesmo protocolo do cogmem: JSON in, JSON out, uma linha por request.

```json
// Busca semantica
{"action": "search", "query": "dano moral atraso voo", "limit": 10, "threshold": 0.3}
{"action": "search", "query": "contrato bancario", "filters": {"ministro": "NANCY ANDRIGHI", "tipo": "ACORDAO"}}

// Documento por ID
{"action": "doc", "id": "151595464"}

// Chunks de um documento
{"action": "chunks", "doc_id": "151595464"}

// Estatisticas
{"action": "stats"}

// Health
{"action": "ping"}
```

### HTTP (axum, porta 8421)

```
GET  /health
GET  /stats
GET  /doc/{id}
GET  /doc/{id}/chunks
POST /search    body: {"query": "...", "limit": 10, "filters": {...}}
```

### Formato de resposta (search)

```json
{
  "status": "ok",
  "query": "dano moral atraso voo",
  "results": [
    {
      "score": 0.82,
      "chunk": {
        "id": "abc123",
        "content": "...trecho do acordao...",
        "chunk_index": 3,
        "token_count": 487
      },
      "document": {
        "id": "151595464",
        "processo": "REsp 1.234.567/SP",
        "ministro": "NANCY ANDRIGHI",
        "orgao_julgador": "TERCEIRA TURMA",
        "data_publicacao": "2024-03-15",
        "tipo": "ACORDAO",
        "teor": "Dando provimento"
      }
    }
  ],
  "total": 10,
  "elapsed_ms": 45
}
```

---

## Crate: core

### embedder.rs

```rust
#[async_trait]
pub trait Embedder: Send + Sync {
    async fn embed(&self, text: &str) -> Result<Vec<f32>>;
    async fn embed_batch(&self, texts: &[String]) -> Result<Vec<Vec<f32>>>;
    fn dim(&self) -> usize;
    fn model_name(&self) -> &str;
}

/// Placeholder -- retorna erro informando que embedding nao esta configurado
pub struct NoopEmbedder;

/// PLACEHOLDER: implementar quando Modal estiver configurado
pub struct ModalEmbedder { /* config */ }

/// Fallback: Ollama na VM OCI (mesmo do cogmem)
pub struct OllamaEmbedder { /* config */ }
```

### chunker.rs

```rust
pub struct ChunkerConfig {
    pub max_tokens: usize,      // 512
    pub overlap_tokens: usize,  // 64
    pub min_chunk_tokens: usize, // 50
}

pub struct ChunkOutput {
    pub chunks: Vec<RawChunk>,
    pub doc_id: String,
}

pub struct RawChunk {
    pub content: String,
    pub chunk_index: usize,
    pub token_count: usize,
}

/// Chunker especializado para texto juridico.
/// - Remove HTML (tags <br>, &nbsp; etc)
/// - Preserva estrutura de paragrafos
/// - Quebra em limites de sentenca quando possivel
/// - Overlap para manter contexto entre chunks
pub fn chunk_legal_text(text: &str, doc_id: &str, config: &ChunkerConfig) -> ChunkOutput;
```

### storage.rs

Mesmo padrao do cogmem: `Mutex<Connection>`, `spawn_blocking` para async.

```rust
pub struct Storage { conn: Mutex<Connection> }

impl Storage {
    pub fn open(path: &str, embedding_dim: usize) -> Result<Self>;
    pub fn open_readonly(path: &str) -> Result<Self>;

    // Documents
    pub fn insert_document(&self, doc: &Document) -> Result<()>;
    pub fn get_document(&self, id: &str) -> Result<Option<Document>>;

    // Chunks
    pub fn insert_chunks(&self, chunks: &[Chunk]) -> Result<()>;
    pub fn get_chunks_by_doc(&self, doc_id: &str) -> Result<Vec<Chunk>>;

    // Embeddings
    pub fn insert_embeddings(&self, chunk_id: &str, embedding: &[f32]) -> Result<()>;
    pub fn insert_embeddings_batch(&self, pairs: &[(String, Vec<f32>)]) -> Result<()>;

    // Search
    pub fn search(&self, query_embedding: &[f32], limit: usize, threshold: f64, filters: &Filters) -> Result<Vec<SearchResult>>;

    // Stats
    pub fn stats(&self) -> Result<DbStats>;

    // Ingest log
    pub fn get_ingest_status(&self, source: &str) -> Result<Option<IngestStatus>>;
    pub fn set_ingest_status(&self, source: &str, status: &str) -> Result<()>;
}
```

---

## Crate: ingest

### Subcomandos CLI

```
stj-vec-ingest scan     --config config.toml    # lista novos ZIPs, registra no ingest_log
stj-vec-ingest chunk    --config config.toml    # processa "pending" -> "chunked"
stj-vec-ingest embed    --config config.toml    # PLACEHOLDER: "chunked" -> "embedded"
stj-vec-ingest full     --config config.toml    # scan + chunk + embed em sequencia
stj-vec-ingest stats                            # mostra estado do ingest_log
stj-vec-ingest reset    --source "202203.zip"   # reseta status para reprocessar
```

### Pipeline

```rust
pub struct Pipeline {
    storage: Arc<Storage>,
    chunker: ChunkerConfig,
    embedder: Box<dyn Embedder>,
}

impl Pipeline {
    /// Fase 1: escaneia integras_dir, registra novos arquivos
    pub async fn scan(&self, integras_dir: &Path) -> Result<ScanStats>;

    /// Fase 2: extrai texto dos ZIPs, chunkeia, salva chunks + documents
    pub async fn chunk_pending(&self) -> Result<ChunkStats>;

    /// Fase 3: PLACEHOLDER -- gera embeddings para chunks sem vetor
    pub async fn embed_pending(&self) -> Result<EmbedStats>;

    /// Fase 1+2+3
    pub async fn full(&self, integras_dir: &Path) -> Result<FullStats>;
}
```

---

## Crate: server

### Daemon

```rust
#[tokio::main]
async fn main() -> Result<()> {
    // 1. Parse args (clap)
    // 2. Load config.toml
    // 3. Open storage readonly
    // 4. Create embedder (from config)
    // 5. Build axum router
    // 6. Spawn socket listener + HTTP listener
    // 7. Graceful shutdown via CancellationToken
}
```

O server abre o DB em **readonly**. Ingestion abre em read-write. WAL mode permite ambos simultaneamente.

---

## Integracao com Claude Code

### Skill /stj-search

```bash
echo '{"action":"search","query":"TERMOS","limit":10}' | nc -U /tmp/stj-vec.sock
```

Mesmo padrao do `/mem-search` -- imperativo, obriga execucao via socket.

### RAG Flow

1. Claude recebe pergunta juridica
2. Invoca `/stj-search` com a query
3. Recebe chunks + metadados dos documentos
4. Sintetiza resposta citando processo, ministro, data, trecho

---

## Modal Integration (PLACEHOLDER)

```
# Scripts placeholder -- implementar quando Modal estiver configurado

scripts/
  export-for-modal.sh    # Extrai chunks sem embedding -> JSONL/Parquet
  import-from-modal.sh   # Le embeddings do Modal -> insere no vec_chunks

# O contrato e simples:
# EXPORT: SELECT id, content FROM chunks WHERE id NOT IN (SELECT chunk_id FROM vec_chunks)
# IMPORT: INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)

# Formato de troca: TBD (JSONL, Parquet, ou API direta)
# Modelo: TBD
# Dimensao: TBD (config.toml embedding.dim)
# Batch size: TBD
```

---

## Workspace Dependencies

```toml
# stj-vec/Cargo.toml
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

---

## Estimativas

| Metrica | Valor estimado |
|---------|---------------|
| Documentos fonte | ~2M |
| Tamanho medio doc | ~1500 tokens |
| Chunks (512tok, 64 overlap) | ~6-8M |
| Tamanho DB (chunks + docs, sem embeddings) | ~15-20GB |
| Tamanho DB (com embeddings 1024d f32) | +25-35GB |
| Tempo ingestion (scan+chunk, sem embed) | ~2-4 horas |
| Tempo busca (KNN top-20) | <100ms |

---

## Fora de escopo (por enquanto)

- FTS BM25 (ja existe no stj-dados-abertos, nao duplicar)
- Frontend web
- Reranking (cross-encoder)
- Ingestion automatica de novos ZIPs (cron)
- Multitenancy

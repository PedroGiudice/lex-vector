# stj-vec-search: Design Doc -- MVP Busca Hibrida STJ

> **Para Claude:** REQUIRED SUB-SKILL: Usar superpowers:executing-plans para implementar este plano task-by-task.

**Objetivo:** Sistema web standalone de busca hibrida (dense + sparse + RRF) sobre 13.5M chunks de jurisprudencia do STJ, com visibilidade total de scores e metadados.

**Arquitetura:** Novo crate Rust `stj-vec-search` (axum) que integra ONNX Runtime para embedding de queries, Qdrant para busca vetorial via gRPC, e SQLite read-only para metadados. Frontend React 19 servido como static files pelo proprio backend.

**Stack:** Rust (axum, ort, qdrant-client, rusqlite), React 19, Vite 7, Tailwind 4, TanStack Query, Zustand.

**Data:** 2026-03-08

---

## Indice

1. [Contexto e Motivacao](#1-contexto-e-motivacao)
2. [Decisoes Pre-aprovadas](#2-decisoes-pre-aprovadas)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Backend: Crate stj-vec-search](#4-backend-crate-stj-vec-search)
5. [Embedding de Queries via ONNX](#5-embedding-de-queries-via-onnx)
6. [Busca Hibrida no Qdrant](#6-busca-hibrida-no-qdrant)
7. [API Contracts](#7-api-contracts)
8. [Frontend](#8-frontend)
9. [Configuracao e Deploy](#9-configuracao-e-deploy)
10. [Tarefas de Implementacao](#10-tarefas-de-implementacao)
11. [Testes](#11-testes)
12. [Evolucao Futura](#12-evolucao-futura)
13. [Leitura Complementar](#13-leitura-complementar)

---

## 1. Contexto e Motivacao

O corpus STJ esta indexado no Qdrant (collection `stj`, 13.44M pontos, dense 1024d cosine + sparse IDF) e os metadados vivem num SQLite de 52GB (`stj-vec/db/stj-vec.db`, 2.1M documentos, 13.5M chunks). O sistema de ingestao e embedding (crates `core`, `ingest`, `case-ingest`, Modal `embed_hybrid.py`, script `import_qdrant.py`) ja esta completo.

O que falta e a **camada de busca**: receber uma query de texto livre, gerar embeddings, buscar no Qdrant com fusao RRF, enriquecer com metadados do SQLite, e apresentar resultados numa UI web.

O MVP e deliberadamente simples: busca direta, sem agentes LLM, sem decomposicao de query, sem re-ranking neural. A complexidade vive na infraestrutura (ONNX embedding, gRPC Qdrant, SQLite 52GB) e na visibilidade dos scores de matching.

---

## 2. Decisoes Pre-aprovadas

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Deployment | Web standalone (browser) | Acesso rapido sem instalacao, qualquer maquina na tailnet |
| Backend | Novo crate Rust `stj-vec-search` | Isolado dos crates de ingestao, responsabilidade unica |
| Frontend | React 19 + Vite 7 + Tailwind 4 + TanStack Query + Zustand | Template existente em `~/.claude/claude-memory-frontend/` |
| Busca | Qdrant prefetch dense+sparse + RRF server-side via Query API | Fusao no Qdrant, sem roundtrip duplo |
| Embedding de query | ONNX Runtime (`ort` crate) com BGE-M3 | Sem dependencia de TEI/servico externo |
| Metadados | SQLite read-only (rusqlite) | DB existente, sem replicacao |
| Escopo MVP | Busca direta sem LLM | Complexidade minima para validar o pipeline |
| Qdrant | localhost:6333/6334, collection `stj` | Ja configurado e populado |

---

## 3. Arquitetura do Sistema

```
Browser (React 19 + Vite 7 + Tailwind 4)
   |
   | HTTP REST (JSON)
   |
stj-vec-search (Rust, axum)  :8421
   |
   +--- POST /api/search  { query, limit?, filters? }
   |      1. Tokeniza + gera embedding dense (1024d) + sparse via ort (ONNX BGE-M3)
   |      2. Qdrant Query API (gRPC) com prefetch dense top-200 + sparse top-200 + fusao RRF
   |      3. Extrai chunk_id do payload de cada ponto retornado
   |      4. JOIN metadados no SQLite (processo, ministro, classe, data, tipo, orgao_julgador)
   |      5. Retorna: chunks + metadados + mini-log de scores (dense, sparse, rrf, ranks)
   |
   +--- GET /api/document/:doc_id
   |      Retorna todos os chunks do documento ordenados por chunk_index
   |
   +--- GET /api/health
   |      Status do backend + metricas (qdrant alive, sqlite alive, model loaded)
   |
   +--- GET /api/filters
   |      Valores distintos para filtros (ministros, classes, tipos, orgaos_julgadores)
   |
   +--- Servir frontend (static files do build React em /dist)
   |
   +--- ort::Session (BGE-M3 ONNX, carregado uma vez no startup)
   +--- qdrant_client::Qdrant (gRPC, conexao persistente)
   +--- rusqlite::Connection (read-only, pool via r2d2-sqlite ou Mutex)
```

### Diagrama de Fluxo de uma Query

```
[Navegador]
     |
     | POST /api/search { query: "dano moral bancario", limit: 20 }
     v
[axum handler]
     |
     | 1. Tokeniza com tokenizers (BGE-M3 tokenizer)
     | 2. Executa ort::Session.run() -> dense Vec<f32> 1024d
     | 3. Extrai sparse weights do output do modelo
     v
[Qdrant gRPC]
     |
     | Query API com prefetch:
     |   prefetch[0]: dense HNSW, top 200, using "dense"
     |   prefetch[1]: sparse inverted, top 200, using "sparse"
     |   fusion: RRF
     |   limit: 20
     |
     | Retorna: 20 pontos com score RRF + payloads (chunk_id, source)
     v
[axum handler]
     |
     | 4. Para cada ponto: extrair chunk_id do payload
     | 5. Buscar no Qdrant scores individuais dense e sparse (via scroll ou cache do prefetch)
     | 6. Batch SELECT no SQLite: chunks.content + documents.* WHERE chunks.id IN (...)
     v
[Resposta JSON]
     |
     | { results: [...], query_info: { embedding_ms, search_ms, total_ms } }
     v
[Navegador renderiza]
```

### Nota sobre Scores Individuais

O Query API do Qdrant com fusao RRF retorna apenas o score RRF final. Para obter os scores individuais dense e sparse (requisito do mini-log), ha duas abordagens:

**Abordagem A -- Duas queries separadas + fusao local:**
Enviar uma query dense e uma sparse separadamente, fazer RRF no Rust. Mais simples de implementar, controle total dos scores, mas 2 roundtrips ao Qdrant.

**Abordagem B -- Query API com prefetch + query separada para scores:**
Usar Query API para resultado final, depois scroll por IDs para obter scores individuais. Mais complexo, 2+ roundtrips.

**Decisao para o MVP: Abordagem A.** Duas queries gRPC paralelas (tokio::join!), fusao RRF no Rust. Latencia similar (queries rodam em paralelo), implementacao mais simples, controle total dos scores individuais. O overhead de fusao local para 200+200 candidatos e negligivel (~microsegundos).

---

## 4. Backend: Crate stj-vec-search

### 4.1. Estrutura do Crate

```
stj-vec/crates/search/
  Cargo.toml
  src/
    main.rs          -- startup, CLI args, carregamento de recursos
    config.rs        -- SearchConfig (TOML)
    routes.rs        -- handlers axum
    embedder.rs      -- OnnxEmbedder (dense + sparse)
    searcher.rs      -- QdrantSearcher (gRPC queries + RRF fusion)
    metadata.rs      -- MetadataStore (SQLite read-only queries)
    types.rs         -- structs de request/response
    error.rs         -- error types
```

### 4.2. Dependencias (Cargo.toml)

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

### 4.3. Relacao com Crates Existentes

O crate `stj-vec-search` NAO depende de `stj-vec-core`. Razoes:

1. `stj-vec-core` carrega sqlite-vec (extensao C, linking complexo) -- desnecessario para busca read-only
2. `stj-vec-core` tem `Storage` com Mutex<Connection> -- queremos pool r2d2 para read-only
3. Os tipos de request/response sao diferentes (MVP inclui scores individuais, ranks, metricas)
4. Embedder do core usa TEI/Ollama HTTP -- queremos ONNX local

O crate `search` reimplementa apenas o que precisa: leitura de metadados SQLite e tipos proprios.

---

## 5. Embedding de Queries via ONNX

### 5.1. Modelo BGE-M3 em ONNX

O modelo BGE-M3 precisa ser exportado para ONNX. O modelo original esta em `/home/opc/lex-vector/stj-vec/modal/` (FlagEmbedding, PyTorch). A exportacao gera:

- `model.onnx` -- grafo de inferencia
- `tokenizer.json` -- tokenizer HuggingFace (usado pelo crate `tokenizers`)

**Exportacao (one-time, fora do escopo do crate):**

```bash
# Na VM, com o modelo BGE-M3 ja baixado
python3 -c "
from optimum.exporters.onnx import main_export
main_export('BAAI/bge-m3', 'bge-m3-onnx/', task='feature-extraction')
"
```

Resultado esperado: `bge-m3-onnx/model.onnx` (~2.2GB) + `tokenizer.json` (~14MB).

Caminho de deploy: `stj-vec/models/bge-m3-onnx/` (fora do Git, `.gitignore`).

### 5.2. OnnxEmbedder

```rust
// src/embedder.rs (interface)

pub struct OnnxEmbedder {
    session: ort::Session,
    tokenizer: tokenizers::Tokenizer,
}

pub struct EmbeddingOutput {
    pub dense: Vec<f32>,           // 1024 dimensoes
    pub sparse: HashMap<u32, f32>, // token_id -> weight
    pub elapsed_ms: u64,
}

impl OnnxEmbedder {
    /// Carrega modelo ONNX e tokenizer do diretorio.
    /// Chamado uma vez no startup do servidor.
    pub fn load(model_dir: &Path) -> Result<Self>;

    /// Gera embedding dense + sparse para um texto de query.
    /// Thread-safe: ort::Session suporta inferencia concorrente.
    pub fn embed(&self, text: &str) -> Result<EmbeddingOutput>;
}
```

**Geracao de sparse embeddings:** O BGE-M3 produz sparse weights como parte do output do modelo (camada `sparse_output` ou via processamento do last_hidden_state). O approach no MVP:

1. Tokenizar o texto com o tokenizer do BGE-M3
2. Rodar inferencia ONNX: input_ids, attention_mask, token_type_ids -> outputs
3. Output dense: mean pooling do last_hidden_state -> vetor 1024d
4. Output sparse: pesos por token extraidos do output do modelo (mesma logica do FlagEmbedding)

**Fallback se sparse ONNX for complexo:** Gerar sparse weights via contagem de termos (TF simples) usando os token_ids do tokenizer. Funcional para o MVP, menos preciso que o modelo treinado. Documentar a diferenca e planejar upgrade.

### 5.3. Performance Esperada

| Metrica | Valor Estimado |
|---------|----------------|
| Carga do modelo | ~10-15s (one-time, startup) |
| Inferencia por query | ~50-150ms (CPU, 16 vCPUs EPYC) |
| RAM do modelo | ~2-3GB |
| Threads ONNX | 4-8 (configuravel via `ort` session options) |

---

## 6. Busca Hibrida no Qdrant

### 6.1. Collection Existente

```
Collection: stj
  - Named vectors:
    - "dense": 1024d, cosine, on_disk, int8 scalar quantization (always_ram)
    - "sparse": sparse, IDF modifier
  - Payload por ponto:
    - chunk_id: string (ID original do chunk no SQLite)
    - source: string (nome do source file)
  - Total: 13.44M pontos
  - IDs: UUIDs deterministicos (uuid.UUID(chunk_id))
```

### 6.2. Estrategia de Busca (Abordagem A)

Duas queries gRPC em paralelo via `tokio::join!`:

**Query 1 -- Dense:**
```
SearchPoints {
  collection: "stj",
  vector: NamedVector("dense", query_dense_vec),
  limit: 200,
  with_payload: true,  // chunk_id
  with_vectors: false,
  filter: <filtros opcionais>,
}
```

**Query 2 -- Sparse:**
```
SearchPoints {
  collection: "stj",
  vector: NamedSparseVector("sparse", indices, values),
  limit: 200,
  with_payload: true,
  with_vectors: false,
  filter: <filtros opcionais>,
}
```

### 6.3. Fusao RRF (Reciprocal Rank Fusion)

```rust
// src/searcher.rs

const RRF_K: f64 = 60.0;

struct RankedResult {
    chunk_id: String,
    dense_score: f32,
    sparse_score: f32,
    dense_rank: usize,   // 1-indexed, 0 se ausente
    sparse_rank: usize,  // 1-indexed, 0 se ausente
    rrf_score: f64,
}

fn fuse_rrf(
    dense_results: Vec<ScoredPoint>,
    sparse_results: Vec<ScoredPoint>,
    limit: usize,
) -> Vec<RankedResult> {
    // 1. Indexar dense: chunk_id -> (rank, score)
    // 2. Indexar sparse: chunk_id -> (rank, score)
    // 3. Uniao de chunk_ids
    // 4. Para cada: rrf = 1/(K+dense_rank) + 1/(K+sparse_rank)
    //    Se ausente num lado, contribuicao = 0
    // 5. Ordenar por rrf_score desc
    // 6. Truncar em limit
}
```

### 6.4. Filtros no Qdrant

Os filtros de metadados (ministro, tipo, classe, data) NAO estao no payload do Qdrant (que tem apenas `chunk_id` e `source`). Duas opcoes:

**Opcao 1 -- Filtro pos-busca no SQLite (MVP):**
Buscar top-N*3 no Qdrant sem filtros, depois filtrar via SQLite JOIN. Simples, funcional para filtros pouco restritivos.

**Opcao 2 -- Adicionar metadados ao payload do Qdrant:**
Enriquecer cada ponto com `ministro`, `tipo`, `classe`, `data_julgamento` no payload. Permite filtro pre-busca no Qdrant. Requer re-importacao.

**Decisao MVP: Opcao 1.** Over-fetch no Qdrant (top 600 por lado em vez de 200 quando filtros ativos), filtrar no Rust apos JOIN com SQLite. Documentar Opcao 2 como upgrade futuro.

---

## 7. API Contracts

### 7.1. POST /api/search

**Request:**
```json
{
  "query": "dano moral em relacao bancaria consumidor",
  "limit": 20,
  "filters": {
    "ministro": "NANCY ANDRIGHI",
    "tipo": "acordao",
    "classe": "RECURSO ESPECIAL",
    "orgao_julgador": null,
    "data_from": "2020-01-01",
    "data_to": "2025-12-31"
  }
}
```

Campos de `filters` sao todos opcionais. Se `filters` e omitido, busca sem restricao.

**Response:**
```json
{
  "results": [
    {
      "chunk_id": "abc123def456...",
      "content": "texto do trecho (ate 512 tokens)...",
      "chunk_index": 3,
      "doc_id": "doc789...",
      "processo": "REsp 1.234.567/SP",
      "classe": "RECURSO ESPECIAL",
      "ministro": "NANCY ANDRIGHI",
      "orgao_julgador": "TERCEIRA TURMA",
      "data_julgamento": "2023-05-15",
      "tipo": "acordao",
      "assuntos": "Responsabilidade civil; Dano moral",
      "scores": {
        "dense": 0.847,
        "sparse": 12.34,
        "rrf": 0.0328,
        "dense_rank": 3,
        "sparse_rank": 7
      }
    }
  ],
  "query_info": {
    "embedding_ms": 95,
    "search_ms": 12,
    "metadata_ms": 3,
    "total_ms": 110,
    "dense_candidates": 200,
    "sparse_candidates": 200,
    "pre_filter_count": 400,
    "post_filter_count": 20
  }
}
```

**Notas sobre scores:**
- `dense`: similaridade cosseno (0.0 a 1.0)
- `sparse`: score BM25/IDF do Qdrant (escala variavel, tipicamente 0-50)
- `rrf`: score RRF (tipicamente 0.001-0.033)
- `dense_rank` e `sparse_rank`: posicao no ranking individual (1-indexed, 0 se nao apareceu)

### 7.2. GET /api/document/:doc_id

**Response:**
```json
{
  "document": {
    "id": "doc789...",
    "processo": "REsp 1.234.567/SP",
    "classe": "RECURSO ESPECIAL",
    "ministro": "NANCY ANDRIGHI",
    "orgao_julgador": "TERCEIRA TURMA",
    "data_julgamento": "2023-05-15",
    "data_publicacao": "2023-06-01",
    "tipo": "acordao",
    "assuntos": "Responsabilidade civil; Dano moral"
  },
  "chunks": [
    {
      "id": "abc...",
      "chunk_index": 0,
      "content": "RECURSO ESPECIAL. RESPONSABILIDADE CIVIL...",
      "token_count": 487
    },
    {
      "id": "def...",
      "chunk_index": 1,
      "content": "No merito, o recorrente alega que...",
      "token_count": 512
    }
  ],
  "total_chunks": 5
}
```

### 7.3. GET /api/health

```json
{
  "status": "ok",
  "qdrant": true,
  "sqlite": true,
  "model_loaded": true,
  "model_name": "bge-m3-onnx",
  "collection_points": 13440000,
  "document_count": 2100000,
  "uptime_secs": 3600
}
```

### 7.4. GET /api/filters

```json
{
  "ministros": ["NANCY ANDRIGHI", "LUIS FELIPE SALOMAO", "..."],
  "classes": ["RECURSO ESPECIAL", "AGRAVO EM RECURSO ESPECIAL", "..."],
  "tipos": ["acordao", "decisao_monocratica", "..."],
  "orgaos_julgadores": ["PRIMEIRA TURMA", "SEGUNDA TURMA", "..."]
}
```

Cacheado no startup (query no SQLite: `SELECT DISTINCT ministro FROM documents WHERE ministro IS NOT NULL ORDER BY ministro`). Refresh via restart do servidor.

---

## 8. Frontend

### 8.1. Origem: Template claude-memory-frontend

O frontend e baseado no template em `/home/opc/.claude/claude-memory-frontend/`. Componentes reutilizados:

| Componente | Uso no STJ | Adaptacao |
|------------|-----------|-----------|
| `SearchView` | Tela principal | Trocar tipos, adicionar metadados juridicos, mini-log de scores |
| `ScoreBar` | Visualizacao de score RRF | Adaptar escala (RRF e 0-0.033, nao 0-1) |
| `Skeleton` | Loading states | Sem mudanca |
| `ApertureSpinner` | Loading indicator | Sem mudanca |
| `ErrorBoundary` | Error handling | Sem mudanca |
| `DaemonBanner` | Status do backend | Renomear para "ServerBanner" |
| `ThemeSwitcher` | Dark/light mode | Sem mudanca |

### 8.2. Estrutura do Frontend

```
stj-vec/frontend/
  package.json
  tsconfig.json
  vite.config.ts
  index.html
  src/
    main.tsx
    App.tsx
    api/
      client.ts          -- fetchJson, buildUrl, apontando para :8421
      types.ts           -- SearchResult, SearchResponse, DocumentResponse, etc.
    components/
      views/
        SearchView.tsx   -- tela principal: input + resultados + preview
      feedback/
        ServerBanner.tsx -- status do backend
        ErrorBoundary.tsx
      indicators/
        ScoreBar.tsx     -- barra de score (adaptada para multi-score)
        MatchingLog.tsx  -- mini-log: dense, sparse, rrf, ranks
        Skeleton.tsx
        ApertureSpinner.tsx
      layout/
        FilterPanel.tsx  -- filtros de metadados (ministro, tipo, classe, data)
    hooks/
      use-search.ts      -- TanStack Query: POST /api/search
      use-document.ts    -- TanStack Query: GET /api/document/:id
      use-health.ts      -- TanStack Query: GET /api/health
      use-filters.ts     -- TanStack Query: GET /api/filters
    store/
      app-store.ts       -- Zustand: query, filters, selected result
    styles/
      globals.css        -- Tailwind 4 + variaveis CSS do template
    lib/
      helpers.ts         -- formatDate, truncate, etc.
```

### 8.3. Layout da Tela Principal

```
+-------------------------------------------------------------------+
| [ServerBanner: status do backend]                    [ThemeSwitcher] |
+-------------------------------------------------------------------+
|                                                                     |
|  +-- Search Input ------------------------------------------------+ |
|  | [Q] dano moral bancario consumidor          [20 resultados]     | |
|  +----------------------------------------------------------------+ |
|                                                                     |
|  +-- Filter Bar --------------------------------------------------+ |
|  | Ministro: [NANCY ANDRIGHI v] Tipo: [acordao v] Classe: [todos] | |
|  | Periodo: [2020-01-01] a [2025-12-31]                           | |
|  +----------------------------------------------------------------+ |
|                                                                     |
|  +-- Results (esquerda) ----+  +-- Preview (direita) -----------+ |
|  |                          |  |                                 | |
|  |  REsp 1.234.567/SP       |  |  Documento Completo            | |
|  |  NANCY ANDRIGHI          |  |                                 | |
|  |  TERCEIRA TURMA          |  |  Chunk 1/5:                    | |
|  |  2023-05-15 | acordao    |  |  RECURSO ESPECIAL. RESP...     | |
|  |  "...dano moral no..."   |  |                                 | |
|  |  +-- Matching Log -----+ |  |  Chunk 2/5:                    | |
|  |  | D:0.847 #3          | |  |  No merito, o recorrente...    | |
|  |  | S:12.34 #7          | |  |                                 | |
|  |  | RRF:0.033           | |  |  [chunk matchado destacado]    | |
|  |  +---------------------+ |  |                                 | |
|  |                          |  |  Chunk 3/5: <-- este matchou   | |
|  |  REsp 987.654/RJ         |  |  +++HIGHLIGHT+++               | |
|  |  ...                     |  |  considerando o dano moral...  | |
|  |  ...                     |  |                                 | |
|  +-- (scroll) -------------+  +-- (scroll) --------------------+ |
+-------------------------------------------------------------------+
|  Query: 95ms embed | 12ms search | 3ms meta | 110ms total         |
+-------------------------------------------------------------------+
```

### 8.4. Componente MatchingLog

Componente novo que renderiza o mini-log de scores para cada resultado:

```tsx
interface MatchingLogProps {
  scores: {
    dense: number;
    sparse: number;
    rrf: number;
    dense_rank: number;
    sparse_rank: number;
  };
}

// Renderiza como:
// D: 0.847 #3  |  S: 12.34 #7  |  RRF: 0.033
// Com cor indicando forca relativa
```

### 8.5. Proxy e Build

Em desenvolvimento: Vite dev server com proxy para `localhost:8421`.

Em producao: `bun run build` gera `dist/`, servido pelo axum via `tower-http::services::ServeDir`.

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8421',
    },
  },
});
```

---

## 9. Configuracao e Deploy

### 9.1. Arquivo de Configuracao

```toml
# stj-vec/search-config.toml

[server]
port = 8421
static_dir = "frontend/dist"     # path relativo ao cwd ou absoluto
cors_origins = ["http://localhost:5173"]  # dev mode

[model]
dir = "models/bge-m3-onnx"       # contem model.onnx + tokenizer.json
threads = 8                       # threads de inferencia ONNX

[qdrant]
url = "http://localhost:6334"     # gRPC
collection = "stj"
dense_top_k = 200                 # candidatos por lado
sparse_top_k = 200
rrf_k = 60                        # constante RRF

[sqlite]
path = "db/stj-vec.db"            # read-only
pool_size = 4                     # conexoes no pool r2d2

[search]
max_results = 50                  # maximo permitido por request
default_limit = 20
overfetch_factor = 3              # multiplicador quando filtros ativos
```

### 9.2. Startup do Servidor

```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-search -- --config search-config.toml
```

Sequencia de startup:
1. Carregar config TOML
2. Abrir pool SQLite read-only (r2d2, N conexoes)
3. Carregar modelo ONNX (10-15s)
4. Conectar ao Qdrant gRPC, verificar collection existe
5. Cachear filtros (SELECT DISTINCT no SQLite)
6. Iniciar servidor axum em 0.0.0.0:8421
7. Log: "stj-vec-search ready on :8421 (model loaded in Xms, Y docs, Z points)"

### 9.3. Systemd Service (opcional, pos-MVP)

```ini
[Unit]
Description=stj-vec-search
After=network.target qdrant.service

[Service]
User=opc
WorkingDirectory=/home/opc/lex-vector/stj-vec
ExecStart=/home/opc/lex-vector/stj-vec/target/release/stj-vec-search --config search-config.toml
Restart=on-failure
Environment=RUST_LOG=stj_vec_search=info

[Install]
WantedBy=default.target
```

---

## 10. Tarefas de Implementacao

### Task 1: Exportar BGE-M3 para ONNX

**Arquivos:**
- Criar: `stj-vec/scripts/export_onnx.py`
- Resultado: `stj-vec/models/bge-m3-onnx/model.onnx`, `tokenizer.json`

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
import shutil

OUTPUT_DIR = Path("models/bge-m3-onnx")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

main_export(
    "BAAI/bge-m3",
    str(OUTPUT_DIR),
    task="feature-extraction",
    opset=17,
)

# Copiar tokenizer.json se nao foi exportado automaticamente
src_tokenizer = Path.home() / ".cache/huggingface/hub/models--BAAI--bge-m3/snapshots"
# (optimum ja copia -- verificar)

print(f"Modelo exportado em {OUTPUT_DIR}")
print(f"Arquivos: {list(OUTPUT_DIR.iterdir())}")
```

**Step 3: Executar e validar**

```bash
python3 scripts/export_onnx.py
ls -lh models/bge-m3-onnx/
# Esperado: model.onnx (~2.2GB), tokenizer.json, config.json
```

**Step 4: Adicionar ao .gitignore**

```bash
echo "models/" >> stj-vec/.gitignore
```

**Step 5: Commit**

```bash
git add scripts/export_onnx.py .gitignore
git commit -m "feat(stj-vec): script de exportacao BGE-M3 para ONNX"
```

---

### Task 2: Scaffold do crate stj-vec-search

**Arquivos:**
- Criar: `stj-vec/crates/search/Cargo.toml`
- Criar: `stj-vec/crates/search/src/main.rs`
- Criar: `stj-vec/crates/search/src/config.rs`
- Criar: `stj-vec/crates/search/src/error.rs`
- Criar: `stj-vec/crates/search/src/types.rs`
- Criar: `stj-vec/search-config.toml`

**Step 1: Criar Cargo.toml com dependencias**

Conteudo conforme secao 4.2.

**Step 2: Criar config.rs**

Structs para deserializacao do TOML conforme secao 9.1.

**Step 3: Criar types.rs**

Structs `SearchRequest`, `SearchResponse`, `SearchResultItem`, `Scores`, `QueryInfo`, `DocumentResponse`, `HealthResponse`, `FiltersResponse`.

**Step 4: Criar error.rs**

```rust
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
}
```

**Step 5: Criar main.rs minimal**

Parsing de CLI args, carga de config, placeholder para startup.

**Step 6: Verificar compilacao**

```bash
cd /home/opc/lex-vector/stj-vec
cargo check -p stj-vec-search
```

**Step 7: Commit**

```bash
git add crates/search/ search-config.toml
git commit -m "feat(stj-vec): scaffold do crate stj-vec-search"
```

---

### Task 3: OnnxEmbedder -- embedding de queries

**Arquivos:**
- Criar: `stj-vec/crates/search/src/embedder.rs`
- Criar: `stj-vec/crates/search/tests/embedder_test.rs`

**Step 1: Escrever teste de integracao**

```rust
#[test]
fn test_onnx_embedder_produces_1024d_dense() {
    let embedder = OnnxEmbedder::load(Path::new("models/bge-m3-onnx")).unwrap();
    let output = embedder.embed("dano moral bancario").unwrap();
    assert_eq!(output.dense.len(), 1024);
    assert!(!output.sparse.is_empty());
    assert!(output.elapsed_ms < 5000); // < 5s na VM
}
```

**Step 2: Implementar OnnxEmbedder**

- Carregar `model.onnx` via `ort::Session::builder()`
- Carregar `tokenizer.json` via `tokenizers::Tokenizer::from_file()`
- `embed()`: tokenizar, criar tensores, rodar inferencia, extrair dense + sparse
- Para sparse: usar pesos do ultimo hidden state por token (max pooling per-token, filtrar por threshold)

**Step 3: Rodar teste, verificar pass**

```bash
cargo test -p stj-vec-search -- --test embedder_test
```

**Step 4: Commit**

```bash
git add crates/search/src/embedder.rs crates/search/tests/
git commit -m "feat(stj-vec): OnnxEmbedder com dense+sparse BGE-M3"
```

---

### Task 4: QdrantSearcher -- busca gRPC + fusao RRF

**Arquivos:**
- Criar: `stj-vec/crates/search/src/searcher.rs`
- Criar: `stj-vec/crates/search/tests/searcher_test.rs`

**Step 1: Escrever teste unitario para RRF**

```rust
#[test]
fn test_rrf_fusion_basic() {
    // Simular 3 resultados dense e 3 sparse com overlap parcial
    let dense = vec![("a", 0.9), ("b", 0.8), ("c", 0.7)];
    let sparse = vec![("b", 15.0), ("d", 12.0), ("a", 10.0)];
    let fused = fuse_rrf(&dense, &sparse, 10, 60.0);
    // "b" deve ter score mais alto (aparece em ambos, ranks bons)
    assert_eq!(fused[0].chunk_id, "b");
    // Todos devem ter ranks corretos
    let b = &fused[0];
    assert_eq!(b.dense_rank, 2);
    assert_eq!(b.sparse_rank, 1);
}
```

**Step 2: Implementar fuse_rrf()**

Funcao pura, sem dependencia de Qdrant. Conforme secao 6.3.

**Step 3: Rodar teste, verificar pass**

**Step 4: Implementar QdrantSearcher**

```rust
pub struct QdrantSearcher {
    client: QdrantClient,
    collection: String,
    dense_top_k: u64,
    sparse_top_k: u64,
    rrf_k: f64,
}

impl QdrantSearcher {
    pub async fn search(
        &self,
        dense_vec: &[f32],
        sparse: &HashMap<u32, f32>,
        limit: usize,
    ) -> Result<Vec<RankedResult>>;
}
```

- Duas queries gRPC em `tokio::join!`
- Extrair `chunk_id` do payload de cada ponto
- Chamar `fuse_rrf()` com resultados

**Step 5: Teste de integracao (requer Qdrant rodando)**

```rust
#[tokio::test]
#[ignore] // requer Qdrant local com collection stj
async fn test_qdrant_search_integration() {
    let searcher = QdrantSearcher::new("http://localhost:6334", "stj", 200, 200, 60.0).await.unwrap();
    let dummy_dense = vec![0.0f32; 1024]; // zero vec, resultados serao ruins mas valida o pipeline
    let dummy_sparse = HashMap::from([(1u32, 1.0f32)]);
    let results = searcher.search(&dummy_dense, &dummy_sparse, 10).await.unwrap();
    assert!(!results.is_empty());
}
```

**Step 6: Commit**

```bash
git add crates/search/src/searcher.rs crates/search/tests/
git commit -m "feat(stj-vec): QdrantSearcher com busca paralela + fusao RRF"
```

---

### Task 5: MetadataStore -- leitura de metadados SQLite

**Arquivos:**
- Criar: `stj-vec/crates/search/src/metadata.rs`

**Step 1: Implementar MetadataStore**

```rust
pub struct MetadataStore {
    pool: r2d2::Pool<r2d2_sqlite::SqliteConnectionManager>,
}

impl MetadataStore {
    pub fn open(path: &str, pool_size: u32) -> Result<Self>;

    /// Busca metadados de chunks por IDs (batch).
    /// Retorna chunk content + document metadata para cada chunk_id.
    pub fn get_chunks_with_metadata(&self, chunk_ids: &[String]) -> Result<HashMap<String, ChunkWithMetadata>>;

    /// Retorna todos os chunks de um documento.
    pub fn get_document_chunks(&self, doc_id: &str) -> Result<DocumentResponse>;

    /// Valores distintos para filtros.
    pub fn get_filter_values(&self) -> Result<FiltersResponse>;

    /// Filtra chunk_ids por criterios de metadados.
    /// Retorna subset dos chunk_ids que atendem aos filtros.
    pub fn filter_chunk_ids(&self, chunk_ids: &[String], filters: &SearchFilters) -> Result<Vec<String>>;
}
```

**Nota sobre performance do batch SELECT:** Para 400 chunk_ids (200 dense + 200 sparse, uniao), usar query com `IN (...)` clause. SQLite suporta ate 999 bind parameters por default; 400 esta dentro do limite. A query faz JOIN chunks + documents.

**Step 2: Testes unitarios**

```rust
#[test]
fn test_metadata_store_open_readonly() {
    // Usar o banco real (52GB) para testar
    let store = MetadataStore::open("/home/opc/lex-vector/stj-vec/db/stj-vec.db", 2).unwrap();
    let filters = store.get_filter_values().unwrap();
    assert!(!filters.ministros.is_empty());
}
```

**Step 3: Commit**

```bash
git add crates/search/src/metadata.rs
git commit -m "feat(stj-vec): MetadataStore com leitura read-only e pool r2d2"
```

---

### Task 6: Rotas axum e integracao

**Arquivos:**
- Criar: `stj-vec/crates/search/src/routes.rs`
- Modificar: `stj-vec/crates/search/src/main.rs`

**Step 1: Definir AppState**

```rust
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

- `POST /api/search`: embed -> search Qdrant -> filter -> metadata -> response
- `GET /api/document/:doc_id`: metadata.get_document_chunks()
- `GET /api/health`: checar qdrant, sqlite, model
- `GET /api/filters`: retornar cache

**Step 3: Implementar main.rs completo**

Sequencia de startup conforme secao 9.2.
Servir static files com `tower_http::services::ServeDir`.
Fallback para index.html (SPA routing).

**Step 4: Teste de integracao end-to-end**

```bash
# Terminal 1
cargo run --release -p stj-vec-search -- --config search-config.toml

# Terminal 2
curl -X POST http://localhost:8421/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "dano moral bancario", "limit": 5}'
```

**Step 5: Commit**

```bash
git add crates/search/src/routes.rs crates/search/src/main.rs
git commit -m "feat(stj-vec): rotas axum com pipeline completo de busca"
```

---

### Task 7: Scaffold do frontend

**Arquivos:**
- Criar: `stj-vec/frontend/package.json`
- Criar: `stj-vec/frontend/vite.config.ts`
- Criar: `stj-vec/frontend/tsconfig.json` (+ app + node)
- Criar: `stj-vec/frontend/index.html`
- Criar: `stj-vec/frontend/src/main.tsx`
- Criar: `stj-vec/frontend/src/App.tsx`
- Criar: `stj-vec/frontend/src/styles/globals.css`
- Criar: `stj-vec/frontend/src/api/client.ts`
- Criar: `stj-vec/frontend/src/api/types.ts`

**Step 1: Copiar e adaptar configuracoes do template**

```bash
mkdir -p stj-vec/frontend/src
# Copiar tsconfig*.json, adaptar paths
# Copiar globals.css com variaveis CSS
```

**Step 2: Definir types.ts**

Tipos TypeScript espelhando os JSON da API (secao 7).

**Step 3: Implementar client.ts**

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

**Step 4: package.json**

```json
{
  "name": "stj-vec-search-ui",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@tanstack/react-query": "^5.90",
    "react": "^19.2",
    "react-dom": "^19.2",
    "zustand": "^5.0"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.1",
    "@types/react": "^19.2",
    "@types/react-dom": "^19.2",
    "@vitejs/plugin-react": "^5.1",
    "tailwindcss": "^4.1",
    "typescript": "~5.9",
    "vite": "^7.2"
  }
}
```

**Step 5: bun install + verificar dev server**

```bash
cd stj-vec/frontend && bun install && bun run dev
```

**Step 6: Commit**

```bash
git add frontend/
git commit -m "feat(stj-vec): scaffold do frontend React 19 + Vite 7 + Tailwind 4"
```

---

### Task 8: Hooks e componentes do frontend

**Arquivos:**
- Criar: `stj-vec/frontend/src/hooks/use-search.ts`
- Criar: `stj-vec/frontend/src/hooks/use-document.ts`
- Criar: `stj-vec/frontend/src/hooks/use-health.ts`
- Criar: `stj-vec/frontend/src/hooks/use-filters.ts`
- Criar: `stj-vec/frontend/src/store/app-store.ts`
- Copiar/adaptar: indicadores do template (ScoreBar, Skeleton, ApertureSpinner)
- Criar: `stj-vec/frontend/src/components/indicators/MatchingLog.tsx`

**Step 1: Implementar hooks TanStack Query**

```typescript
// use-search.ts
export function useSearch(query: string, filters: SearchFilters, limit: number) {
  return useQuery({
    queryKey: ['search', query, filters, limit],
    queryFn: () => api.search({ query, limit, filters }),
    enabled: query.length > 0,
    staleTime: 5 * 60 * 1000, // cache 5min por query
  });
}
```

**Step 2: Implementar store Zustand**

```typescript
interface AppState {
  query: string;
  filters: SearchFilters;
  selectedResultId: string | null;
  selectedDocId: string | null;
  setQuery: (q: string) => void;
  setFilters: (f: Partial<SearchFilters>) => void;
  selectResult: (chunkId: string, docId: string) => void;
  clearSelection: () => void;
}
```

**Step 3: Criar MatchingLog.tsx**

Componente compacto que mostra D/S/RRF com cores e ranks.

**Step 4: Adaptar ScoreBar para escala RRF**

RRF scores sao tipicamente 0.001-0.033. Normalizar para 0-1 visualmente usando min/max do resultado atual.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat(stj-vec): hooks TanStack Query, store Zustand, componentes de score"
```

---

### Task 9: SearchView -- tela principal

**Arquivos:**
- Criar: `stj-vec/frontend/src/components/views/SearchView.tsx`
- Criar: `stj-vec/frontend/src/components/layout/FilterPanel.tsx`

**Step 1: Implementar FilterPanel**

Select dropdowns para ministro, tipo, classe, orgao_julgador. Date inputs para data_from/data_to.
Populados via `useFilters()` hook.

**Step 2: Implementar SearchView**

Layout conforme secao 8.3:
- Input de busca com submit no Enter
- FilterPanel abaixo do input
- Lista de resultados a esquerda (420px) com:
  - Metadados do documento (processo, ministro, turma, data, tipo)
  - Preview do content do chunk (3 linhas, com highlight de termos)
  - MatchingLog (D/S/RRF scores e ranks)
- Painel de preview a direita com:
  - Metadados completos do documento
  - Todos os chunks do documento (via useDocument)
  - Chunk que matchou destacado visualmente
- Barra de metricas no rodape (embedding_ms, search_ms, total_ms)

**Step 3: Integrar no App.tsx**

```tsx
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-[var(--color-bg)]">
        <ServerBanner />
        <SearchView />
      </div>
    </QueryClientProvider>
  );
}
```

**Step 4: Testar com backend rodando**

```bash
# Terminal 1: backend
cargo run --release -p stj-vec-search -- --config search-config.toml

# Terminal 2: frontend dev
cd stj-vec/frontend && bun run dev
# Abrir http://localhost:5173
```

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat(stj-vec): SearchView com resultados, filtros, preview e matching log"
```

---

### Task 10: Build de producao e servir static files

**Arquivos:**
- Modificar: `stj-vec/crates/search/src/main.rs` (servir static files)
- Modificar: `stj-vec/frontend/vite.config.ts` (output dir)

**Step 1: Configurar build output**

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    outDir: 'dist',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8421',
    },
  },
});
```

**Step 2: Build do frontend**

```bash
cd stj-vec/frontend && bun run build
```

**Step 3: Configurar axum para servir dist/**

```rust
// Em main.rs, apos configurar rotas da API:
let static_service = ServeDir::new(&config.server.static_dir)
    .fallback(ServeFile::new(format!("{}/index.html", config.server.static_dir)));

let app = Router::new()
    .nest("/api", api_routes)
    .fallback_service(static_service);
```

**Step 4: Testar modo producao**

```bash
cargo run --release -p stj-vec-search -- --config search-config.toml
# Abrir http://localhost:8421 -- deve servir o frontend
# POST /api/search deve funcionar
```

**Step 5: Commit**

```bash
git add crates/search/src/main.rs frontend/
git commit -m "feat(stj-vec): servir frontend como static files via axum"
```

---

## 11. Testes

### 11.1. Testes Unitarios (sem dependencias externas)

| Teste | O que valida |
|-------|-------------|
| `test_rrf_fusion_basic` | Fusao RRF com overlap parcial |
| `test_rrf_fusion_disjoint` | Fusao RRF sem overlap (itens exclusivos de cada lado) |
| `test_rrf_fusion_single_side` | Apenas dense OU apenas sparse |
| `test_rrf_fusion_empty` | Input vazio retorna vazio |
| `test_config_parse` | Parsing do TOML de configuracao |
| `test_search_request_deserialization` | Defaults de limit e filters |
| `test_scores_serialization` | Formato JSON dos scores |

### 11.2. Testes de Integracao (requerem infra)

| Teste | Dependencia | Marker |
|-------|-------------|--------|
| `test_onnx_embedder_dense_1024d` | modelo ONNX em `models/` | `#[ignore]` |
| `test_onnx_embedder_sparse_nonzero` | modelo ONNX | `#[ignore]` |
| `test_qdrant_search_returns_results` | Qdrant local + collection stj | `#[ignore]` |
| `test_metadata_store_filter_values` | SQLite stj-vec.db | `#[ignore]` |
| `test_metadata_batch_lookup` | SQLite stj-vec.db | `#[ignore]` |
| `test_full_pipeline_e2e` | ONNX + Qdrant + SQLite | `#[ignore]` |

### 11.3. Comandos de Teste

```bash
# Unitarios (rapidos, CI)
cargo test -p stj-vec-search

# Integracao (requer infra rodando)
cargo test -p stj-vec-search -- --ignored

# Tudo
cargo test -p stj-vec-search -- --include-ignored
```

---

## 12. Evolucao Futura

### 12.1. Self-Query Retriever (pos-MVP)

Pesquisado em `stj-vec/docs/plans/query_juridica.md`. A ideia e usar um LLM para decompor a query em:
- **Componente semantico:** a busca vetorial propriamente dita
- **Componente estruturado:** filtros de metadados extraidos da query

Exemplo: "acordaos da Nancy Andrighi sobre dano moral em 2023" ->
- semantico: "dano moral"
- filtros: `{ ministro: "NANCY ANDRIGHI", tipo: "acordao", data_from: "2023-01-01", data_to: "2023-12-31" }`

Isso elimina a necessidade de o usuario preencher filtros manualmente na maioria dos casos.

### 12.2. Decomposicao Multi-Perspectiva

Tambem pesquisado em `query_juridica.md`. Para queries complexas, o LLM gera N sub-queries que capturam diferentes perspectivas do problema juridico. Cada sub-query gera resultados separados, depois fusao por RRF novamente.

Exemplo: "responsabilidade solidaria de instituicao financeira por fraude de terceiro" ->
- Sub-query 1: "fraude bancaria responsabilidade solidaria"
- Sub-query 2: "dever de seguranca banco operacao fraudulenta"
- Sub-query 3: "nexo causal fraude terceiro instituicao financeira"

### 12.3. Metadados no Payload do Qdrant

Migrar filtros de pos-busca (SQLite) para pre-busca (payload indexado no Qdrant). Requer re-importacao dos 13.44M pontos com payloads enriquecidos. Beneficio: filtros mais eficientes, especialmente para filtros restritivos.

### 12.4. Highlight de Termos no Backend

Retornar posicoes de match (offsets) dos termos da query dentro de cada chunk, para o frontend fazer highlight preciso em vez de match simplificado por string.

### 12.5. Re-ranking Neural

Apos RRF, aplicar um cross-encoder (ex: ms-marco-MiniLM) para re-ranquear os top-20 resultados. Melhora precision@k significativamente mas adiciona ~200ms de latencia.

---

## 13. Leitura Complementar

- `stj-vec/docs/plans/busca-hibrida-SQL.md` -- Analise completa de opcoes de storage vetorial (SQLite-vec vs Qdrant vs pgvector), benchmarks, e justificativa da decisao Qdrant
- `stj-vec/docs/plans/query_juridica.md` -- Pesquisa sobre decomposicao de queries juridicas, Self-Query Retriever, metadados como componente semantico
- `stj-vec/docs/plans/2026-02-24-legal-vec-ingest.md` -- Plano de ingestao do pipeline completo
- `stj-vec/modal/embed_hybrid.py` -- Implementacao Modal para geracao de embeddings dense+sparse (referencia para logica de sparse weights)
- `stj-vec/scripts/import_qdrant.py` -- Script de importacao para Qdrant (referencia para schema da collection)
- Template frontend: `/home/opc/.claude/claude-memory-frontend/` -- Componentes reutilizaveis (SearchView, ScoreBar, Skeleton, etc.)

---

*Ultima atualizacao: 2026-03-08*

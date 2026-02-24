# Retomada: stj-vec -- Implementar Ingest + Server

## Contexto rapido

Estamos construindo o `stj-vec`, um sistema de busca vetorial semantica sobre jurisprudencia do STJ. E um Cargo workspace Rust em `/home/opc/lex-vector/stj-vec/` com 3 crates: core (lib), server (bin), ingest (bin).

O core crate esta 100% implementado (types, config, chunker, embedder, storage) com 19 testes passando. Faltam os crates ingest (scanner, pipeline, CLI) e server (routes, daemon). O design e o plano de implementacao estao em `docs/plans/`.

Branch: `work/stj-vec-design`. Embedding e placeholder (Modal TBD, dim=0 no config).

## Arquivos principais

- `docs/plans/2026-02-23-stj-vec-design.md` -- design aprovado
- `docs/plans/2026-02-23-stj-vec-implementation.md` -- plano com 13 tasks (6 concluidas)
- `docs/contexto/24022026-stj-vec-core.md` -- contexto detalhado desta sessao
- `stj-vec/crates/core/src/` -- core completo (types, config, chunker, embedder, storage)
- `stj-vec/crates/ingest/src/main.rs` -- stub, precisa implementar
- `stj-vec/crates/server/src/main.rs` -- stub, precisa implementar
- `stj-vec/config.toml` -- config com paths reais

## Proximos passos (por prioridade)

Implementar tasks 7-11 usando **agent team com worktree isolation**. Tasks 12-13 serao feitas manualmente com o usuario.

### 1. Task 7: scanner.rs (ingest crate)
**Onde:** `stj-vec/crates/ingest/src/scanner.rs`
**O que:** Escaneia `/home/opc/juridico-data/stj/integras/textos/` (857 subdiretorios tipo `202203`, `20220502`). Cada subdir e um "source". Retorna `Vec<SourceDir>` com path, nome, file_count. Cross-referencia com `ingest_log` no storage para identificar sources novos.
**Verificar:** `cargo test -p stj-vec-ingest`

### 2. Task 8: pipeline.rs (ingest crate)
**Onde:** `stj-vec/crates/ingest/src/pipeline.rs`
**O que:** Pipeline struct que orquestra: `scan()` registra sources como "pending", `chunk_pending()` le TXTs de cada source, strip HTML via `core::chunker`, insere chunks + documents (metadata do JSON correspondente) no storage, marca "chunked". `embed_pending()` e placeholder (log "not configured"). Precisa ler metadata JSON de `metadata/metadados{source_name}.json` para popular documents.
**Verificar:** `cargo test -p stj-vec-ingest`

### 3. Task 9: Ingest CLI (ingest crate)
**Onde:** `stj-vec/crates/ingest/src/main.rs`
**O que:** Clap v4 com subcomandos: scan, chunk, embed (placeholder), full (scan+chunk+embed), stats, reset. Flag `--config` (default "config.toml"). Wire subcomandos para Pipeline methods.
**Verificar:** `cargo run -p stj-vec-ingest -- --config config.toml stats`

### 4. Task 10: Server routes (server crate)
**Onde:** `stj-vec/crates/server/src/routes.rs` e `context.rs`
**O que:** AppState com `Arc<Storage>` readonly + `Arc<dyn Embedder>`. Rotas axum: GET /health, GET /stats, GET /doc/:id, GET /doc/:id/chunks, POST /search (embed query + KNN + join documents).
**Verificar:** `cargo check -p stj-vec-server`

### 5. Task 11: Server daemon (server crate)
**Onde:** `stj-vec/crates/server/src/main.rs`
**O que:** Clap args (--config, --port, --socket). Load config, open storage readonly, create embedder (Noop se dim=0). Axum router com routes. Socket Unix listener (JSON line protocol, mesmo do cogmem: `{"action":"search","query":"..."}`) + HTTP listener. Graceful shutdown via CancellationToken.
**Verificar:** `cargo run -p stj-vec-server -- --config config.toml` e `curl localhost:8421/health`

### NAO FAZER (Tasks 12-13)
- Task 12 (smoke test com dados reais) -- fazer com usuario
- Task 13 (skill /stj-search) -- fazer com usuario

## Como verificar

```bash
cd /home/opc/lex-vector/stj-vec

# Testes do core (devem passar todos 19)
cargo test -p stj-vec-core --lib

# Build completo
cargo check

# Branch correta
git branch --show-current  # work/stj-vec-design
```

## Nota sobre agent team

Na sessao anterior, tentamos agent team com worktrees mas os teammates nao conseguiram commitar (worktrees foram auto-cleaned). Provavelmente precisam de instrucoes mais explicitas sobre como operar no worktree (git add/commit na branch do worktree, nao na principal). Considerar despachar com instrucoes de git mais detalhadas, ou implementar direto se agent team falhar novamente.

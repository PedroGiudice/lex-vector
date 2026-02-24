# Contexto: stj-vec -- Core Crate Implementado

**Data:** 2026-02-24
**Sessao:** work/stj-vec-design
**Duracao:** ~2h

---

## O que foi feito

### 1. Design completo do stj-vec
Documento de design aprovado em `docs/plans/2026-02-23-stj-vec-design.md`. Sistema de busca vetorial semantica sobre ~2M documentos juridicos do STJ. Arquitetura: Cargo workspace com 3 crates (core, server, ingest), SQLite + sqlite-vec, embeddings via Modal (placeholder).

### 2. Plano de implementacao com 13 tasks
Plano detalhado em `docs/plans/2026-02-23-stj-vec-implementation.md`. TDD, bite-sized tasks, codigo completo no plano. Tasks 1-6 concluidas, 7-13 pendentes.

### 3. Core crate completo (6 modulos, 19 testes)

**types.rs** -- Document, Chunk, SearchResult, SearchFilters, DbStats, IngestStatus, StjMetadata (deserializa JSON camelCase do STJ)

**error.rs** -- StjVecError com thiserror (Storage, EmbeddingNotConfigured, EmbeddingFailed, DocumentNotFound, Config, Io, Other)

**config.rs** -- AppConfig deserialization do `config.toml`. Secoes: data, chunking, embedding (placeholder dim=0), server. Metodo `embedding_enabled()` retorna false se dim=0.

**chunker.rs** -- `strip_html()` remove tags HTML dos textos STJ (br, p, entidades). `chunk_legal_text()` divide em chunks de ~512 tokens com overlap de 64. Quebra paragrafos longos por sentenca. IDs deterministicos via md5(doc_id-chunk_index).

**embedder.rs** -- Trait `Embedder` (embed, embed_batch, dim, model_name) + `NoopEmbedder` placeholder. Modal e Ollama sao stubs comentados.

**storage.rs** -- SQLite + sqlite-vec. CRUD completo: documents, chunks, ingest_log, embeddings (condicional se dim>0). Busca vetorial KNN com filtros (ministro, tipo, data range). `reset_ingest()` para reprocessar. WAL mode.

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `stj-vec/Cargo.toml` | Criado -- workspace root |
| `stj-vec/config.toml` | Criado -- config com paths reais e embedding placeholder |
| `stj-vec/crates/core/src/types.rs` | Criado -- 9 structs |
| `stj-vec/crates/core/src/error.rs` | Criado -- StjVecError enum |
| `stj-vec/crates/core/src/config.rs` | Criado -- AppConfig + 1 test |
| `stj-vec/crates/core/src/chunker.rs` | Criado -- chunker + 7 testes |
| `stj-vec/crates/core/src/embedder.rs` | Criado -- trait + noop + 3 testes |
| `stj-vec/crates/core/src/storage.rs` | Criado -- full CRUD + 7 testes |
| `stj-vec/crates/server/src/main.rs` | Stub (println) |
| `stj-vec/crates/ingest/src/main.rs` | Stub (println) |
| `stj-vec/scripts/*.sh` | Placeholders Modal |
| `docs/plans/2026-02-23-stj-vec-design.md` | Design aprovado |
| `docs/plans/2026-02-23-stj-vec-implementation.md` | Plano 13 tasks |

## Commits desta sessao

```
54b3b33 feat(stj-vec): add storage layer with SQLite + sqlite-vec
5192ff4 feat(stj-vec): implement core crate (types, config, chunker, embedder)
34277c7 feat(stj-vec): scaffold workspace with 3 crates
035f700 docs(stj-vec): implementation plan with 13 tasks
c4e7686 docs(stj-vec): design document for STJ vector search system
```

## Pendencias (tasks restantes)

| Task | Prioridade | Descricao |
|------|-----------|-----------|
| 7. scanner.rs | Alta | Escaneia `integras/textos/` (857 subdirs) |
| 8. pipeline.rs | Alta | Orquestra scan->chunk->embed |
| 9. ingest CLI | Alta | Clap subcommands (scan/chunk/embed/full/stats/reset) |
| 10. server routes | Alta | Axum: /search, /doc/:id, /stats, /health |
| 11. server daemon | Alta | Socket Unix + HTTP, graceful shutdown |
| 12. smoke test | Media | Testar com dados reais (1 source) |
| 13. /stj-search skill | Media | Skill imperativa para Claude Code |

**Tasks 7-11 podem ser feitas por agent team.** Tasks 12-13 devem ser feitas manualmente com o usuario.

## Decisoes tomadas

- **Workspace com 3 crates** em vez de crate unico: ingestion e serving desacoplados
- **SQLite + sqlite-vec** em vez de DuckDB: proven no cogmem, WAL concorrente
- **Embedding dim/modelo como placeholder**: Modal definira, config.toml parametriza
- **Dados ficam onde estao**: `/home/opc/juridico-data/stj/integras/textos/` (857 subdirs, ~2M TXTs)
- **Metadados**: JSON arrays em `/home/opc/juridico-data/stj/integras/metadata/metadados{YYYYMM}.json`
- **Formato TXT do STJ**: HTML inline (br, p, nbsp), encoding UTF-8, nome do arquivo = seqDocumento

## Formato dos dados reais

```json
// metadata/metadados202203.json
[{
  "seqDocumento": 146211705,
  "dataPublicacao": 1646276400000,   // epoch ms
  "tipoDocumento": "ACÓRDÃO",
  "processo": "AREsp 1996346    ",   // trailing spaces
  "ministro": "LUIS FELIPE SALOMÃO",
  "teor": "Concedendo",
  "assuntos": "11806;11806"
}]
```

```
# integras/textos/202203/146211705.txt
DECISÃO<br>Trata-se de agravo...<br>&nbsp;É o relatório.
```

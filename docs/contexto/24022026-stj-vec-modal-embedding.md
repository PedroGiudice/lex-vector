# Contexto: stj-vec -- Ingest/Server Completos + Modal Embedding Validado

**Data:** 2026-02-24
**Sessao:** work/stj-vec-design (continuacao)
**Duracao:** ~3h

---

## O que foi feito

### 1. Ingest crate completo (tasks 7-9)
Scanner, pipeline e CLI implementados via agent team (rust-developer em worktree). Scanner encontra subdiretorios de integras, pipeline orquestra scan->chunk com metadata JSON, CLI clap com subcomandos scan/chunk/embed/full/stats/reset/export-chunks/import-embeddings.

### 2. Server crate completo (tasks 10-11)
Routes Axum e daemon implementados via agent team (backend-developer em worktree). Rotas: GET /health, /stats, /doc/:id, /doc/:id/chunks, POST /search. Daemon HTTP + Unix socket com graceful shutdown via CancellationToken.

### 3. Decisao de modelo de embedding (CMR-45)
**BGE-M3 (BAAI/bge-m3), dim=1024, via Modal.** Justificativa: pesquisa JurisTCU mostra que modelos BERT juridicos PT-BR nao batem BM25 em retrieval; modelos modernos com contrastive training dominam. BGE-M3 e o melhor open-source multilingual (MIT).

### 4. Modal embedding service desenhado e implementado
- `modal/download_model.py`: baixa BGE-M3 para Volume `stj-vec-models`
- `modal/embed.py`: Modal Class com T4 GPU, `@enter` carrega modelo FP16, `embed_source()` processa JSONL e gera .npz + .json, `modal.map()` para escalar horizontalmente

### 5. Embedding testado com dados reais
3 chunks reais de decisoes STJ (source 202203) embeddados com sucesso no Modal T4:
- Shape: (3, 1024), dtype float32, normas ~1.0 (normalizado)
- Cold start: ~2min (build image + load model), embedding dos 3 chunks: instantaneo
- Output: .npz + .json no Volume `stj-vec-data`

### 6. CLI export/import implementado
- `export-chunks`: query chunks do SQLite por source, gera JSONL (1 arquivo por source)
- `import-embeddings`: le .npz (parser nativo Rust para formato numpy) + .json, insere no vec_chunks

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `stj-vec/crates/core/src/storage.rs` | Modificado -- adicionado `list_documents_by_source()` |
| `stj-vec/crates/ingest/src/scanner.rs` | Criado -- scan de subdiretorios integras |
| `stj-vec/crates/ingest/src/pipeline.rs` | Criado -- orquestra scan->chunk, le metadata JSON |
| `stj-vec/crates/ingest/src/exporter.rs` | Criado -- export chunks para JSONL |
| `stj-vec/crates/ingest/src/importer.rs` | Criado -- import .npz embeddings, parser npy nativo |
| `stj-vec/crates/ingest/src/main.rs` | Modificado -- CLI clap com 8 subcomandos |
| `stj-vec/crates/server/src/context.rs` | Criado -- AppState com Arc<Storage> + Arc<dyn Embedder> |
| `stj-vec/crates/server/src/routes.rs` | Criado -- 5 rotas Axum |
| `stj-vec/crates/server/src/main.rs` | Modificado -- daemon HTTP + Unix socket |
| `stj-vec/modal/download_model.py` | Criado -- download BGE-M3 para Volume |
| `stj-vec/modal/embed.py` | Criado -- Modal Class T4, batch embedding |
| `stj-vec/config.toml` | Modificado -- dim=1024, provider=modal, model=BAAI/bge-m3 |
| `docs/plans/2026-02-24-modal-embedding-service.md` | Criado -- plano 5 tasks |

## Commits desta sessao (19 commits no branch)

```
a27867a feat(stj-vec): add huggingface-secret to Modal scripts
6e61405 fix(stj-vec): rename container_idle_timeout to scaledown_window
2514243 feat(stj-vec): add import-embeddings command with .npz parser
5339fc5 feat(stj-vec): add Modal scripts for BGE-M3 embedding
f3e7fae feat(stj-vec): add export-chunks command for Modal Volume upload
b953f4f docs(stj-vec): implementation plan for Modal embedding service
3a519f7 config(stj-vec): set BGE-M3 as embedding model (dim=1024, Modal provider)
312aff7 chore(stj-vec): remove unused ErrorResponse struct
4469149 feat(stj-vec): add server daemon with socket + HTTP
79cae3c feat(stj-vec): add server routes and app state
e164c9f feat(stj-vec): add ingest CLI with clap subcommands
79b7d36 feat(stj-vec): add ingestion pipeline with scan and chunk phases
36f44e8 feat(stj-vec): add integras directory scanner
```

## Testes: 27 passing

- Core: 19 (types, config, chunker, embedder, storage)
- Ingest: 8 (scanner 3, pipeline 2, importer 3)
- Server: 0 (sem testes unitarios -- rotas testadas manualmente)

## Modal Volumes

| Volume | Conteudo |
|--------|----------|
| `stj-vec-models` | `/bge-m3/` -- modelo completo (safetensors, config, tokenizer) |
| `stj-vec-data` | `/chunks/test.jsonl` (3 chunks teste), `/embeddings/test.npz` + `.json` |

## Decisoes tomadas

- **BGE-M3 dim=1024 via Modal** (CMR-45): melhor retrieval multilingual, $5-20 para corpus completo
- **T4 GPU**: BGE-M3 FP16 cabe com folga (~6GB), throughput suficiente, mais barata
- **Multi-T4 via modal.map()**: escala horizontal, cada container pega 1 source da fila
- **1 JSONL por source**: natural com estrutura de subdiretorios, modal.map() como work queue (sem straggler)
- **Output .npz + .json**: numpy compacto, parser Rust nativo sem deps externas
- **HF secret** no Modal: acelera downloads, evita rate limits

## Pendencias

1. **Embedding de todos os dados** -- scan+chunk dos 857 sources, export, upload, Modal run, import
2. **Benchmark T4 vs GPU mais caras** -- confirmar que multi-T4 e melhor custo/throughput que A10G/A100
3. **Script de automacao** -- minimizar interacao Claude Code durante embedding (processo longo e custoso)
4. **Server search com embedder real** -- NoopEmbedder no server, precisa de ModalEmbedder ou OllamaEmbedder para queries online
5. **Smoke test completo** -- apos embedding, testar busca semantica com queries reais
6. **Skill /stj-search** (task 13) -- criar apos server funcional

## Formato dos dados reais

```
/home/opc/juridico-data/stj/integras/textos/  -- 857 subdirs (YYYYMM ou YYYYMMDD)
/home/opc/juridico-data/stj/integras/metadata/ -- metadados{source}.json (JSON array)
```

Cada TXT tem HTML inline (br, p, nbsp). Chunker ja limpa isso.

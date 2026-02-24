# Retomada: stj-vec -- Sparse Embedding + Busca Hibrida

## Contexto

Dense embedding completo: 852 sources, ~13.5M embeddings no SQLite (`db/stj-vec.db`). TEI nao suporta sparse de BGE-M3 (exige MaskedLM). Usar FlagEmbedding via `modal/embed_hybrid.py` (ja criado, nao testado).

## Arquivos

- `stj-vec/modal/embed_hybrid.py` -- FlagEmbedding dense+sparse, H200, batch=1024
- `stj-vec/modal/embed.py` -- TEI dense-only (funcional, nao mexer)
- `stj-vec/crates/core/src/storage.rs` -- schema SQLite, precisa tabela sparse_chunks
- `stj-vec/crates/server/src/routes.rs` -- rota /search, precisa busca hibrida
- `docs/contexto/24022026-embedding-session2.md` -- contexto completo

## Proximos passos

### 1. Testar embed_hybrid.py com 1 source
```bash
cd /home/opc/lex-vector/stj-vec && modal run modal/embed_hybrid.py --source 20230801
```
Verificar: .npz (dense), .json (ids), .sparse.json (lexical weights) gerados no Volume.

### 2. Avaliar throughput e decidir GPU
FlagEmbedding e PyTorch vanilla (sem flash attention). Throughput sera menor que TEI. Medir emb/s real no 1 source e decidir:
- H200 com batch alto (caro mas rapido)
- L4 com batch menor (barato mas lento)
- CMR-46 no Linear tem dados de referencia

### 3. Run sparse completo
`modal run modal/embed_hybrid.py --all-pending` -- processa TODOS os 857 sources (gera novo dense + sparse). O `list_pending_sources` checa por `.sparse.json`.

### 4. Download e import sparse
Criar importer pra `.sparse.json` -> tabela `sparse_chunks(chunk_id, token, weight)` no SQLite. Filtro de peso minimo ja no embed_hybrid.py (MIN_SPARSE_WEIGHT=0.01).

### 5. Smoke test busca dense-only (pode fazer antes do sparse)
```bash
cd /home/opc/lex-vector/stj-vec && cargo run --release -p stj-vec-server -- --config config.toml
curl -X POST localhost:8421/search -d '{"query":"recurso especial provido"}'
```
Precisa de embedder pra queries: OllamaEmbedder local ou chamar Modal.

### 6. Busca hibrida
Fusao `score = w * dense + (1-w) * sparse` configuravel em config.toml.

## Nota sobre disco
47GB livres. juridico-data (33GB) precisa migrar pro Object Storage. Prompt de cleanup em `docs/prompts/vm-cleanup.md`.

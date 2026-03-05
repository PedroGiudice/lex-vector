# Retomada: Qdrant Import + Busca Hibrida STJ

## Contexto rapido

Qdrant instalado (Docker, localhost:6333) com collection `stj` (dense 1024d + sparse IDF). 13.3M de 13.5M pontos importados via `import_qdrant.py` (REST + 6 workers). 5 sources estavam sendo re-gerados no Modal (`embed_hybrid.py` unificado dense+sparse). O "mismatch de IDs" do SQLite nao existia.

## Arquivos principais

- `stj-vec/scripts/import_qdrant.py` -- importacao REST + parallel, UUIDs idempotentes
- `stj-vec/modal/embed_hybrid.py` -- gera dense+sparse num pass (A10G, FlagEmbedding)
- `stj-vec/db/stj-vec.db` -- SQLite com metadados (2.1M docs, 13.5M chunks)
- `docs/contexto/05032026-qdrant-import-setup.md` -- contexto detalhado

## Proximos passos (por prioridade)

### 1. Completar importacao (5 sources restantes)
**Onde:** Modal volume `stj-vec-data`, depois `import_qdrant.py`
**O que:** Os 5 sources (20220810, 20230629, 20241001, 20241002, 20241014) estavam rodando no Modal. Baixar e importar:
```bash
for src in 20220810 20230629 20241001 20241002 20241014; do
    modal volume get stj-vec-data embeddings/$src.npz stj-vec/embeddings/$src.npz
    modal volume get stj-vec-data embeddings/$src.json stj-vec/embeddings/$src.json
    modal volume get stj-vec-data embeddings/$src.sparse.json stj-vec/embeddings/$src.sparse.json
done
stj-vec/.venv/bin/python stj-vec/scripts/import_qdrant.py --sources 20220810 20230629 20241001 20241002 20241014
```
**Verificar:** `curl -s http://localhost:6333/collections/stj | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['points_count'])"`  -- deve ser ~13.44M

### 2. Implementar busca hibrida
**Onde:** novo endpoint (Rust via qdrant-client ou Python)
**O que:** query que faz dense retrieval + sparse retrieval + RRF fusion no Qdrant, depois busca metadados no SQLite
**Por que:** objetivo final do stj-vec -- busca juridica em 13.5M chunks

### 3. Deprecar embed.py (TEI)
**Onde:** `stj-vec/modal/embed.py`
**O que:** Agora redundante -- `embed_hybrid.py` gera dense+sparse. Manter como referencia ou deletar.

## Como verificar

```bash
# Qdrant rodando
curl http://localhost:6333/healthz
curl -s http://localhost:6333/collections/stj | python3 -m json.tool

# Collection status
curl -s http://localhost:6333/collections/stj | python3 -c "
import sys,json; r=json.load(sys.stdin)['result']
print(f'Pontos: {r[\"points_count\"]:,}  Status: {r[\"status\"]}')
"

# DB integro
sqlite3 stj-vec/db/stj-vec.db "SELECT COUNT(*) FROM chunks;"  # 13485051

# Venv do stj-vec
stj-vec/.venv/bin/python -c "from qdrant_client import QdrantClient; print('OK')"
```

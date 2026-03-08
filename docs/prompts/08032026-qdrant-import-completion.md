# Retomada: Busca Hibrida STJ no Qdrant

## Contexto rapido

Qdrant esta com 13.44M pontos importados (99.7% dos 13.49M chunks no SQLite), collection `stj` com dense 1024d cosine + sparse IDF + quantizacao int8. O `embed_hybrid.py` gera dense+sparse num unico pass via FlagEmbedding/BGE-M3 no Modal. O `import_qdrant.py` faz importacao REST + 6 workers paralelos com UUIDs idempotentes. Os 6 sources restantes tem JSONLs vazios (nao representam dados reais).

Um bug de race condition (`volume_data.commit()` dentro de containers `.spawn()`) foi corrigido -- nunca fazer commit dentro de containers paralelos no Modal Volume.

## Arquivos principais

- `stj-vec/modal/embed_hybrid.py` -- gera dense+sparse embeddings (Modal GPU)
- `stj-vec/scripts/import_qdrant.py` -- importacao para Qdrant (REST + parallel)
- `stj-vec/db/stj-vec.db` -- SQLite com metadados (2.1M docs, 13.5M chunks)
- `docs/contexto/08032026-qdrant-import-completion.md` -- contexto desta sessao

## Proximos passos (por prioridade)

### 1. Implementar busca hibrida
**Onde:** novo script/modulo (sugestao: `stj-vec/search/hybrid_search.py` ou endpoint no ccui-backend)
**O que:** query que faz dense retrieval + sparse retrieval + RRF fusion no Qdrant, depois busca metadados no SQLite
**Por que:** objetivo final do stj-vec -- busca juridica semantica em 13.5M chunks
**Detalhes:**
- Qdrant suporta busca hibrida nativa (named vectors `dense` + `sparse`)
- RRF (Reciprocal Rank Fusion) combina os scores dos dois retrievals
- Apos retrieval, fazer JOIN com SQLite para metadados (doc_id, tribunal, data, tipo)
- Query de embedding: usar BGE-M3 localmente (TEI em CPU, porta 8080) ou via Modal
**Verificar:** query de teste retornando resultados com metadados

### 2. Deprecar embed.py (TEI-only)
**Onde:** `stj-vec/modal/embed.py`
**O que:** agora redundante -- `embed_hybrid.py` gera dense+sparse. Manter como referencia ou deletar.

### 3. Committar worktree stj-vec-continue
**Onde:** worktree em `/home/opc/lex-vector/.worktrees/stj-vec-continue/`
**O que:** commit das mudancas pendentes (fix do embed_hybrid.py + erro aprendido no CLAUDE.md + docs) e merge na main

## Como verificar

```bash
# Qdrant rodando e saudavel
curl http://localhost:6333/healthz
curl -s http://localhost:6333/collections/stj | python3 -c "
import sys,json; r=json.load(sys.stdin)['result']
print(f'Pontos: {r[\"points_count\"]:,}  Status: {r[\"status\"]}')
"
# Deve retornar: Pontos: 13,442,327  Status: green

# DB integro
sqlite3 stj-vec/db/stj-vec.db "SELECT COUNT(*) FROM chunks;"  # 13485051

# Venv do stj-vec
stj-vec/.venv/bin/python -c "from qdrant_client import QdrantClient; print('OK')"

# embed_hybrid.py NAO tem volume_data.commit() dentro do embed_source
grep -n "volume_data.commit" stj-vec/modal/embed_hybrid.py
# Deve retornar apenas 1 linha (dentro de flush_volume)
```

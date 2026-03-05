# Contexto: Qdrant Setup + Importacao de Embeddings STJ

**Data:** 2026-03-05
**Sessao:** stj-vec-continue
**Duracao:** ~3h

---

## O que foi feito

### 1. Diagnostico do "mismatch de IDs"
O suposto mismatch entre `chunks.id` e `vec_chunks.chunk_id` nao existe. O JOIN funciona via tabela auxiliar `vec_chunks_rowids` (criada automaticamente pelo sqlite-vec). O erro original era tentar consultar a virtual table `vec_chunks` sem a extensao `vec0` carregada.

### 2. Qdrant instalado e configurado
Docker container `qdrant` em localhost:6333/6334, storage persistente em `/home/opc/qdrant-data/`.
Collection `stj` criada com:
- Dense: 1024d cosine, on_disk, HNSW on_disk, quantizacao int8 always_ram
- Sparse: modifier IDF
- Optimizers: indexing_threshold=50000, memmap_threshold=50000

### 3. Script de importacao (`stj-vec/scripts/import_qdrant.py`)
REST + multiprocessing (6 workers). UUIDs derivados do chunk_id (idempotente). Suporta `--sources`, `--resume-from`, `--dry-run`, `--workers`, `--batch-size`.

### 4. Importacao executada
13,338,416 pontos importados de ~13.5M. 5 sources faltantes estao sendo re-gerados no Modal.

### 5. `embed_hybrid.py` unificado (dense + sparse)
Modificado para gerar dense (.npz + .json) + sparse (.sparse.json) num unico pass via FlagEmbedding. Adicionado `volume_data.commit()` dentro do container (antes fazia commit externo que nao persistia dense).

`list_pending_sources` agora checa os 3 arquivos (.npz + .json + .sparse.json).

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `CLAUDE.md` | Modificado -- stj-vec agora referencia Qdrant |
| `stj-vec/scripts/import_qdrant.py` | Criado -- importacao REST + parallel |
| `stj-vec/modal/embed_hybrid.py` | Modificado -- dense+sparse unificado + commit interno |

## Commits desta sessao

```
e8b093c feat(stj-vec): embed_hybrid.py gera dense + sparse num unico pass
dd462d4 feat(stj-vec): script de importacao Qdrant + atualizar CLAUDE.md
```

## Pendencias

1. **5 sources rodando no Modal** -- 20220810 (done), 20230629, 20241001, 20241002, 20241014. Apos terminar: baixar e importar no Qdrant.
2. **gRPC instavel** -- erro `sendmsg: Socket operation on non-socket`. Script usa REST como fallback. Investigar se necessario.
3. **Busca hibrida** -- Qdrant populado, proximo passo e implementar endpoint de busca (Rust ou Python).
4. **embed.py (TEI)** -- script legado para dense-only via TEI. Agora redundante com embed_hybrid.py unificado. Considerar deprecar.

## Decisoes tomadas

- **REST ao inves de gRPC** para import_qdrant.py: gRPC tinha erros de socket intermitentes
- **UUIDs do chunk_id** como point ID no Qdrant: garante idempotencia
- **commit() dentro do container** no embed_hybrid.py: commit externo nao persistia writes de outros containers
- **SQLite-vec redundante**: vec_chunks nao sera mais usado para busca, Qdrant assume

# Contexto: stj-vec -- Embedding em Massa via Modal (Dense)

**Data:** 2026-02-24
**Sessao:** work/stj-vec-embedding-pipeline
**Duracao:** ~4h

---

## O que foi feito

### 1. Fixes no chunker (char boundary panics)
O chunker fatiava strings em byte offsets arbitrarios, causando panics com caracteres multi-byte (acentos em texto juridico). Duas correcoes: `floor_char_boundary()` na quebra de paragrafos longos e `ceil_char_boundary()` no overlap entre chunks. Rust 1.93 suporta ambos nativamente.

### 2. Parsing flexivel de metadata STJ
Os JSONs de metadata do STJ tem campos com case inconsistente entre sources: `seqDocumento` (antigos) vs `SeqDocumento` (novos), `ministro` vs `NM_MINISTRO`, `dataPublicacao` como i64 (epoch) ou string ("2024-04-03"). Removido `rename_all = "camelCase"` do `StjMetadata`, adicionados `#[serde(alias)]` para todas variantes, e deserializador flexivel para datas.

### 3. Scan + chunk completo de todos os dados
857 sources escaneados e chunkeados: **2.1M documentos, 13.5M chunks**. DB SQLite em `db/stj-vec.db` com 31GB. Chunk levou ~2h rodando via `nohup` no terminal (independente do Claude Code).

### 4. Export paralelo dos chunks para JSONL
O exporter Rust (`export-chunks`) era sequencial (~7 sources/min, estimativa 2h). Criado script Python (`/tmp/reexport.py`) com `ProcessPoolExecutor(max_workers=6)` que exporta via sqlite3 em paralelo: **857 sources em ~3 minutos**, 23GB de JSONL.

Primeiro tentativa usou `sqlite3 json_object()` via shell -- rapido mas gerava JSON invalido (newlines nao escapados). O script Python com `json.dumps()` resolve corretamente.

### 5. Upload pro Modal Volume
23GB de JSONL uploadados para Volume `stj-vec-data` em `/chunks/`. Upload leva ~10min.

### 6. GPU: T4 -> L4 -> A100-40GB
- T4 original descartada
- L4 testada com benchmark real: **83 emb/s** (16.6K chunks em 3min20s)
- A100-40GB escolhida por melhor emb/$ (475K emb/$ estimado, 180K medido na primeira run)
- batch_size aumentado de 128 para 512 (A100 usava apenas 24% da VRAM)

### 7. Embedding em execucao
Run atual: 10x A100-40GB com batch_size=512 via `modal run modal/embed.py --all-pending`. Modal escalou para 10 containers automaticamente. **183/857 sources embeddados** no momento da documentacao. ETA no terminal: ~49 min para completar.

### 8. Design doc e plano para dense + sparse
Design aprovado para fase 2: trocar `sentence-transformers` por `FlagEmbedding` para gerar dense + sparse numa unica chamada. Sparse armazenado em tabela `sparse_chunks` no mesmo SQLite. Busca hibrida com fusao automatica de scores.

**NOTA: o embedding atual e SOMENTE dense.** O sparse sera adicionado depois, requerendo re-embedding de todo o corpus.

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `stj-vec/crates/core/src/chunker.rs` | Modificado -- fix char boundary com ceil/floor_char_boundary |
| `stj-vec/crates/core/src/types.rs` | Modificado -- serde aliases flexiveis, deserialize_date_flexible |
| `stj-vec/crates/ingest/src/pipeline.rs` | Modificado -- data_publicacao como Option<String> direto |
| `stj-vec/modal/embed.py` | Modificado -- gpu="A100-40GB", batch_size=512 |
| `docs/design-docs/2026-02-24-stj-vec-embedding-pipeline.md` | Criado -- design pipeline dense+sparse+reranker |
| `docs/prompts/2026-02-24-embedding-pipeline-execution.md` | Criado -- plano 9 passos |

## Commits desta sessao

```
bd9e510 docs(stj-vec): design doc e plano de execucao do pipeline de embedding
920dfdc fix(stj-vec): corrige char boundary panics no chunker e parsing flexivel de metadata
```

Mudancas nao commitadas: gpu A100-40GB e batch_size=512 no embed.py, atualizacao do design doc.

## Testes: 27 passing

- Core: 19 (types, config, chunker, embedder, storage)
- Ingest: 8 (scanner 3, pipeline 2, importer 3)
- Server: 0

## Modal Volumes

| Volume | Conteudo |
|--------|----------|
| `stj-vec-models` | `/bge-m3/` -- modelo BGE-M3 completo |
| `stj-vec-data` | `/chunks/` -- 857 JSONL (23GB), `/embeddings/` -- 183+ .npz e .json (em crescimento) |

## Decisoes tomadas

- **A100-40GB multi-container**: melhor emb/$ medido. Modal escala automaticamente (subiu 10-11 containers).
- **batch_size=512**: VRAM do A100 subutilizada (24% com batch=128). Aumentar melhora throughput.
- **Dense-only primeiro**: embeddar dense agora, adicionar sparse depois. Valida pipeline completo antes de complicar.
- **Re-export via Python, nao shell**: `sqlite3 json_object()` via shell gera JSON invalido em edge cases. Python `json.dumps()` e seguro.
- **B200 considerada mas nao adotada**: 2x B200 seria mais barato (~$28 vs ~$17) mas o run A100 ja estava andando. Para futuros runs (sparse), considerar B200 com batch_size=2048.

## Pendencias

1. **Embedding dense em andamento** -- 183/857 sources feitos, ETA ~49min. Acompanhar no terminal.
2. **Commit das mudancas nao commitadas** -- gpu A100-40GB e batch_size=512
3. **Import dos embeddings pra SQLite** -- apos embedding terminar no Modal, download e import
4. **Implementar sparse** -- trocar sentence-transformers por FlagEmbedding, re-embeddar tudo com dense+sparse
5. **Busca hibrida no server** -- fusao dense+sparse automatica
6. **Re-ranker** -- Serafim 335M ou cross-encoder Legal-BERTimbau (fase 2)
7. **Benchmark throughput real B200** -- pra run sparse, considerar 2x B200 com batch=2048
8. **Limpar /tmp** -- 23GB de JSONL em /tmp/stj-vec-chunks/ podem ser deletados apos confirmar embeddings

## Metricas de benchmark

| GPU | emb/s medido | batch_size | emb/$ |
|-----|-------------|-----------|-------|
| L4 | 83 | 128 | 373K |
| A100-40GB (1a run, 10x) | ~105 por container | 128 | 180K |
| A100-40GB (2a run, 10x) | TBD | 512 | TBD |

## Formato dos dados no Modal

```
Volume stj-vec-data:
  /chunks/{source}.jsonl      -- {"id": "chunk_id", "content": "texto..."}
  /embeddings/{source}.npz    -- dense embeddings (N x 1024, float32)
  /embeddings/{source}.json   -- chunk_ids alinhados com .npz
```

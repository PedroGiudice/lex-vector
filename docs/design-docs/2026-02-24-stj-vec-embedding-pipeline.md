# Design: stj-vec Embedding Pipeline (Dense + Sparse + Re-ranking)

**Data:** 2026-02-24
**Status:** Aprovado
**Escopo:** Pipeline completo de embedding e busca para ~13.5M chunks de jurisprudencia STJ

---

## Decisoes tomadas

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Modelo de embedding | BGE-M3 (BAAI/bge-m3) | Melhor open-source multilingual pra retrieval. JurisTCU mostra que nenhum modelo PT-BR legal bate BM25; BGE-M3 com 8K context e contrastive training domina. |
| Modos de embedding | Dense (1024d) + Sparse | Dense captura semantica; sparse captura termos exatos (artigos, sumulas, "provido"/"deferido"). ColBERT descartado por storage (~1.4TB minimo). |
| GPU | Modal A100-40GB (4x containers via map()) | Melhor emb/$ medido (~475K emb/$). BGE-M3 FP16 cabe com folga em 40GB VRAM. Benchmark real: 83 emb/s na L4, ~277 emb/s estimado na A100. |
| Re-ranker | Serafim 335M ou cross-encoder Legal-BERTimbau (2o estagio) | Roda em CPU na VM sobre top-k candidatos. Bias complementar ao BGE-M3 pra vocabulario juridico BR. Adicionado depois do pipeline base funcionar. |
| Storage | SQLite unico (dense em vec_chunks via sqlite-vec, sparse em tabela separada) | Uma base, um endpoint. |
| Busca hibrida | Fusao automatica dense + sparse com peso configuravel | Transparente pro usuario. Score = w * dense + (1-w) * sparse. |

## Arquitetura

```
[13.5M chunks no SQLite]
        |
        v
[export-chunks] --> JSONL por source (857 arquivos)
        |
        v
[Modal L4 x4-6] --> BGE-M3 FlagEmbedding
        |               |
        |               +--> dense: .npz (float32, 1024d)
        |               +--> sparse: .sparse.json (dict token->peso por chunk)
        v
[import-embeddings] --> SQLite
        |                 |
        |                 +--> vec_chunks (dense, sqlite-vec)
        |                 +--> sparse_chunks (chunk_id, token, weight)
        v
[server /search]
        |
        +--> query encode (dense + sparse)
        +--> busca dense (vec_chunks, cosine top-K)
        +--> busca sparse (sparse_chunks, weighted token match)
        +--> fusao: score = w * dense + (1-w) * sparse
        +--> [futuro] re-rank top-N com Serafim 335M
        +--> resposta
```

## Mudancas no embed.py

Trocar `sentence-transformers` por `FlagEmbedding` (biblioteca oficial BGE-M3). A API `BGEM3FlagModel.encode()` retorna `{'dense_vecs': np.ndarray, 'lexical_weights': list[dict]}` numa unica chamada.

Output por source:
- `{source}.npz` -- dense embeddings (shape: N x 1024, float32)
- `{source}.sparse.json` -- array de dicts `[{"token": weight, ...}, ...]` alinhado com chunk_ids
- `{source}.json` -- chunk_ids (como antes)

## Mudancas no storage (Rust)

Nova tabela:

```sql
CREATE TABLE IF NOT EXISTS sparse_chunks (
    chunk_id TEXT NOT NULL,
    token TEXT NOT NULL,
    weight REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sparse_token ON sparse_chunks(token);
CREATE INDEX IF NOT EXISTS idx_sparse_chunk ON sparse_chunks(chunk_id);
```

Sparse search: dado um dict query_sparse `{token: weight}`, buscar chunks que compartilham tokens e somar `query_weight * doc_weight` por chunk.

## Mudancas no importer (Rust)

Alem do `.npz`, ler `.sparse.json` e inserir na tabela `sparse_chunks`. Batch insert com transacao pra performance.

## Mudancas no server

`POST /search` passa a:
1. Chamar embedder com query -> dense_vec + sparse_dict
2. Buscar vec_chunks por cosine similarity -> top K com score_dense
3. Buscar sparse_chunks pelos tokens da query -> score_sparse por chunk
4. Fusao: `score = w * score_dense + (1-w) * score_sparse` (w configuravel em config.toml, default 0.7)
5. Retornar top N ordenado por score final

## Re-ranker (fase 2, pos-MVP)

Apos pipeline base funcional:
- Baixar Serafim 335M (PORTULAN) ou cross-encoder Legal-BERTimbau
- Rodar em CPU na VM sobre top 20-50 candidatos
- Re-ordenar com score do cross-encoder
- Configuravel via config.toml (on/off, modelo, top-k)

## Estimativas

| Item | Valor |
|------|-------|
| Chunks totais | 13.5M |
| Storage dense (vec_chunks) | ~55 GB |
| Storage sparse (sparse_chunks) | ~15-30 GB |
| Storage total DB | ~100-120 GB (com indices) |
| Custo Modal (4x L4) | ~$12-15 |
| Tempo estimado embedding | ~4-6h |
| Re-ranker latencia | <100ms pra 50 candidatos em CPU |

## Riscos

1. **DB 100+ GB em SQLite**: WAL mode e PRAGMA otimizados devem dar conta. Se performance degradar, migrar sparse pra tabela separada em arquivo .db dedicado.
2. **Sparse storage pode ser grande**: se tokens unicos por chunk forem muitos (>200), a tabela sparse_chunks tera bilhoes de rows. Monitorar e considerar filtro por peso minimo (descartar tokens com weight < threshold).
3. **FlagEmbedding vs sentence-transformers**: API diferente, precisa testar na image Modal antes de rodar em massa.

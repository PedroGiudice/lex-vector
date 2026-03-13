# Busca híbrida em produção com 13.5M chunks e BGE-M3

A abordagem híbrida BLOB + rerank (opção C) é o **padrão de facto em produção** para BGE-M3 a essa escala — a própria documentação do modelo recomenda usar dense retrieval como primeiro estágio e aplicar sparse scoring apenas nos top-K candidatos. Para a stack completa, **Qdrant é a escolha mais vantajosa**: suporta nativamente sparse vectors desde v1.7, tem cliente Rust oficial, opera com ~24-32 GB de RAM via quantização escalar + mmap, e elimina a necessidade de reimplementar índice invertido ou gerenciar a complexidade do Elasticsearch. SQLite a 120 GB é viável para metadados, mas inviável como motor de busca vetorial sem ANN index — a migração para Qdrant (ou PostgreSQL + pgvector como fallback) é necessária.

---

## Sparse vectors do BGE-M3 e os três caminhos de armazenamento

O BGE-M3 produz sparse vectors como dicionários `{token_id: float32_weight}` sobre um vocabulário de **250.002 dimensões** (tokenizer XLM-RoBERTa), com ativação ReLU garantindo valores estritamente não-negativos. Para chunks de jurisprudência de ~200-500 tokens, espere **100-200 elementos não-zero por vetor**, resultando em ~1.2 KB por vetor sparse e **~16 GB totais** para 13.5M chunks.

A **opção A (BLOB + brute force)** sobre 13.5M vetores é computacionalmente proibitiva: ~2.7 bilhões de comparações por query, resultando em 5-30 segundos mesmo com Rust + SIMD e dados em RAM. A **opção B (tabela invertida)** gera ~2 bilhões de rows (`chunk_id, token_id, weight`), com 48-64 GB incluindo índices. SQLite aguenta esse volume (há relatos de 10B rows), mas tokens populares produzem posting lists de milhões de entradas, e sem pruning avançado (max-score, WAND), queries levam 100ms a vários segundos. Essencialmente, você estaria reimplementando o que vector databases já fazem internamente.

A **opção C (híbrida)** é o padrão recomendado pela própria documentação do BGE-M3: dense HNSW retorna top-1000 em ~5-50ms, carregar 1000 BLOBs sparse custa <10ms (1.2 MB de I/O), e computar 1000 dot products sparse leva <1ms em Rust. **Latência total: 10-60ms por query**, plenamente interativa. O Vespa demonstrou esta arquitetura com BGE-M3 em produção usando `weakAnd` + rerank multi-estágio, e o Pinecone confirma que SPLADE+dense híbrido consistentemente supera qualquer modalidade isolada nos benchmarks BEIR.

```rust
fn sparse_dot_product(q_idx: &[u32], q_val: &[f32], d_idx: &[u32], d_val: &[f32]) -> f32 {
    let (mut i, mut j) = (0, 0);
    let mut score = 0.0f32;
    while i < q_idx.len() && j < d_idx.len() {
        match q_idx[i].cmp(&d_idx[j]) {
            std::cmp::Ordering::Equal => { score += q_val[i] * d_val[j]; i += 1; j += 1; }
            std::cmp::Ordering::Less => i += 1,
            std::cmp::Ordering::Greater => j += 1,
        }
    }
    score
}
```

Internamente, as vector databases tratam sparse vectors de formas distintas. O **Qdrant** usa índice invertido clássico com busca exata (não aproximada), com posting lists `(vector_id, weight)` por dimensão e suporte a IDF automático. O **Elasticsearch** armazena sparse vectors no índice invertido do Lucene, com décadas de otimização em compressão e traversal. O **Milvus** usa `SPARSE_INVERTED_INDEX` com inner product. Todos convergem para o mesmo princípio: índice invertido para sparse, HNSW para dense, fusão via RRF ou score linear.

---

## SQLite a 120 GB encontra seus limites para busca vetorial

SQLite suporta 120 GB tecnicamente — o limite teórico é **281 TB** (2⁴⁸ bytes), e há relatos de bancos de centenas de GB em produção para workloads read-heavy. Com as pragmas corretas (`WAL`, `mmap_size ≥ 130GB`, `page_size = 16384`, `cache_size = -65536`), leituras concorrentes ilimitadas funcionam bem. A documentação oficial do SQLite, porém, é clara: *"If you are contemplating databases of this magnitude, you would do well to consider a client/server database engine."*

O problema não é SQLite como storage de metadados — é a **ausência de índice ANN**. O **sqlite-vec** (v0.1.6, por Alex Garcia) faz apenas brute-force, sem HNSW ou IVF. A 13.5M × 1024 dimensões, cada query escanearia ~54 GB de vetores densos, levando dezenas de segundos. O sqlite-vss (baseado em Faiss) foi **efetivamente abandonado**. Nenhuma extensão SQLite suporta sparse vectors nativamente. Para busca vetorial a essa escala, SQLite precisa ser complementado por um motor externo.

O **PostgreSQL + pgvector** (v0.8.2) é a alternativa relacional mais madura. Suporta HNSW e IVFFlat com indexação paralela (até 30× mais rápido que builds single-thread), **tipo `sparsevec` nativo** (v0.7.0+) com até 1.000 elementos não-zero, e quantização escalar via `halfvec` (redução de 50% no storage). A 13.5M × 1024 dimensões com float32, o índice HNSW consome **~110-165 GB** em RAM; com `halfvec`, cai para **~55-85 GB**. O `pgvector-rust` (v0.4) integra diretamente com sqlx: `pgvector = { version = "0.4", features = ["sqlx"] }`, suportando tipos `Vector`, `HalfVector`, `SparseVector` e `Bit`.

Uma opção particularmente relevante para VPS com RAM limitada é o **pgvectorscale** (Timescale), que implementa StreamingDiskANN em Rust via PGRX. No benchmark com **50M vetores × 768 dimensões** (Cohere), alcançou **471 QPS a 99% recall** com p50: 31ms, p95: 60ms — sem exigir que o índice caiba inteiro em RAM. Para um VPS com 32-48 GB de RAM, esta é a combinação mais custo-eficiente no ecossistema PostgreSQL.

| Aspecto | SQLite | PostgreSQL + pgvector |
|---|---|---|
| Busca vetorial ANN | ❌ Nenhuma extensão viável | ✅ HNSW, IVFFlat, DiskANN |
| Sparse vectors nativo | ❌ Não suportado | ✅ `sparsevec` (v0.7.0+) |
| Concorrência | Leitores ilimitados, 1 writer | MVCC completo, múltiplos writers |
| RAM para 13.5M×1024 | N/A (sem ANN) | ~14 GB (int8) a ~55 GB (float32) |
| Complexidade operacional | Zero config, arquivo único | Servidor, tuning, monitoring |
| Migração sqlx (Rust) | Atual | Troca de feature flag + query syntax |

---

## Elasticsearch resolve busca híbrida mas cobra caro em recursos

O ES suporta **nativamente** a arquitetura desejada: campo `dense_vector` com HNSW para kNN, campo `sparse_vector` para vetores SPLADE custom, e **RRF Retriever** (GA desde ES 8.16) para fusão. Confirmado: os sparse vectors do BGE-M3 podem ser indexados diretamente no campo `sparse_vector` — a ativação ReLU garante valores positivos, e o formato `{"token": weight}` é compatível. Existe até um modelo adaptado no HuggingFace (`dabitbol/bge-m3-sparse-elastic`). Desde ES 8.15, o parâmetro `query_vector` permite queries com vetores sparse pré-computados.

A query triple-híbrida (BM25 + dense kNN + sparse BGE-M3) funciona em uma única chamada via RRF ou Linear Retriever (ES 8.18+):

```json
{
  "retriever": {
    "rrf": {
      "retrievers": [
        { "standard": { "query": { "match": { "text": "direito constitucional" } } } },
        { "standard": { "query": { "sparse_vector": { "field": "sparse_embedding", "query_vector": {"constitucional": 0.85} } } } },
        { "knn": { "field": "dense_embedding", "query_vector": [...], "k": 20, "num_candidates": 200,
                   "filter": { "term": { "tribunal": "STF" } } } }
      ],
      "rank_constant": 60, "rank_window_size": 100
    }
  }
}
```

Para **13.5M docs com int8 quantization**, os vetores densos consomem **~14 GB** de off-heap RAM (fórmula: `num_vectors × (dims + 12) × 1 byte`). Sparse vectors usam o índice invertido do Lucene com footprint de memória significativamente menor. O benchmark da Elastic com **138M vetores × 1024 dims** indexou em <5 horas (~8K docs/s) num cluster de 3 nós × 60 GB RAM. Em single-node para 13.5M, espere **5-30ms por kNN query** com segmentos bem consolidados.

O **DiskBBQ** (ES 9.2+, GA em dezembro 2025) é transformador: usa clustering hierárquico k-means + Better Binary Quantization para busca em disco, alcançando **~15ms de latência com apenas 100 MB de RAM** para vetores. Isso eliminaria a necessidade de 55+ GB de RAM para HNSW.

**Ressalva crítica**: o RRF Retriever requer **licença Enterprise/Platinum** no ES self-managed. Para deployment on-premise em VPS sem licença paga, essa funcionalidade não está disponível — seria necessário implementar RRF manualmente no lado do cliente, o que adiciona complexidade. Sparse vector fields também só retornaram ao ES a partir da versão 8.11; versões anteriores não servem.

| Config ES | RAM mínima (single node) | Latência kNN estimada |
|---|---|---|
| HNSW float32 | 96-128 GB | 5-15 ms |
| HNSW int8 | 64-96 GB | 5-20 ms |
| HNSW int4/BBQ | 48-64 GB | 10-30 ms |
| DiskBBQ (ES 9.2+) | 32-48 GB | ~15 ms |

---

## Qdrant é a escolha mais vantajosa para essa stack Rust

O **Qdrant** (v1.17.0, escrito em Rust, 27K+ stars no GitHub) é o único sistema entre os avaliados que atende **todos** os requisitos simultaneamente: sparse vectors nativos, dense+sparse por ponto via named vectors, cliente Rust oficial, on-disk com mmap, e deployment single-node em VPS.

Sparse vectors são first-class citizens desde v1.7.0 — armazenados via índice invertido com busca **exata** (não aproximada), suportando IDF automático. A criação de collection com named vectors permite dense e sparse por ponto:

```json
{
  "vectors": { "dense": { "size": 1024, "distance": "Cosine", "on_disk": true } },
  "sparse_vectors": { "sparse": { "modifier": "idf" } }
}
```

A **Query API** (v1.10+) suporta hybrid search server-side com prefetch + RRF, incluindo pipelines multi-estágio:

1. Prefetch dense (HNSW, top-100) + prefetch sparse (índice invertido, top-100)
2. Fusão via RRF (Reciprocal Rank Fusion)
3. Rerank opcional com ColBERT/cross-encoder

O **cliente Rust** (`qdrant-client` v1.16.0 no crates.io) usa gRPC via Tonic, com cobertura completa da API incluindo named vectors, sparse vectors, prefetch queries e payload filtering. É o cliente oficial, mantido pela equipe Qdrant.

Para **120 GB de vetores em VPS com RAM limitada**, a configuração recomendada usa quantização escalar (int8) com vetores originais em disco via mmap:

- **Vetores densos quantizados em RAM**: 13.5M × 1024 × 1 byte × 1.5 overhead ≈ **~20 GB**
- **Vetores originais**: 55 GB em disco (mmap)
- **HNSW graph**: em disco (inline storage, v1.16)
- **Índice invertido sparse**: ~5-15 GB, configurável on_disk
- **RAM total necessária: ~24-32 GB** com NVMe SSD rápido (183K+ IOPS)

O Qdrant demonstra nos benchmarks próprios o **maior RPS** e menores latências em quase todos os cenários, com 4× throughput vs concorrentes em alguns datasets. O algoritmo **ACORN** (v1.16) resolve o problema de filtered search com seletividade fraca, evitando o colapso de accuracy que afeta ES e Weaviate sob filtros restritivos. O query planner automaticamente escolhe entre HNSW traversal e brute-force no subconjunto filtrado dependendo da seletividade.

**Weaviate** é descartado: **não suporta sparse vectors custom** — sua "busca híbrida" combina apenas BM25 built-in com dense vectors, sem possibilidade de injetar vetores SPLADE/BGE-M3. Existe feature request aberta (#4019) sem implementação. Também não tem cliente Rust oficial. **Meilisearch** é descartado: busca vetorial ainda experimental, sem sparse vectors, escala a 13.5M×1024 não comprovada, e foco primário em text search para e-commerce.

---

## Arquitetura recomendada e decisão final

Para o sistema descrito — 13.5M chunks de jurisprudência, BGE-M3 dense+sparse, Rust, VPS dedicado — a arquitetura ótima combina **Qdrant como motor de busca** com SQLite retido para metadados não-vetoriais se desejado.

O pipeline de query é o padrão Option C confirmado pela documentação BGE-M3:

1. **Query encoding**: BGE-M3 produz dense (1024-dim), sparse (token→weight), e opcionalmente ColBERT
2. **Retrieval**: Qdrant Query API com prefetch dense (HNSW, top-200) + prefetch sparse (inverted index, top-200)
3. **Fusion**: RRF server-side no Qdrant, retornando top-20
4. **Filtros**: payload-based filtering (tribunal, data, tipo) aplicados durante o traversal HNSW

O VPS ideal: **32-64 GB RAM, NVMe SSD 500GB+, 8 cores**. Com quantização escalar + mmap, 32 GB é suficiente. O deployment é um único container Docker: `docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.17.0`. A integração Rust usa `qdrant-client` via gRPC assíncrono com Tokio — sem overhead de serialização HTTP.

Se a preferência for por stack relacional sem dependência de vector DB dedicado, **PostgreSQL + pgvector + pgvectorscale** é o fallback mais sólido: `sparsevec` nativo, HNSW ou DiskANN para dense, sqlx já suportado, e o `pgvector-rust` crate integra diretamente. O custo é mais RAM (64+ GB para HNSW float32, ou 32-48 GB com StreamingDiskANN) e complexidade operacional maior que Qdrant.

| Critério | Qdrant | PostgreSQL + pgvector | Elasticsearch |
|---|---|---|---|
| Sparse vectors BGE-M3 | ✅ Nativo, inverted index | ✅ `sparsevec` (max 1000 non-zero) | ✅ `sparse_vector` field |
| Hybrid search server-side | ✅ RRF, prefetch, rerank | ❌ Manual no cliente | ⚠️ RRF requer licença Enterprise |
| RAM mínima (13.5M×1024) | **~24-32 GB** (scalar quant + mmap) | ~32-48 GB (DiskANN) | ~48-64 GB (int4/BBQ) |
| Cliente Rust | ✅ Oficial gRPC (v1.16.0) | ✅ pgvector-rust + sqlx | ⚠️ elasticsearch-rs (REST) |
| Filtros + vetores | ✅ ACORN, query planner | ✅ Iterative scan (v0.8.0) | ✅ Pre-filtering HNSW |
| Complexidade operacional | Baixa (Docker single-node) | Média (PG tuning) | Alta (JVM, cluster config) |
| Custo licenciamento | Open source (Apache 2.0) | Open source | ⚠️ RRF requer licença paga |

A recomendação é clara: **Qdrant** para busca híbrida dense+sparse com BGE-M3 em produção, com a menor barreira de RAM, melhor integração Rust, e funcionalidade híbrida mais completa sem custos de licenciamento.
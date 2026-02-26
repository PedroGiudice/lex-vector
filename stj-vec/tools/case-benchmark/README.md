# Case Knowledge Benchmark

Medir tempo e custo de embedding via Modal GPU (H200 + TEI bge-m3).

## Passo a passo

### 1. Chunkificar o arquivo e exportar JSONL

```bash
python3 tools/case-benchmark/01_chunk_export.py \
  /tmp/integra_teste.md \
  /tmp/case-bench/chunks.jsonl
```

Output: numero de chunks, tamanho medio, arquivo JSONL.

### 2. Upload JSONL pro Modal Volume

```bash
modal volume put case-knowledge-data /tmp/case-bench/chunks.jsonl chunks/
```

### 3. Embedar no Modal (H200)

```bash
cd /home/opc/lex-vector/stj-vec
modal run tools/case-benchmark/02_modal_embed.py --source chunks
```

Output: tempo de embedding (GPU), tempo total (incl. cold start), custo estimado.

### 4. Download dos embeddings

```bash
modal volume get case-knowledge-data embeddings/ /tmp/case-bench/embeddings/
```

### 5. (Opcional) Importar no knowledge.db pra testar qualidade de busca

```bash
# Primeiro criar um caso de teste com case-ingest (so chunkifica, sem embedar)
# Depois importar os embeddings do Modal:
python3 tools/case-benchmark/03_import_embeddings.py \
  --input /tmp/case-bench/embeddings \
  --db /path/to/knowledge.db
```

## O que medir

- **Step 1**: tempo de chunking (deve ser <1s)
- **Step 3**: tempo total e custo. Expectativa pra ~650 chunks:
  - Cold start H200: ~30-60s
  - Embedding GPU: ~2-5s
  - Total: ~60s
  - Custo: ~$0.08

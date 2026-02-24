# Execucao: stj-vec Embedding Pipeline (Dense + Sparse)

## Contexto rapido

stj-vec: busca vetorial sobre jurisprudencia STJ. Cargo workspace Rust em `/home/opc/lex-vector/stj-vec/`, 3 crates (core, ingest, server) + scripts Modal Python. Scan e chunk completos: **857 sources, 2.1M documentos, 13.5M chunks** em SQLite (31GB em `db/stj-vec.db`). 27 testes passando.

Design aprovado: BGE-M3 com **dense + sparse** via Modal L4, storage unificado em SQLite, busca hibrida com fusao automatica. Design doc: `docs/design-docs/2026-02-24-stj-vec-embedding-pipeline.md`.

## Arquivos principais

- `stj-vec/modal/embed.py` -- Modal Class, atualmente usa sentence-transformers e so dense. **Precisa reescrever pra FlagEmbedding com dense + sparse.**
- `stj-vec/modal/download_model.py` -- modelo BGE-M3 ja no Volume `stj-vec-models`
- `stj-vec/crates/core/src/storage.rs` -- schema SQLite. **Precisa adicionar tabela sparse_chunks.**
- `stj-vec/crates/ingest/src/importer.rs` -- importa .npz. **Precisa adicionar import de .sparse.json.**
- `stj-vec/crates/ingest/src/exporter.rs` -- exporta chunks pra JSONL. Sem mudancas.
- `stj-vec/crates/ingest/src/main.rs` -- CLI clap. Sem mudancas no subcomando.
- `stj-vec/crates/server/src/routes.rs` -- rota /search. **Precisa implementar busca hibrida.**
- `stj-vec/config.toml` -- dim=1024, provider=modal. **Adicionar peso hibrido.**

## Passos (executar em ordem)

### 1. Reescrever embed.py para FlagEmbedding (dense + sparse)

Trocar `sentence-transformers` por `FlagEmbedding` na image Modal. A API:

```python
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("/models/bge-m3", use_fp16=True)
result = model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=False)
# result['dense_vecs']: np.ndarray (N, 1024)
# result['lexical_weights']: list[dict] -- [{token_id: weight}, ...]
```

Output por source:
- `{source}.npz` -- dense (como antes)
- `{source}.sparse.json` -- lista de dicts sparse, alinhada com chunk_ids
- `{source}.json` -- chunk_ids (como antes)

Atencao: `lexical_weights` retorna token_ids numericos. Precisa converter pra tokens de texto usando o tokenizer (`model.tokenizer.decode([token_id])`), porque o Rust precisa dos tokens como strings pra busca.

GPU: `gpu="L4"` (ja configurado).

**Verificar:** `modal run embed.py --source 202203` com 3 chunks de teste. Checar que gera os 3 arquivos e que sparse.json tem dicts com tokens texto.

### 2. Testar embed.py com source de teste no Modal

```bash
cd /home/opc/lex-vector/stj-vec
# Garantir que chunks de teste estao no Volume
modal volume ls stj-vec-data /chunks/
# Rodar embedding de 1 source
modal run modal/embed.py --source test
# Verificar output
modal volume ls stj-vec-data /embeddings/
```

Checar: `test.npz` (dense), `test.sparse.json` (sparse), `test.json` (ids).

### 3. Adicionar tabela sparse_chunks no storage.rs

Em `SCHEMA_SQL`:

```sql
CREATE TABLE IF NOT EXISTS sparse_chunks (
    chunk_id TEXT NOT NULL,
    token TEXT NOT NULL,
    weight REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sparse_token ON sparse_chunks(token);
CREATE INDEX IF NOT EXISTS idx_sparse_chunk ON sparse_chunks(chunk_id);
```

Adicionar metodos:
- `insert_sparse_batch(chunk_id, tokens: Vec<(String, f32)>)` -- batch insert numa transacao
- `search_sparse(query_tokens: HashMap<String, f32>, limit: usize) -> Vec<(String, f32)>` -- retorna chunk_ids com score sparse

**Verificar:** testes unitarios pra insert e search sparse.

### 4. Adaptar importer.rs para .sparse.json

Alem de ler `.npz`, ler `{source}.sparse.json` (Vec<HashMap<String, f32>>) e inserir na tabela sparse_chunks. Batch insert com transacao (13.5M chunks x ~100-200 tokens cada = muitas rows).

Considerar filtro de peso minimo (ex: descartar tokens com weight < 0.01) pra reduzir tamanho da tabela.

**Verificar:** importar embeddings de teste e checar que sparse_chunks tem dados.

### 5. Export chunks e upload pro Modal Volume

```bash
cd /home/opc/lex-vector/stj-vec
cargo run --release -p stj-vec-ingest -- --config config.toml export-chunks --output /tmp/stj-vec-chunks
modal volume put stj-vec-data /tmp/stj-vec-chunks/ /chunks/ --force
```

Verificar: `modal volume ls stj-vec-data /chunks/ | wc -l` == 857.

**ATENCAO:** 13.5M chunks em JSONL pode ser grande (dezenas de GB). Se /tmp nao tiver espaco, usar outro diretorio. `df -h /tmp` antes.

### 6. Rodar embedding em massa no Modal

```bash
modal run modal/embed.py --all-pending
```

Isso usa `modal.map()` pra distribuir 857 sources em multiplos containers L4. Estimativa: 4-6h, $12-15.

**Este comando deve ser rodado no terminal independente (nohup ou tmux), nao via Claude Code.**

```bash
cd /home/opc/lex-vector/stj-vec
nohup modal run modal/embed.py --all-pending > /tmp/embedding.log 2>&1 &
tail -f /tmp/embedding.log
```

Verificar: `modal volume ls stj-vec-data /embeddings/ | wc -l` == 857 (ou 857*3 se contar .npz + .sparse.json + .json).

### 7. Download e import dos embeddings

```bash
modal volume get stj-vec-data /embeddings/ /tmp/stj-vec-embeddings/
cd /home/opc/lex-vector/stj-vec
nohup cargo run --release -p stj-vec-ingest -- --config config.toml import-embeddings --input /tmp/stj-vec-embeddings > /tmp/import.log 2>&1 &
```

**Import vai ser longo** -- 13.5M chunks x (dense + sparse). Rodar no terminal independente.

Verificar: `sqlite3 db/stj-vec.db "SELECT count(*) FROM vec_chunks; SELECT count(DISTINCT chunk_id) FROM sparse_chunks;"`

### 8. Implementar busca hibrida no server

Adaptar `POST /search`:
1. Encode query -> dense_vec + sparse_dict
2. Busca dense: vec_chunks cosine similarity -> top K
3. Busca sparse: sparse_chunks token match -> score por chunk
4. Fusao: `score = w * dense + (1-w) * sparse` (w de config.toml)
5. Retorna top N

Adicionar em config.toml:
```toml
[search]
hybrid_weight = 0.7  # peso do dense (1.0 = so dense, 0.0 = so sparse)
```

**Verificar:** smoke test com queries reais: "progressao funcional servidor", "art. 1.022 CPC", "recurso especial provido".

### 9. (Fase 2) Re-ranker

Apos pipeline base funcional:
- Baixar Serafim 335M via `huggingface-cli download`
- Implementar re-ranker em Python (script ou microservico) ou Rust (candle/ort)
- Integrar no server como estagio pos-fusao
- Configuravel em config.toml

## Verificacao de estado

```bash
cd /home/opc/lex-vector/stj-vec

# Testes
cargo test --workspace

# Stats (pode ser lento com DB grande -- usar sqlite3 direto)
sqlite3 db/stj-vec.db "SELECT count(*) FROM documents; SELECT count(*) FROM chunks; SELECT count(*) FROM vec_chunks; SELECT count(DISTINCT chunk_id) FROM sparse_chunks;"

# Modal
modal volume ls stj-vec-models   # bge-m3/
modal volume ls stj-vec-data     # chunks/, embeddings/
modal profile current            # pedrogiudice

# Disco
df -h /tmp
du -sh db/stj-vec.db
```

## Nota sobre custo

Budget Modal: $30/mes. Estimativa deste run: $12-15 com 4x L4. Sobra margem pra re-runs parciais se algo falhar. O `--all-pending` so processa sources sem embeddings, entao e seguro re-rodar se interromper.

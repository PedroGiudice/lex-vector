# Retomada: Migracao stj-vec para Storage VPS + Importacao de Sparse Embeddings

## Contexto rapido

O stj-vec e o sistema de busca vetorial de jurisprudencia STJ (Rust, sqlite-vec, axum). O DB tem 52GB (2.1M docs, 13.5M chunks, 5.27M dense embeddings). A VM dev (Contabo, 193GB NVMe) esta sem espaco para importar os sparse embeddings (41.6GB no Modal Volume). Decisao: migrar stj-vec para um Storage VPS dedicado (Contabo, 400GB SSD, $8/mes).

O Storage VPS ja esta provisionado:
- **IP:** 84.247.165.172
- **IPv6:** 2a02:c207:2312:5349::1/64
- **User:** root
- **OS:** Ubuntu (recem-provisionado, limpo)
- **Disco:** 400GB SSD, 3 cores, 8GB RAM

Os sparse embeddings do BGE-M3 (852 sources, 41.6GB) estao no Modal Volume `stj-vec-data` como `.sparse.json` e DEVEM ser importados -- FTS5/BM25 nao basta para jurisprudencia. Nao existe tabela de sparse no schema atual do SQLite.

## Arquivos principais

- `stj-vec/` -- workspace Rust (crates: core, ingest, server, case-ingest)
- `stj-vec/db/stj-vec.db` -- banco SQLite (52GB) com docs, chunks, FTS5, vec_chunks
- `stj-vec/modal/embed_hybrid.py` -- script Modal que gerou os sparse embeddings
- `stj-vec/modal/embed.py` -- script Modal para dense embeddings (TEI + H200)
- `stj-vec/scripts/import_embeddings.py` -- importador Python (dense, .npz -> vec_chunks)
- `stj-vec/crates/core/src/storage.rs` -- schema e queries do SQLite
- `stj-vec/config.toml` -- config do sistema (paths, embedding, server)
- `~/.config/rclone/rclone.conf` -- config rclone (remote `contabo`, bucket `opc-data`)
- `docs/contexto/04032026-stj-vec-storage-migration.md` -- contexto detalhado desta sessao

## Proximos passos (por prioridade)

### 1. Configurar Storage VPS

**Onde:** Storage VPS (84.247.165.172)
**O que:**
- SSH como root, criar usuario `opc`, configurar authorized_keys
- Instalar Tailscale (`curl -fsSL https://tailscale.com/install.sh | sh && tailscale up`)
- Instalar dependencias: `build-essential`, `pkg-config`, `libssl-dev`, Rust toolchain
- Instalar Python 3.11+, uv, numpy, sqlite-vec (para script de import)
**Por que:** Precisa estar acessivel via Tailscale e ter ferramentas para rodar o stj-vec
**Verificar:** `ssh opc@<tailscale-ip>` funciona da VM dev

### 2. Migrar stj-vec para o Storage VPS

**Onde:** VM dev -> Storage VPS via rsync/Tailscale
**O que:**
- rsync do DB: `rsync -avP /home/opc/lex-vector/stj-vec/db/stj-vec.db opc@<tailscale-ip>:/home/opc/stj-vec/db/`
- rsync dos fontes: `rsync -avP /home/opc/lex-vector/stj-vec/{crates,scripts,modal,config.toml,Cargo.toml,Cargo.lock} opc@<tailscale-ip>:/home/opc/stj-vec/`
- Compilar no Storage VPS: `cd /home/opc/stj-vec && cargo build --release`
- Atualizar `config.toml` com novos paths
**Por que:** Liberar 52GB na VM dev e ter espaco para sparse no Storage VPS
**Verificar:** `cargo test -- --test-threads=1` no Storage VPS

### 3. Baixar sparse embeddings do Modal para o Storage VPS

**Onde:** Storage VPS
**O que:**
- Instalar Modal CLI: `uv pip install modal && modal setup`
- Baixar sparse: `modal volume get stj-vec-data embeddings/*.sparse.json /home/opc/stj-vec/embeddings/`
- Baixar IDs: `modal volume get stj-vec-data embeddings/*.json /home/opc/stj-vec/embeddings/` (excluir .sparse.json)
**Por que:** Sparse embeddings custaram GPU (H200) para gerar, sao necessarios para busca hibrida de qualidade
**Verificar:** `ls /home/opc/stj-vec/embeddings/*.sparse.json | wc -l` == 852

### 4. Criar schema e importador para sparse embeddings

**Onde:** `stj-vec/crates/core/src/storage.rs` e novo script Python
**O que:**
- Definir tabela para sparse weights. Opcoes:
  - Tabela `sparse_chunks (chunk_id TEXT PK, weights BLOB)` com weights serializados como binario compacto
  - Ou integrar com FTS5 customizado (mais complexo, melhor performance de query)
- Criar script `scripts/import_sparse.py` analogo ao `import_embeddings.py`
- O formato sparse e `[{token_id: weight, ...}, ...]` por source
**Por que:** Nao existe tabela de sparse no schema atual
**Verificar:** `SELECT COUNT(*) FROM sparse_chunks` apos import

### 5. Gerar 6 sources faltantes de dense embeddings

**Onde:** Modal (`embed.py`)
**O que:** `modal run modal/embed.py --source 20221230` (e os outros 5: 20240110, 20240115, 20251020, 20260126, 20260205)
**Por que:** 6 de 858 sources nao tem dense embedding
**Verificar:** `modal volume ls stj-vec-data embeddings/ | grep -c ".npz"` == 858

### 6. Resolver mismatch de IDs entre chunks e vec_chunks

**Onde:** `stj-vec/crates/core/src/storage.rs`
**O que:** Investigar o formato de chunk_id em cada tabela. `chunks.id` usa um formato, `vec_chunks.chunk_id` usa outro. O JOIN entre eles retorna zero matches. Pode ser prefixo de source (ex: `202203_0001`) vs hash. Corrigir ou criar mapeamento.
**Por que:** Sem isso, nao da para correlacionar embedding com texto do chunk
**Verificar:** `SELECT COUNT(*) FROM chunks c JOIN vec_chunks_rowids v ON c.id = v.chunk_id` > 0

### 7. Otimizar queries de busca

**Onde:** `stj-vec/crates/core/src/storage.rs` e `stj-vec/crates/server/src/routes.rs`
**O que:** Implementar busca hibrida (dense + sparse + FTS5 com RRF fusion). Otimizar para latencia < 500ms em 5.27M vetores. Considerar pre-filtering por metadata (data, ministro, classe).
**Por que:** Objetivo final -- busca vetorial de qualidade para jurisprudencia STJ
**Verificar:** Query de teste retorna resultados relevantes em < 500ms

## Dados importantes

### Modal Volume `stj-vec-data`

```
chunks/     -- 858 arquivos JSONL (1 por source/mes)
embeddings/ -- 852 .npz (dense), 852 .sparse.json, 844 .json (IDs)
```

### Object Storage Contabo (rclone)

```ini
# ~/.config/rclone/rclone.conf
[contabo]
type = s3
provider = Other
access_key_id = 3f76c0c1c0484052c0b6eecc580cad50
secret_access_key = 26a187fd69c445efd38dedefdd2ac1fc
endpoint = https://eu2.contabostorage.com
```

Bucket `opc-data`: 10.57GB usado de 250GB. Tem parte dos integras do STJ.

### DB Schema relevante

```sql
-- vec_chunks (dense embeddings, sqlite-vec)
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id TEXT PRIMARY KEY,
    embedding float[1024] distance_metric=cosine
);

-- chunks_fts (BM25 sparse, FTS5)
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    chunk_id UNINDEXED, content,
    tokenize='unicode61 remove_diacritics 2'
);

-- Tabela de sparse embeddings: NAO EXISTE, precisa criar
```

## Como verificar

```bash
# Verificar DB intacto
sqlite3 /home/opc/lex-vector/stj-vec/db/stj-vec.db "SELECT COUNT(*) FROM documents;"
# Esperado: 2147015

# Verificar embeddings no Modal
modal volume ls stj-vec-data embeddings/ | wc -l
# Esperado: 2548

# Verificar rclone
rclone ls contabo:opc-data/ | head -5

# Verificar Tailscale
tailscale status

# Verificar espaco
df -h /home/opc/
```

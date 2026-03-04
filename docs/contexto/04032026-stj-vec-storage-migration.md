# Contexto: stj-vec Storage e Migracao para VPS Storage

**Data:** 2026-03-04
**Sessao:** stj-vec-continue
**Duracao:** ~3h (investigacao, analise, decisao)

---

## O que foi feito

### 1. Levantamento completo do estado do stj-vec

Inventario do DB (`db/stj-vec.db`, 52GB):

| Tabela | Quantidade |
|--------|-----------|
| documents | 2,147,015 |
| chunks | 13,485,051 |
| chunks_fts (FTS5/BM25) | populada |
| vec_chunks (dense embeddings) | 5,269,603 |
| ingest_log (sources) | 857 |

Descoberta critica: os IDs em `vec_chunks` nao correspondem aos IDs em `chunks`. A query `chunks.id NOT IN vec_chunks_rowids.chunk_id` retorna 13.5M (todos). Formato de ID diferente entre as tabelas.

### 2. Estado dos embeddings no Modal Volume (`stj-vec-data`)

| Tipo | Arquivos | Tamanho |
|------|----------|---------|
| chunks (.jsonl) | 858 | - |
| NPZ (dense) | 852 | 38.6 GB |
| Sparse JSON (lexical weights BGE-M3) | 852 | 41.6 GB |
| ID JSON | 844 | 0.4 GB |
| **Total** | **2548** | **80.7 GB** |

6 sources sem embedding dense: `20221230`, `20240110`, `20240115`, `20251020`, `20260126`, `20260205`.

Sparse embeddings: **852/858 sources gerados, zero importados no DB.** Nao existe tabela de sparse no schema atual.

### 3. Analise de disco e decisao de infraestrutura

VM Contabo atual (193GB NVMe):

| Dir | Tamanho |
|-----|---------|
| /home | 151GB |
| /var (Docker) | 14GB |
| /usr | 12GB |
| /tmp | 12GB |

Dentro de /home:

| Dir | Tamanho |
|-----|---------|
| stj-vec DB | 52GB |
| juridico-data/stj | 33GB |
| ELCO-machina | 23GB |
| legal-workbench | 11GB |
| Resto | ~30GB |

Targets limpos nesta sessao: stj-vec/target (4.8GB), ELCO-machina/src-tauri/target (6.2GB), ccui-backend/target (1.4GB) = **+12.4GB liberados**.

### 4. Object Storage Contabo

Descoberto rclone configurado em `~/.config/rclone/rclone.conf`:

```ini
[contabo]
type = s3
provider = Other
access_key_id = 3f76c0c1c0484052c0b6eecc580cad50
secret_access_key = 26a187fd69c445efd38dedefdd2ac1fc
endpoint = https://eu2.contabostorage.com
acl = private
```

Bucket: `opc-data` (10.57GB de 250GB usados, ~137k objetos). Ja tem parte dos dados juridicos.

Sync parcial dos integras foi iniciado e cancelado (decisao mudou para Storage VPS).

### 5. Cogmem zerado

O `cogmem.db` foi recriado vazio em 2026-03-04 10:38:26 (causa desconhecida). Perda total do historico de sessoes. Resolvido em sessao paralela: o DB real e `context_memory.db` (3206 chunks intactos), paths corrigidos nos agents/skills.

## Decisoes tomadas

- **Storage VPS de $8/mes (3c/8GB/400GB SSD)**: melhor custo-beneficio para resolver o problema de disco. stj-vec migra para la inteiro (DB + binarios + server axum). VM atual fica para dev.
- **Sparse embeddings sao necessarios**: FTS5/BM25 nao basta para jurisprudencia. Os 41.6GB de sparse DEVEM ser importados (custaram GPU para gerar).
- **Nao migrar para VM unica de $26**: apesar de simples, centralizar nao e necessario quando o gargalo e especifico (stj-vec storage).
- **Ubuntu 24.04 LTS** para o Storage VPS: mesma versao da VM atual.

## Pendencias identificadas

1. **Provisionar Storage VPS** (em andamento) -- usuario fez o pedido, aguardando provisionamento
2. **Configurar Tailscale** no Storage VPS -- para conectividade com a VM dev
3. **Migrar stj-vec** -- rsync do DB (52GB) + binarios + configs
4. **Baixar embeddings do Modal** -- 852 npz (38.6GB dense, ja importados) + 852 sparse.json (41.6GB, pendentes)
5. **Criar schema de sparse** -- tabela nova no SQLite para lexical weights do BGE-M3
6. **Importar sparse embeddings** no DB
7. **Gerar 6 sources faltantes** -- dense embeddings para 20221230, 20240110, 20240115, 20251020, 20260126, 20260205
8. **Resolver mismatch de IDs** -- chunks.id vs vec_chunks.chunk_id usam formatos diferentes
9. **Otimizar queries** -- objetivo original da sessao, adiado por falta de espaco

## Docker rodando na VM atual

| Container | Imagem | Uso |
|-----------|--------|-----|
| tei | text-embeddings-inference:cpu-1.6 | Embeddings para cogmem/queries |
| penpot (5 containers) | frontend, backend, exporter, postgres, valkey | Design tool |
| mailcatcher | sj26/mailcatcher | Penpot dev |

Imagens Docker consomem ~5.5GB, overlay2 ~11GB. Considerar mover Penpot para o Storage VPS se disco continuar apertado.

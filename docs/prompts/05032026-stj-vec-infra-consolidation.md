# Retomada: stj-vec Infra Consolidada + Proximos Passos

## Contexto rapido

VM dev foi upgradada para Cloud VPS 50 (64GB RAM, 16 cores, 600GB NVMe, $46/mes). Todos os dados do stj-vec foram consolidados nela: DB de 52GB (2.1M docs, 13.5M chunks) e embeddings completos (852 dense + 852 sparse + 844 IDs = 81GB). Storage VPS temporario (84.247.165.172) pode ser cancelado -- dados verificados byte a byte.

Decisao arquitetural: **Qdrant** para busca hibrida (dense HNSW + sparse inverted + RRF server-side). SQLite mantido para metadados. Com mmap agressivo, RAM nao e o bottleneck -- IOPS do disco e.

Tres sistemas de embeddings foram identificados: stj-vec (52GB+81GB), legal-knowledge-base (2.1GB, ChromaDB desatualizado), cogmem (28MB). O Case Knowledge System foi desenhado (`~/.claude/docs/design-docs/2026-02-24-case-knowledge-system.md`) mas nunca implementado.

Visao futura: MCP unificado com custom tools para todas as bases, tudo num plugin.

## Arquivos principais

- `stj-vec/db/stj-vec.db` -- DB principal (52GB, 2.1M docs, 13.5M chunks)
- `stj-vec/embeddings/` -- 2548 arquivos (852 dense .npz + 852 sparse .sparse.json + 844 IDs .json)
- `docs/busca-hibrida-SQL` -- pesquisa completa sobre opcoes de busca hibrida
- `Minimal-RAM-1M.md` -- artigo Qdrant sobre RAM minimo com mmap
- `docs/contexto/05032026-stj-vec-infra-consolidation.md` -- contexto detalhado desta sessao
- `~/.claude/docs/design-docs/2026-02-24-case-knowledge-system.md` -- design do Case Knowledge (nao implementado)
- `~/.claude/docs/design-docs/2026-02-24-shared-knowledge-system.md` -- design da migracao legal-knowledge

## Proximos passos (por prioridade)

### 1. Resolver mismatch de IDs (CRITICO)
**Onde:** `stj-vec/db/stj-vec.db` -- tabelas `chunks` e `vec_chunks`
**O que:** chunks.id e vec_chunks.chunk_id usam formatos diferentes. JOIN retorna zero rows. Sem isso, nenhuma busca funciona.
**Por que:** Bloqueia qualquer uso pratico do sistema de busca
**Verificar:** `sqlite3 stj-vec/db/stj-vec.db "SELECT c.id, v.chunk_id FROM chunks c JOIN vec_chunks v ON c.id = v.chunk_id LIMIT 5;"` -- deve retornar rows

### 2. Instalar e configurar Qdrant
**Onde:** VM dev (Docker)
**O que:** `docker run -p 6333:6333 -p 6334:6334 -v /home/opc/qdrant-data:/qdrant/storage qdrant/qdrant:latest`. Criar collection com named vectors (dense 1024d cosine on_disk + sparse com IDF). Configurar quantizacao escalar + mmap.
**Por que:** Decisao tomada -- Qdrant e o motor de busca hibrida
**Verificar:** `curl http://localhost:6333/collections` deve listar a collection

### 3. Importar embeddings no Qdrant
**Onde:** Criar script Python ou Rust que le os .npz (dense) e .sparse.json (sparse) e faz upsert no Qdrant
**O que:** 13.5M pontos com dense vector (1024d) + sparse vector + payload (doc_id, source_date, etc)
**Por que:** Os embeddings estao em arquivos brutos, precisam ser indexados
**Verificar:** `curl http://localhost:6333/collections/stj/points/count` deve retornar ~5.27M (dense existentes) crescendo ate 13.5M

### 4. Implementar Case Knowledge System
**Onde:** Design doc em `~/.claude/docs/design-docs/2026-02-24-case-knowledge-system.md`
**O que:** Cada caso = pasta com `base/` (docs) + `knowledge.db` (sqlite-vec). Embedding via bge-m3. Agentes operam sobre o conhecimento do caso.
**Por que:** Necessario para workflow juridico completo. Prototipo em `/home/opc/casos/teste-escritorio/` esta vazio.

### 5. Migrar legal-knowledge-base
**Onde:** `~/.claude/legal-knowledge-base/` (ChromaDB + text-embedding-004 768d)
**O que:** Migrar para sqlite-vec + bge-m3 1024d, alinhando com stack stj-vec/cogmem
**Por que:** Stack inconsistente (3 engines de embedding diferentes)

### 6. Cancelar Storage VPS
**Onde:** Painel Contabo
**O que:** Cancelar VPS 84.247.165.172 ($8/mes). Dados ja verificados byte a byte na VM consolidada.
**Verificar:** `ssh opc@84.247.165.172` deve falhar apos cancelamento

## Como verificar

```bash
# VM specs
free -h  # 62GB total
df -h /  # 581GB total, ~327GB livres
nproc    # 16

# DB integro
sqlite3 stj-vec/db/stj-vec.db "SELECT COUNT(*) FROM documents;"  # 2147015
sqlite3 stj-vec/db/stj-vec.db "SELECT COUNT(*) FROM chunks;"     # 13485051

# Embeddings completos
ls stj-vec/embeddings/*.npz | wc -l          # 852
ls stj-vec/embeddings/*.sparse.json | wc -l  # 852
ls stj-vec/embeddings/*.json | grep -v sparse | wc -l  # 844

# Servicos
curl http://localhost:8080/health   # TEI OK
curl http://localhost:3939/health   # cogmem OK
curl http://localhost:11434/api/version  # ollama OK
docker ps  # Penpot containers
```

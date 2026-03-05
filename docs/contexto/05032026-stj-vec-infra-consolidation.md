# Contexto: Consolidacao de Infraestrutura e Migracao stj-vec

**Data:** 2026-03-05
**Sessao:** stj-vec-continue (branch main)
**Duracao:** ~4h

---

## O que foi feito

### 1. Provisionamento e Configuracao do Storage VPS

Storage VPS Contabo (84.247.165.172, 3 cores, 8GB RAM, 400GB SSD, $8/mes) foi configurado:
- Usuario `opc` com sudo NOPASSWD e chave SSH
- Tailscale instalado e autenticado (hostname: `stj-vec-storage`, IP: 100.92.50.33)
- Rust toolchain 1.93.1 instalado
- Modal CLI configurado em venv (`/home/opc/.venv/bin/modal`)
- stj-vec compilado com `cargo build --release`

### 2. Transferencia do stj-vec para Storage VPS

**DB (52GB):** transferido via `tar cf - | ssh | tar xf -` (gzip). rsync foi tentado primeiro mas a ~150KB/s era inviavel (~100h). tar over SSH atingiu ~460-530MB/min.

**Embeddings (81GB, 2548 files):** baixados diretamente do Modal Volume `stj-vec-data` no Storage VPS via `modal volume get stj-vec-data embeddings/ /home/opc/stj-vec/`. Completou todos os 852 sparse + 852 dense + 844 IDs.

### 3. Pesquisa e Decisoes de Arquitetura (Busca Hibrida)

Documento de pesquisa `docs/busca-hibrida-SQL` analisa opcoes para busca hibrida em 13.5M chunks:

- **Decisao: Qdrant** como motor de busca vetorial (dense HNSW + sparse inverted index + RRF server-side)
- **SQLite mantido** para metadados (docs, chunks, FTS5)
- **Opcao C confirmada:** dense retrieval primeiro (HNSW top-K), sparse reranking nos candidatos

Artigo da Qdrant (`Minimal-RAM-1M.md`) demonstrou que com mmap agressivo (vetores + HNSW on_disk), o consumo de RAM e drasticamente menor (~135MB para 1M vetores 100d). **O fator dominante e IOPS do disco, nao RAM.**

### 4. Upgrade da VM Dev: Cloud VPS 30 -> Cloud VPS 50

- **Specs novas:** 16 vCPU, 64GB RAM, 600GB NVMe (particionado para 581GB)
- **Custo:** $46/mes
- **IP mantido** (live migration)
- Particao expandida de 199GB -> 581GB via `growpart + resize2fs`
- Todos os servicos restaurados (TEI, cogmem, ollama, Docker/Penpot)
- Whisper desabilitado (nao necessario)

### 5. Transferencia dos dados de volta (Storage VPS -> VM consolidada)

Apos o upgrade, todos os dados foram trazidos de volta:
- **DB:** 52GB (55,405,920,256 bytes) -- verificado byte a byte
- **Embeddings:** 81GB (86,597,304,593 bytes), 2548 files -- verificado byte a byte
- Storage VPS pode ser cancelado

### 6. Limpeza do repositorio

- Removido `adk-agents/` (movido para repo proprio) -- 54 files deletados
- Commitados `Minimal-RAM-1M.md` e `docs/busca-hibrida-SQL`
- Erros aprendidos adicionados ao CLAUDE.md

### 7. Identificacao dos 3 Sistemas de Embeddings

| Sistema | Local | Escopo | Tamanho |
|---------|-------|--------|---------|
| **stj-vec** | `stj-vec/db/stj-vec.db` | 2.1M decisoes STJ, 13.5M chunks | 52GB DB + 81GB embeddings |
| **legal-knowledge-base** | `~/.claude/legal-knowledge-base/` | 15,268 docs legislacao/doutrina | 2.1GB (ChromaDB + legal-vec.db) |
| **cogmem** | `~/.claude/context_memory.db` | 3,327 chunks de sessoes Claude | 28MB |

**Ausente: case-docs** (`/home/opc/casos/teste-escritorio/`) -- prototipo vazio. Design docs existem em:
- `~/.claude/docs/design-docs/2026-02-24-case-knowledge-system.md`
- `~/.claude/docs/design-docs/2026-02-24-shared-knowledge-system.md`

O Case Knowledge System foi desenhado mas nunca implementado. Conceito: cada caso juridico = pasta com `base/` (docs embedados) + `knowledge.db` (sqlite-vec local). Agentes operam sobre esse conhecimento.

O Shared Legal Knowledge System (`legal-knowledge-base`) precisa migrar de ChromaDB + text-embedding-004 para sqlite-vec + bge-m3 para alinhar com o stack.

## Estado dos arquivos

| Arquivo | Status |
|---------|--------|
| `CLAUDE.md` | Modificado -- erros aprendidos (WebSearch antes de estimar) |
| `~/.claude/CLAUDE.md` | Modificado -- regra de limpeza de processos, WebSearch |
| `docs/busca-hibrida-SQL` | Criado -- pesquisa completa Qdrant vs pgvector vs ES |
| `Minimal-RAM-1M.md` | Criado -- artigo Qdrant sobre RAM minimo |
| `stj-vec/db/stj-vec.db` | Transferido (52GB) |
| `stj-vec/embeddings/` | Transferido (81GB, 2548 files) |

## Commits desta sessao

```
9159874 docs: erros aprendidos - WebSearch antes de estimar sizing
d293f6f chore: persist pending changes (serena, embed_hybrid, vibma screenshot)
297e305 chore: remove adk-agents (movido para repo proprio)
```

## Pendencias identificadas

1. **Mismatch de IDs (CRITICO)** -- chunks.id e vec_chunks.chunk_id usam formatos diferentes (JOIN retorna zero). Impede qualquer busca funcional. Investigar e resolver antes de qualquer outra coisa.
2. **Schema sparse + importacao no Qdrant** -- decidido usar Qdrant, mas nao instalado nem configurado. 852 arquivos sparse prontos para importar.
3. **Case Knowledge System nao implementado** -- design doc aprovado mas zero codigo. Necessario para workflow juridico completo.
4. **legal-knowledge-base migracao** -- ChromaDB -> sqlite-vec + bge-m3 (alinhar stack)
5. **6 sources sem dense embeddings** -- 20221230, 20240110, 20240115, 20251020, 20260126, 20260205
6. **Cancelar Storage VPS** -- dados migrados, $8/mes para economizar
7. **MCP unificado para bases de dados** -- visao: 1 MCP server com custom tools para stj-vec, legal-knowledge, case-docs, tudo num plugin

## Decisoes tomadas

- **Qdrant para busca hibrida:** suporta dense+sparse nativamente, RRF server-side, cliente Rust oficial, mmap para baixo consumo de RAM
- **RAM nao e bottleneck, IOPS do disco e:** artigo Qdrant prova que com mmap, 1M vetores 100d precisam de apenas 135MB RAM. Fator dominante e random reads do disco.
- **Consolidar tudo numa VM:** upgrade para Cloud VPS 50 ($46, 64GB RAM, 600GB NVMe). Storage VPS temporario sera cancelado.
- **tar over SSH para transferencias grandes:** rsync era inviavel (~150KB/s entre VMs Contabo). tar pipe SSH atingiu ~700MB/min.
- **WebSearch antes de estimar recursos:** erro repetido de sizing teorico. Adicionado como regra no CLAUDE.md.

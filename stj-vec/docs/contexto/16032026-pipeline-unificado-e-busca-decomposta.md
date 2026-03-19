# Contexto: Pipeline Rust Unificado + Base Atualizada + Busca Decomposta

**Data:** 2026-03-16
**Branch:** main (22 commits ahead of origin, nao pushados)
**Duracao:** ~4 horas

---

## O que foi feito

### 1. Pipeline Rust unificado (download + extract + enrich + update)

Implementacao completa das Fases 2+3 do pipeline de ingestao. Antes tinhamos scripts Python separados; agora tudo roda via `stj-vec-ingest` (Rust, release binary).

Subcomandos CLI:
- `download --source <integras|espelhos|all>` -- cliente CKAN com manifest incremental, retry com backoff exponencial
- `extract` -- descompacta ZIPs baixados
- `enrich` -- cruza espelhos de acordaos com documentos (classe, orgao, data_julgamento, ministro)
- `update` -- orquestra download + extract + scan + chunk + enrich
- `export-chunks` -- exporta chunks para JSONL (consumido pelo Modal)

Modulos novos: `download.rs` (509 linhas), `unzip.rs` (264 linhas).

### 2. Chunker section-aware

O chunker antigo dividia por tamanho fixo (512 tokens), misturando EMENTA com VOTO no mesmo chunk. O novo detecta headers de secao e forca quebra de chunk em fronteira de secao, sem overlap entre secoes.

Headers reconhecidos: EMENTA, ACORDAO, RELATORIO, VOTO, DECISAO, DECIDO, e formato numerado (I. CASO EM EXAME, II. QUESTAO EM DISCUSSAO, etc.).

Arquivo: `crates/core/src/chunker.rs` -- funcao `is_section_header()` + logica `section_break` no loop de acumulacao.

### 3. Indice processo_digits + otimizacao do enrich

Antes: `find_documents_by_processo_digits()` fazia full-scan de 2.1M rows extraindo digitos em Rust. Enrich de 460 espelhos levava >10 minutos sem terminar.

Agora: coluna `processo_digits` (pre-computada, somente digitos) com indice B-tree. Query vira `WHERE processo_digits = ?1`. Enrich dos 460 espelhos: **18 segundos**.

Schema: `ALTER TABLE documents ADD COLUMN processo_digits TEXT` + `CREATE INDEX idx_documents_processo_digits`.

### 4. Base de dados atualizada ate 2026-03-13

Pipeline completo executado nesta sessao:

| Etapa | Resultado |
|-------|-----------|
| Download espelhos | 471 JSONs de 10 datasets CKAN |
| Download integras | 109 novos (1715 pulados via manifest) |
| Extract ZIPs | 63.949 textos extraidos |
| Scan | 16 novos sources detectados |
| Chunk | ~28.600 novos chunks (section-aware) |
| Enrich | 115.012 matches, 169.556 campos atualizados |
| Embeddings (Modal GPU) | 23.862 embeddings (20 sources, L4 GPU, 102 emb/s) |
| Import Qdrant | 28.608 pontos em 5s |

### 5. Pagina de inteiro teor do documento (Laravel)

View Blade `search/document.blade.php` que mostra o acordao completo (metadados + todos os chunks concatenados). Antes, resultados mostravam apenas o snippet do chunk.

Rotas: `/document/{docId}` (HTML) e `/api/document/{docId}` (JSON).
Links "Ver inteiro teor" adicionados em busca direta (JS) e decomposta (Livewire).

### 6. RRF score display corrigido

Thresholds errados (0.7/0.4) substituidos por faixas corretas para k=60 (0.025/0.015). Adicionada posicao de ranking (#1, #2...) antes do score numerico.

### 7. Prompt dual dense/sparse reforcado

Secao 4 do prompt do decomposer reescrita com exemplos lado a lado (formulaico vs semantico). Agora o modelo gera queries variadas que exploram ambos os canais de busca.

### 8. Remocao do crate server legado (sqlite-vec)

Crate `server/` removido (-328 linhas). `ServerConfig` e `default_threshold` removidos do core. O server ativo e `stj-vec-search` (crate `search`, Qdrant). Sem threshold por design -- top-K implicito.

### 9. Timer Alpine.js na busca decomposta

Timer que pulava de 3 em 3 segundos (wire:poll) substituido por Alpine.js `x-data` que conta a cada 1 segundo no client.

### 10. Deteccao de processo morto (EM ANDAMENTO)

Adicionado `isProcessDead()` via `posix_kill($pid, 0)` em AgentRunner e SdkAgentRunner. **Teste falhando** -- mock nao inclui o novo metodo. Precisa corrigir na proxima sessao.

---

## Estado dos arquivos

### Commitados (22 commits na main, nao pushados)

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `crates/ingest/src/download.rs` | Criado | Cliente CKAN, manifest, retry, streaming |
| `crates/ingest/src/unzip.rs` | Criado | Extracao ZIPs, copia metadados |
| `crates/ingest/src/pipeline.rs` | Modificado | +download(), +extract_pending(), +enrich(), +update() |
| `crates/ingest/src/main.rs` | Modificado | +subcomandos download, extract, enrich, update |
| `crates/ingest/src/lib.rs` | Modificado | +exports download, unzip |
| `crates/core/src/chunker.rs` | Modificado | +section-aware chunking, +is_section_header() |
| `crates/core/src/config.rs` | Modificado | -ServerConfig, -default_threshold, +downloads_dir |
| `crates/core/src/storage.rs` | Modificado | +processo_digits, query indexada |
| `crates/server/` | Deletado | Crate legado inteiro removido |
| `config.toml` | Modificado | -[server], +downloads_dir |
| `web/resources/views/search/document.blade.php` | Criado | View inteiro teor |
| `web/resources/views/search/index.blade.php` | Modificado | +links inteiro teor, +RRF corrigido |
| `web/resources/views/livewire/decomposed-search.blade.php` | Modificado | +RRF corrigido, +timer Alpine.js |
| `web/app/Http/Controllers/SearchController.php` | Modificado | document() renderiza Blade, +documentApi() |
| `web/routes/web.php` | Modificado | +rota /api/document/{docId} |
| `web/tests/Feature/SearchControllerTest.php` | Modificado | +4 testes (view, API, 404s) |
| `agent/prompts/decomposer.md` | Modificado | Secao 4 reescrita (dual dense/sparse) |
| `docs/plans/rust-unified-pipeline.md` | Criado | Plano das 3 fases |

### Nao commitados (pendentes)

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `web/app/Livewire/DecomposedSearch.php` | Modificado | +isProcessDead() call (teste falhando) |
| `web/app/Services/AgentRunnerInterface.php` | Modificado | +isProcessDead() na interface |
| `web/app/Services/AgentRunner.php` | Modificado | +isProcessDead() via posix_kill |
| `web/app/Services/SdkAgentRunner.php` | Modificado | +isProcessDead() via posix_kill |
| `stj-vec/Cargo.lock` | Modificado | Lock atualizado |
| `stj-vec/modal/embed_hybrid.py` | Modificado | Atualizado pelo usuario (fora desta sessao) |
| `~/.claude/agents/query-decomposer.md` | Modificado | Dual dense/sparse (fora do repo) |

---

## Commits desta sessao

```
a4bd8b8 fix(stj-vec-web): timer da busca decomposta atualiza a cada 1s via Alpine.js
52defe8 refactor(stj-vec): remove crate server legado (sqlite-vec) e ServerConfig/threshold
a39ae03 fix(stj-vec): RRF thresholds UI corrigidos + prompt dual dense/sparse reforcado
57bc869 fix(stj-vec): chunker section-aware + indice processo_digits para enrich O(log n)
8ef2524 feat(stj-vec-web): pagina de inteiro teor do documento com links na busca
a5ceb4a feat(stj-vec/ingest): pipeline Rust unificado -- download CKAN, extract, enrich, update
7e8dc86 feat(stj-vec): enrich pipeline Fase 1 + estrategia dual dense/sparse
```

(7 commits desta sessao, 22 total na main nao pushados)

---

## Decisoes tomadas

- **Pipeline tudo em Rust**: usuario rejeitou manter Python downloader em paralelo. Razao: arquitetura unica, sem bifurcacao de linguagem. Descartado: manter scripts Python para download.
- **Chunker corrigido agora, nao depois**: usuario insistiu que novos dados devem ser chunkeados corretamente desde o inicio. Rechunkear 13.5M chunks existentes descartado (mitigado por metadados enriquecidos).
- **Sem download via UI**: decisao de manter download/ingest como CLI/cron, nao expor botoes no Laravel. Razao: operacao de infra, nao de usuario. Timer systemd futuro.
- **Remover server legado**: crate `server/` (sqlite-vec) removido. Razao: risco de ser usado acidentalmente; o crate `search` (Qdrant) e o unico server.
- **SDK Agent TS (nao Rust/Python)**: TypeScript via Bun com @anthropic-ai/sdk. Manual agentic loop, coleta de tool calls. 7-23x mais rapido que CLI. Descartado: Agent SDK (overkill), Rust (sem SDK), Python (startup lento).
- **RRF sem threshold no backend**: Qdrant retorna top-K por canal, RRF funde. Threshold artificial descartado. Display no UI com faixas 0.025/0.015.
- **Manifest para incremental downloads**: gerado a partir dos arquivos existentes no disco para evitar re-download de 1715 resources.

---

## Metricas

### Base de dados SQLite

| Metrica | Valor |
|---------|-------|
| Total documentos | 2.210.952 |
| Total chunks | 13.878.754 |
| processo preenchido | 99.9% |
| orgao_julgador | 30.1% (acordaos enriquecidos) |
| data_julgamento | 26.3% (acordaos enriquecidos) |
| processo_digits indexado | 2.208.712 |
| Tamanho DB | ~52GB |

### Qdrant

| Metrica | Valor |
|---------|-------|
| Total pontos | 13.470.848 |
| Status | green |
| Collection | stj (dense 1024d + sparse) |

### Embeddings (Modal)

| Metrica | Valor |
|---------|-------|
| GPU utilizada | L4 (22GB VRAM) |
| VRAM peak | 3.9GB (18%) |
| GPU util avg | 87.1% |
| Throughput | 102 emb/s |
| 20 sources processados | 23.862 embeddings em 4.5 min |

### Performance

| Operacao | Tempo |
|----------|-------|
| Enrich 460 espelhos | 18s (antes: >10min) |
| SDK Agent query | 19-55s (CLI: 130-450s) |
| Import Qdrant 28k pontos | 5s |

### Disco

| Path | Tamanho |
|------|---------|
| Qdrant data | 93GB |
| Embeddings | 81GB |
| SQLite | 53GB |
| Juridico data | 33GB |
| **Livre** | **170GB** |

---

## Pendencias identificadas

1. **Corrigir teste DecomposedSearch `isProcessDead`** (alta) -- mock no teste nao inclui o novo metodo. Arquivos ja modificados mas nao commitados. Fix: adicionar `->shouldReceive('isProcessDead')->andReturn(false)` no mock helper.

2. **Push para origin** (alta) -- 22 commits locais na main. Nenhum PR aberto.

3. **Conectar Laravel ao Tailscale Serve** (media) -- BFF roda em 8082 mas nao tem HTTPS via Tailscale. Porta 8000 reservada (extractor lab). Opcao: configurar Tailscale Serve em porta alternativa.

4. **Timer systemd para atualizacao automatica** (media) -- `stj-vec-ingest update` deve rodar periodicamente (semanal ou diario). Nao implementado.

5. **5 sources antigos sem embeddings** (baixa) -- 20220810, 20230629, 20241001, 20241002, 20241014. Pendentes do Modal desde antes desta sessao.

6. **UI component library** (baixa) -- pesquisa feita sobre TallStackUI, Mary UI, BladewindUI. Recomendacao: TallStackUI (integra com Livewire). Nao implementado.

7. **Espelho com JSON invalido** (baixa) -- `segunda-secao/20240229.json` (data inexistente). 1 de 460. Sem impacto.

8. **data_julgamento cobertura baixa** (baixa) -- 26.3%. Depende de campo `dataDecisao` nos espelhos. O enrich ja preenche quando o espelho tem o dado, mas muitos espelhos nao tem.

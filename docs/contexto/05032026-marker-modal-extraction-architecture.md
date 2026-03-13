# Contexto: Arquitetura de Extracao Marker via Modal -- Analise e Decisoes

**Data:** 2026-03-05
**Sessao:** main (sem branch dedicado)
**Duracao:** ~1h30m
**Agente:** modal-inference (especialista GPU/Modal)

---

## O que foi feito

### 1. Levantamento completo do codebase de extracao

Mapeamento de todos os artefatos existentes relacionados a extracao de PDFs com Marker:

| Artefato | Local | Status | Papel |
|----------|-------|--------|-------|
| `marker_gpu_benchmark.ipynb` | `ferramentas/legal-text-extractor/` | Funcional | Benchmark single/multi-GPU em Modal Notebook |
| `modal_worker.py` | `ferramentas/legal-text-extractor/` | Legado | Worker com T4Extractor, `.map()`, multi-modo |
| `marker_engine.py` | `ferramentas/legal-text-extractor/src/engines/` | Legado | Engine wrapper com monitoring/Sentry |
| `marker_benchmark_image.py` | `ferramentas/legal-text-extractor/` | Funcional | Custom image Modal para notebook |

**Decisao: todo o codigo LTE e LEGADO.** O padrao a seguir e o de `stj-vec/modal/`.

### 2. Analise dos scripts stj-vec como padrao de referencia

Leitura completa de 4 scripts Modal em `stj-vec/modal/`:

| Script | GPU | Framework | Paralelismo | Producao? |
|--------|-----|-----------|-------------|-----------|
| `embed_hybrid.py` | H200 | FlagEmbedding | `.spawn()` + `handle.get()` | Sim |
| `embed.py` | H200 | TEI sidecar | `.map()` | Sim |
| `benchmark_gpu.py` | L4/A10G/A100 | sentence-transformers | Classes por GPU | Benchmark |
| `download_model.py` | CPU | sentence-transformers | N/A | Setup |

**Padroes-chave identificados:**

```
1. Unidade atomica de trabalho = 1 source JSONL (independente, idempotente)
2. list_pending_sources() = resumibilidade (re-run pula completos)
3. .spawn() para disparar N jobs -> handle.get() para coletar
4. .map() alternativo para distribuicao automatica
5. flush_volume() ao final para commit
6. UUIDs derivados de chunk_id para idempotencia no Qdrant
7. Volumes compartilhados (stj-vec-models, stj-vec-data)
```

Alem dos scripts Modal, lidos tambem:
- `import_qdrant.py` -- ProcessPoolExecutor com 6 workers, REST, idempotente
- `import_embeddings.py` -- Import para SQLite vec_chunks (legado, redundante com Qdrant)

### 3. Analise dos internos do Marker via memoria + pesquisa

Dados consolidados de 8+ sessoes anteriores (cogmem):

**Pipeline do Marker (6 estagios por chunk):**
1. Layout Detection (LayoutLMv3/Surya)
2. OCR Error Detection
3. Bbox Detection
4. Text Recognition (Donut/Swin encoder-decoder)
5. Reading Order (Donut/MBart encoder-decoder)
6. Text Cleanup (T5)

**Dados de performance medidos:**

| Config | Throughput | Tempo 1000 pags | Custo |
|--------|-----------|-----------------|-------|
| 1x L4 (sequencial) | ~1.6 pag/s | ~9h30m | ~$7.60 |
| 4x T4 (paralelo) | N/A (wall time) | 49 min | ~$1.93 |
| H100 (projetado, 22 processos) | ~122 pag/s | N/A | N/A |

**Comportamento critico do PdfConverter:**
- `page_range` aceita lista de paginas -- processa apenas essas
- Cada instanciacao do `PdfConverter` rebuilda o pipeline inteiro
- `CHUNK_SIZE=5` = catastrofico (200 rebuilds para 1000 pags)
- `CHUNK_SIZE=100` = otimo (10 rebuilds)
- `create_model_dict()` e o gargalo de load ("10% hang", 1-5 min)
- VRAM media ~2-5GB mas pode disparar com scans pesados

**Bug conhecido:** 2x A10G no mesmo notebook carrega modelos nas 2 GPUs mas processa so em `cuda:0`. Multi-GPU real requer containers separados (cada um com `CUDA_VISIBLE_DEVICES` isolado).

### 4. Rule de dominio criada: natureza dos autos judiciais

Adicionada secao no `legal-workbench/CLAUDE.md` documentando que autos de acoes judiciais sao heterogeneos por natureza (pecas digitais, scans, boletos, fotos, certidoes). Implicacoes diretas na arquitetura:
- VRAM dimensionada para pior caso
- Chunks de 50-100 pags para isolar paginas anomalas
- Retry por chunk obrigatorio
- Marker e a unica opcao (pdfplumber/pypdf falham silenciosamente)

### 5. Erro aprendido registrado

Adicionado ao `CLAUDE.md` raiz: "Assumi VRAM do Marker sem dados" -- regra: NAO assumir metricas de hardware sem medir.

---

## Estado dos arquivos

| Arquivo | Status | Detalhe |
|---------|--------|---------|
| `CLAUDE.md` | Modificado | +1 erro aprendido (VRAM Marker) |
| `legal-workbench/CLAUDE.md` | Modificado | +secao "Natureza dos Documentos Juridicos" (29 linhas) |

Nenhum script novo foi criado nesta sessao -- foi sessao de analise e decisao.

---

## Decisoes tomadas

1. **LTE e legado, padrao e stj-vec:** O codigo em `ferramentas/legal-text-extractor/` (modal_worker.py, marker_engine.py) nao deve ser base para novos scripts. O padrao a reproduzir e `stj-vec/modal/embed_hybrid.py`.

2. **Paralelismo horizontal, nao vertical:** Containers Modal separados (1 GPU cada) via `.spawn()` ou `.map()`, nunca `multiprocessing` dentro de 1 container. Validado por dados reais (4x T4 = 49 min vs 1x L4 = 9h30m).

3. **VRAM nao pode ser assumida:** Documentos juridicos sao roleta -- dimensionar para pior caso, com retry granular por chunk.

4. **Investigacao pendente:** Como exatamente o `PdfConverter` processa internamente (pass global vs pagina-a-pagina) ainda nao foi confirmado por leitura do source code. Queries de pesquisa foram geradas mas nao executadas.

---

## Pendencias identificadas

1. **Ler source do PdfConverter** (alta) -- Confirmar se o Marker faz pass global sobre o PDF antes de extrair, ou se processa pagina-a-pagina dentro do page_range. Isso determina se chunks de 1 pagina sao viaveis ou se ha overhead fixo por instanciacao.

2. **Escrever script Modal para Marker** (alta) -- No padrao stj-vec, com `.spawn()`, resumibilidade, retry por chunk, margem de VRAM. Dois perfis: "autos completos" (chunk=50, retry agressivo) e "peca digital" (chunk=100, rapido).

3. **Atualizar agente modal-inference** (media) -- Cobrir workloads de processamento de documentos (Marker/OCR), padroes de paralelismo Modal (`.spawn()` vs `.map()`), e batch processing para corpus grande.

4. **Issue ccui-app** (baixa) -- Adicionar referencia/citacao do usuario nas respostas (como Claude Desktop). Tool `create_issue` do Linear nao disponivel nesta sessao -- criar manualmente.

5. **Pesquisa Marker internals** (media) -- 5 queries de pesquisa geradas, nao executadas:
   - `marker-pdf PdfConverter page_range processing order does it scan all pages before extracting`
   - `marker-pdf VRAM spike scanned document OCR heavy GPU out of memory`
   - `site:github.com/datalab-to/marker PdfConverter page_range converters/pdf.py`
   - `marker-pdf memory usage per page does it load entire PDF into memory`
   - `site:github.com/issues marker-pdf parallel chunk GPU multi-process CUDA`

---

## Skill/agente avaliado

O agente `modal-inference` foi avaliado e tem lacunas:
- Cobre embeddings e LLMs, mas nao workloads de processamento de documentos
- Nao documenta padroes de paralelismo Modal (`.spawn()`, `.map()`, `max_containers`)
- Nao cobre batch processing para corpus grande (resumibilidade, chunking de input)

A skill `embedding-modal` referencia scripts em `stj-vec/tools/case-benchmark/` (pipeline Case Knowledge) que sao derivados do padrao stj-vec principal.

---

## Arquivos de referencia criticos

| Arquivo | Papel |
|---------|-------|
| `stj-vec/modal/embed_hybrid.py` | Padrao de referencia -- `.spawn()`, resumibilidade, hybrid output |
| `stj-vec/modal/embed.py` | Padrao TEI sidecar -- `.map()`, HTTP batching |
| `stj-vec/modal/benchmark_gpu.py` | Benchmark multi-GPU sistematico |
| `stj-vec/scripts/import_qdrant.py` | Import paralelo com ProcessPoolExecutor |
| `legal-workbench/CLAUDE.md` | Rule de dominio sobre autos judiciais |
| `marker_gpu_benchmark.ipynb` | Notebook de benchmark (funcional, single-GPU por sessao) |

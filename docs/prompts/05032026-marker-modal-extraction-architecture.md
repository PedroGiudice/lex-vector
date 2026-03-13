# Retomada: Script Modal para Extracao Marker (padrao stj-vec)

## Contexto rapido

Sessao anterior analisou toda a infraestrutura de extracao PDF com Marker no repo. Conclusao: o codigo em `ferramentas/legal-text-extractor/` (modal_worker.py, marker_engine.py) e legado. O padrao correto e o de `stj-vec/modal/embed_hybrid.py` -- paralelismo horizontal via `.spawn()`, containers separados, resumibilidade, idempotencia.

Dados medidos confirmam: 4x T4 paralelo = 49 min para 1000 pags ($1.93), vs 1x L4 sequencial = 9h30m ($7.60). O Marker usa ~2-5GB VRAM na media, mas documentos juridicos (autos) sao heterogeneos e VRAM pode disparar com scans/fotos/boletos. O `PdfConverter` rebuilda o pipeline inteiro a cada instanciacao -- `CHUNK_SIZE=100` e otimo, `CHUNK_SIZE=5` e catastrofico.

Uma rule de dominio foi adicionada ao `legal-workbench/CLAUDE.md` documentando a natureza imprevisivel dos autos judiciais e suas implicacoes para a arquitetura Modal.

Contexto detalhado: `docs/contexto/05032026-marker-modal-extraction-architecture.md`

## Arquivos principais

- `stj-vec/modal/embed_hybrid.py` -- padrao de referencia (`.spawn()`, resumivel, hybrid)
- `stj-vec/modal/embed.py` -- padrao TEI sidecar (`.map()`)
- `stj-vec/modal/benchmark_gpu.py` -- benchmark multi-GPU
- `legal-workbench/CLAUDE.md` -- rule de dominio sobre autos
- `ferramentas/legal-text-extractor/marker_gpu_benchmark.ipynb` -- notebook benchmark existente
- `docs/contexto/05032026-marker-modal-extraction-architecture.md` -- contexto completo

## Proximos passos (por prioridade)

### 1. Confirmar comportamento interno do PdfConverter

**Onde:** Source code do Marker (instalado no `.venv` do LTE, ou GitHub `datalab-to/marker`)
**O que:** Ler `marker/converters/pdf.py` e confirmar se:
  - O `PdfConverter.__call__()` faz um pass global sobre todas as paginas do page_range antes de extrair
  - Ou se processa pagina-a-pagina de forma independente
  - Qual o overhead real por instanciacao (modelos sao recarregados ou reutilizados via `artifact_dict`?)
**Por que:** Determina se chunks de 10-20 paginas sao viaveis (se nao ha pass global) ou se 50-100 e o minimo viavel
**Verificar:** Leitura do source code. 5 queries de pesquisa foram geradas na sessao anterior:
```
marker-pdf PdfConverter page_range processing order does it scan all pages before extracting
marker-pdf VRAM spike scanned document OCR heavy GPU out of memory
site:github.com/datalab-to/marker PdfConverter page_range converters/pdf.py
marker-pdf memory usage per page does it load entire PDF into memory
site:github.com/issues marker-pdf parallel chunk GPU multi-process CUDA
```

### 2. Escrever script Modal para extracao Marker

**Onde:** Criar `stj-vec/modal/extract_marker.py` (ou `legal-workbench/ferramentas/modal/extract_marker.py` -- decidir local)
**O que:** Script no padrao `embed_hybrid.py`:
  - `MarkerExtractor` class com `@modal.enter()` carregando modelos
  - `extract_chunk(pdf_path, page_start, page_end)` como `@modal.method()`
  - `list_pending_extractions()` para resumibilidade
  - `main()` com `.spawn()` distribuindo chunks
  - Dois perfis: "autos" (chunk=50, retry, T4/L4) e "digital" (chunk=100, rapido, T4)
  - Imagem com `marker-pdf`, `tesseract-ocr-por`, `poppler-utils`
  - Volume compartilhado para PDFs input e markdowns output
  - Retry por chunk com backoff (chunk que falha = re-tentar com chunk_size menor)
  - Metricas de calibracao (`[CALIBRATION]` logs como embed_hybrid.py)
**Por que:** Pipeline de producao para extracao de autos judiciais
**Verificar:**
```bash
modal run extract_marker.py --source <nome-do-pdf> --dry-run
modal run extract_marker.py --source <nome-do-pdf>
```

### 3. Atualizar agente modal-inference

**Onde:** `~/.claude/agents/modal-inference.md`
**O que:** Adicionar secao cobrindo:
  - Workloads de processamento de documentos (Marker, OCR, nao apenas embedding/LLM)
  - Padroes de paralelismo Modal: `.spawn()` (controle fino) vs `.map()` (automatico) vs `max_containers` (scaling)
  - Batch processing para corpus grande: resumibilidade, chunking de input, retry granular
  - Referencia ao padrao stj-vec como implementacao canonica
**Por que:** O agente so cobre embeddings/LLMs, e e acionado para qualquer workload GPU no Modal
**Verificar:** Ler o agente atualizado e confirmar que cobre os 3 padroes

### 4. Criar issue Linear para ccui-app

**Onde:** Linear (workspace cmr-auto)
**O que:** Issue "ccui-app: adicionar referencia/citacao do usuario nas respostas (como Claude Desktop)"
**Por que:** PGR faz referencia ao que o usuario disse nas conversas, feature de UX
**Verificar:** `mcp__linear__list_issues` confirmando criacao

## Como verificar

```bash
# Confirmar que as mudancas desta sessao estao presentes
cd /home/opc/lex-vector
git diff --stat
# Deve mostrar: CLAUDE.md (+1 linha), legal-workbench/CLAUDE.md (+29 linhas)

# Confirmar rule de dominio
grep -c "Natureza dos Documentos Juridicos" legal-workbench/CLAUDE.md
# Deve retornar: 1

# Confirmar padrao stj-vec existe e e legivel
cat stj-vec/modal/embed_hybrid.py | head -20

# Confirmar notebook existe
ls ferramentas/legal-text-extractor/marker_gpu_benchmark.ipynb
```

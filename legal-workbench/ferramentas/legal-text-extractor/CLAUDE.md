# CLAUDE.md - Legal Text Extractor (LTE)

Pipeline de extracao de texto de documentos juridicos.

---

## Arquitetura Atual (2026-01)

**Engine principal: Marker** (ML-based, GPU-accelerated via Modal)

O LTE evoluiu de um pipeline de 4 etapas (Cartografo -> Saneador -> Extrator -> Bibliotecario)
para usar o **Marker** como engine principal de extracao.

### Estrategia de GPU (Modal)

A configuracao **ideal** para extracao e **chunking do PDF + multiplas GPUs pequenas**.
O PDF e dividido em blocos de ~100 paginas e cada bloco vai para uma GPU independente.
GPUs pequenas (T4 16GB, L4 24GB) conseguem devorar o PDF inteiro como piranhas --
cada uma ataca um pedaco em paralelo.

| Config | GPUs | Custo/h | Quando usar |
|--------|------|---------|-------------|
| Multi-T4 (2-8x) | T4 16GB | ~$0.59/GPU | PDFs > 300 paginas (padrao `--smart`) |
| Bi/Quad-L4 | L4 24GB | ~$0.80/GPU | PDFs pesados com muito OCR |
| A100 unica | A100 80GB | ~$3.50 | PDFs < 300 paginas ou debug |

**Por que chunking + GPUs pequenas vence:**
- Escala horizontal: 4x T4 processam 4 blocos simultaneamente
- Custo menor: T4/L4 sao fracao do preco de A100
- Sem gargalo de VRAM: cada GPU carrega apenas ~100 paginas
- Resiliencia: se um chunk falha, so re-processa aquele bloco

Implementacao: `modal_worker.py` (`extract_pdf_parallel`, `T4Extractor`)

### Engines Ativos
| Engine | Uso | Localizacao |
|--------|-----|-------------|
| **Marker** | Producao (GPU via Modal) | `src/engines/marker_engine.py` |
| **pdfplumber** | Fallback para PDFs nativos simples | `src/engines/pdfplumber_engine.py` |

### Codigo Obsoleto (NAO USAR)
O repositorio contem codigo legado do pipeline antigo que NAO deve ser usado:

| Arquivo/Modulo | Status | Motivo |
|----------------|--------|--------|
| `pytesseract` | OBSOLETO | Substituido por Marker OCR (Surya) |
| `pdf2image` | OBSOLETO | Substituido por Marker |
| `anthropic` | NUNCA FOI DEP | Codigo experimental removido |
| `src/steps/step_03_extract.py` | PARCIALMENTE OBSOLETO | Logica Tesseract obsoleta |
| `src/analyzers/section_analyzer.py` | OBSOLETO | Usava Anthropic |
| `tests/test_image_cleaner_integration.py` | OBSOLETO | Usa pdf2image |
| `tests/test_section_analyzer.py` | OBSOLETO | Usa anthropic |
| `tests/test_step_02_vision.py` | OBSOLETO | Usa pytesseract |

---

## Dependencias Atuais

```toml
# pyproject.toml - deps principais
marker-pdf >= 1.0.0      # Engine principal
modal >= 0.64.0          # GPU serverless
pdfplumber               # Fallback para texto nativo
opencv-python-headless   # Pre-processamento imagem
numpy                    # Operacoes numericas
```

**NAO SAO DEPENDENCIAS:**
- `pytesseract` - OBSOLETO
- `pdf2image` - OBSOLETO
- `anthropic` - NUNCA FOI DEPENDENCIA

---

## Testes

### Testes que FUNCIONAM
```bash
cd legal-workbench/ferramentas/legal-text-extractor
uv run pytest tests/test_cleaner.py tests/test_detector.py -v
```

### Testes OBSOLETOS (vao falhar por imports)
- `test_image_cleaner_integration.py`
- `test_section_analyzer.py`
- `test_step_02_vision.py`

> **TODO:** Remover ou atualizar testes obsoletos

---

## Deploy (Docker)

O servico de producao esta em `docker/services/text-extractor/`:
- `celery_worker.py` - Worker que usa Marker via Modal GPU
- `api/main.py` - FastAPI para submissao de jobs

```bash
# Testar localmente
cd legal-workbench
docker compose up -d api-text-extractor
```

---

## NUNCA

- Usar `pytesseract`, `pdf2image`, ou `anthropic` - SAO OBSOLETOS
- Modificar `src/context/store.py` sem testes
- Alterar schema do SQLite sem migration plan
- Rodar testes obsoletos e assumir que "deps faltam"

---

*Herdado de: ferramentas/CLAUDE.md*
*Ultima atualizacao: 2026-01-17*

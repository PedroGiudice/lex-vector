# Legal Text Extractor

Agente de extração inteligente de texto de documentos jurídicos processuais brasileiros.

## Instalação

```bash
cd ferramentas/legal-text-extractor
python -m venv .venv
source .venv/bin/activate  # Linux/WSL
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## Uso

```python
from main import LegalTextExtractor

extractor = LegalTextExtractor()
result = extractor.process_pdf("processo.pdf", separate_sections=True)

print(f"Sistema: {result.system_name}")
print(f"Redução: {result.reduction_pct:.1f}%")
```

## Testes

```bash
pytest tests/
```

## Arquitetura

Pipeline de 3 estágios algorítmicos (sem dependência de API externa):

```
PDF → [Cartógrafo] → [Saneador] → [Extrator] → Texto Limpo
       step_01       step_02       step_03
```

1. **Cartógrafo** (`step_01_layout.py`): Detecta sistema judicial, mapeia layout
2. **Saneador** (`step_02_vision.py`): Pré-processa imagens para OCR
3. **Extrator** (`step_03_extract.py`): Extrai texto com bbox filtering

### ImageCleaner (`src/core/image_cleaner.py`)

Módulo de visão computacional (OpenCV/Numpy) para limpeza de imagens:

- **Modos**: `auto`, `digital`, `scanned`
- **Funcionalidades**:
  - `remove_gray_watermarks()` - Remove marcas d'água cinza
  - `clean_dirty_scan()` - Adaptive threshold para scans
  - `remove_color_stamps()` - HSV segmentation para carimbos
  - `remove_speckles()` - Median filter para ruído salt-and-pepper
  - `has_speckle_noise()` - **Detecção condicional de ruído** (evita degradar texto preto)

```python
from src.core.image_cleaner import ImageCleaner, CleaningOptions

cleaner = ImageCleaner()
cleaned = cleaner.process_image(pil_image, mode="auto")

# Ou com opções customizadas
opts = CleaningOptions(watermark_threshold=190, despeckle_kernel=5)
cleaner = ImageCleaner.from_options(opts)
```

### PipelineOrchestrator (`src/pipeline/orchestrator.py`)

Orquestrador de alto nível com processamento página-a-página e integração UI:

```python
from src.pipeline.orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

# Modo básico
result = orchestrator.process(Path("documento.pdf"))

# Com callback de progresso (para Streamlit)
def on_progress(current, total, msg):
    st.progress(current / total)
    st.text(msg)

result = orchestrator.process(pdf_path, progress_callback=on_progress)

# Modo generator (streaming)
for page in orchestrator.process_generator(pdf_path):
    print(f"Página {page['page_num']}: {len(page['text'])} chars")
```

**Engines suportados:**
| Engine | Uso | Característica |
|--------|-----|----------------|
| `pdfplumber` | Texto nativo | Leve, usa `safe_bbox` |
| `tesseract` | OCR (scans) | Converte 1 página por vez |
| `marker` | Alta qualidade | Cache inteligente |

## Status

- ✅ Fase 1: Core de limpeza (75+ padrões)
- ✅ Fase 2: Pipeline Algorítmico
  - 3 estágios algorítmicos (Cartógrafo, Saneador, Extrator)
  - ImageCleaner com despeckle condicional
  - Detecção automática de modo (digital/scanned)
  - 100% preservação de texto em documentos digitais
- ✅ **Fase 3: Integração UI (ATUAL)**
  - Extração granular página-a-página
  - `progress_callback` para barras de progresso
  - `process_generator` para streaming
  - Cache Marker para eficiência

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

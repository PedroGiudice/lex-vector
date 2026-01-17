# RunPod Template - Marker PDF Extractor

Extracao de texto de PDFs juridicos com GPU.

## Specs - 2x A40

| Recurso | Valor |
|---------|-------|
| GPU | 2x NVIDIA A40 |
| VRAM | 96 GB |
| Preco | $0.40/hr (on-demand) |
| Disponibilidade | High |

## Config do Template

```
Template Name: lw-marker-pdf-extractor
Image: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
Container Disk: 20 GB
Volume Disk: 50 GB
Volume Mount: /workspace
HTTP Port: 8000
TCP Port: 22
```

### Variaveis de Ambiente

```
TORCH_DEVICE=cuda
DETECTOR_BATCH_SIZE=32
RECOGNITION_BATCH_SIZE=64
HF_HOME=/workspace/huggingface
MARKER_CACHE_DIR=/workspace/marker_cache
```

## Primeiro Uso

### 1. Instalar Marker

```bash
pip install marker-pdf
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-por
```

### 2. Baixar Modelos (~5-10min primeira vez)

```bash
python -c "from marker.models import create_model_dict; create_model_dict()"
```

## Uso

### CLI

```bash
marker_single /workspace/input.pdf /workspace/output --output_format markdown
```

### Python

```python
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

models = create_model_dict()
converter = PdfConverter(artifact_dict=models)
rendered = converter("/workspace/input.pdf")
text, _, _ = text_from_rendered(rendered)
print(text)
```

## Performance

| Tipo PDF | 100 pags | GPU | CPU (OCI) |
|----------|----------|-----|-----------|
| Nativo | ~30s | ~8min |
| OCR | ~2min | ~15min |

## Custos

| Volume | Horas | Custo/mes |
|--------|-------|-----------|
| 100 PDFs | ~3h | ~$1.20 |
| 200 PDFs | ~6h | ~$2.40 |

## Troubleshooting

**CUDA OOM:** Reduza `DETECTOR_BATCH_SIZE=16`
**Download falhou:** `rm -rf /workspace/huggingface/hub/models--*` e tente novamente

---
*2026-01-17*

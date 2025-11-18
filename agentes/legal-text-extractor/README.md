# Legal Text Extractor

Agente de extração inteligente de texto de documentos jurídicos processuais brasileiros.

## Instalação

```bash
cd agentes/legal-text-extractor
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

## Status

- ✅ Fase 1: Core de limpeza (75+ padrões)
- ✅ **Fase 2 - Milestone 1: SDK Integration (COMPLETO)**
  - Rate limiting automático (20 req/min)
  - Retry logic com exponential backoff
  - Prompt engineering com few-shot examples
  - JSON parsing com validação Pydantic
  - Extração de seções com fuzzy matching
- ✅ **Fase 2 - Milestone 2: Learning System (COMPLETO)**
  - Pattern extraction de documentos validados
  - Few-shot manager com auto-seleção de exemplos
  - Metrics tracking (precision/recall/F1)
  - Storage JSON persistente
  - Performance trends e auto-decisão de melhorias
- 🚧 Fase 2 - Milestone 3: Self-Improvement (próximo)
- ⏸️ Fase 2 - Milestone 4: End-to-End Testing

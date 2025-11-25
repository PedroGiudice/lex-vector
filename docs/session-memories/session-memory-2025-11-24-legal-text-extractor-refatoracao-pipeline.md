# Session Memory: Legal Text Extractor - Refatoração Pipeline 3 Estágios

**Data:** 2025-11-24
**Objetivo:** Refatorar legal-text-extractor para arquitetura de pipeline algorítmica

---

## Contexto Crítico

### Decisão Arquitetural
- **REMOVIDO:** Uso de Claude API/SDK para separação de seções
- **ADOTADO:** Pipeline algorítmica 100% local (Python/OpenCV/Tesseract)
- **Motivo:** Custo proibitivo de LLM para autos volumosos (5.000+ páginas)

### Filosofia do Projeto
```
A "inteligência" de extração deve ser ALGORÍTMICA (Python/OpenCV),
NÃO baseada em chamadas de API.
```

---

## O que foi implementado

### Arquitetura Pipeline de 3 Estágios

```
src/steps/
├── step_01_layout.py   # Cartógrafo - Histograma de densidade
├── step_02_vision.py   # Saneador - OpenCV pipeline
└── step_03_extract.py  # Extrator - pdfplumber + Tesseract
```

### Arquivos Criados

| Arquivo | Linhas | Status |
|---------|--------|--------|
| `src/config.py` | ~140 | ✅ Completo |
| `src/steps/step_01_layout.py` | ~280 | ✅ Completo |
| `src/steps/step_02_vision.py` | ~390 | ✅ Completo |
| `src/steps/step_03_extract.py` | ~460 | ✅ Completo |
| `scripts/generate_fixtures.py` | ~360 | ✅ Completo |
| `test-documents/fixture_test.pdf` | 178KB | ✅ Gerado |

### Commits Realizados

```
baee1c4 feat(legal-text-extractor): adiciona gerador de fixtures e dependências vision
8141790 feat(legal-text-extractor): implementa step_03_extract.py (Extrator)
```

---

## Algoritmo do Cartógrafo (step_01_layout.py)

**Histograma de Densidade para detecção de tarja lateral:**

```python
# 1. Divide largura em N bins (default: 100)
# 2. Conta caracteres por bin
# 3. Detecta pico nos últimos 20% = TARJA
# 4. Define x_cut para excluir zona de ruído
# 5. Classifica: NATIVE (>50 chars) ou RASTER_NEEDED
```

**Output:** `outputs/{doc_id}/layout.json`

```json
{
  "doc_id": "documento",
  "total_pages": 10,
  "pages": [
    {
      "page_num": 1,
      "type": "NATIVE",
      "safe_bbox": [0, 0, 480, 800],
      "has_tarja": true,
      "tarja_x_cut": 480
    }
  ]
}
```

---

## PDFs de Teste Adicionados

1. **1057607-11.2024.8.26.0002.pdf** (25.8 MB) - PJe com tarjas
2. **Forscher x Salesforce** (2.5 MB) - Digital misto
3. **Luiz Victor x Salesforce** (43.6 MB) - Inicial + docs

**Fixture sintética:** `fixture_test.pdf` (3 páginas)
- Página 1: NATIVE (texto normal)
- Página 2: RASTER_NEEDED (imagem de texto)
- Página 3: TARJA (texto + tarja lateral 20%)

---

## Dependências Necessárias

```bash
# Python
pip install pdf2image opencv-python-headless numpy pytesseract

# Sistema (WSL2/Ubuntu)
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-por
```

---

## Próximos Passos (Pendente)

1. **Instalar dependências** no ambiente de casa
2. **Testar pipeline completo** com fixture_test.pdf:
   ```bash
   cd agentes/legal-text-extractor
   source .venv/bin/activate
   python src/steps/step_01_layout.py test-documents/fixture_test.pdf
   ```
3. **Validar output** `outputs/{doc_id}/final.md`
4. **Testar com PDFs reais** (os 3 adicionados)

---

## Arquivos Preservados (NÃO modificar)

```
src/core/
├── patterns.py   # 75+ regex de limpeza
├── cleaner.py    # Orquestrador de limpeza
├── detector.py   # Auto-detecção de sistemas
└── normalizer.py # Normalização pós-limpeza
```

---

## Arquivos a IGNORAR (código legado)

```
src/analyzers/   # Claude API (não usar)
src/learning/    # Claude API (não usar)
src/prompts/     # Claude prompts (não usar)
```

---

## Output Esperado (final.md)

```markdown
## [[PAGE_001]] [TYPE: NATIVE]
(Conteúdo textual limpo da página 1...)

## [[PAGE_002]] [TYPE: OCR]
(Conteúdo extraído via Tesseract da página 2...)

## [[PAGE_003]] [TYPE: NATIVE]
(Conteúdo com tarja removida da página 3...)
```

**Propósito:** Preservar fronteiras de página para segmentação semântica futura.

---

## Notas Importantes

- Os testes de ontem mencionados pelo usuário **NÃO foram commitados**
- A mudança de estratégia (remover SDK) **NÃO estava documentada no repo**
- Esta sessão documenta essas decisões para referência futura

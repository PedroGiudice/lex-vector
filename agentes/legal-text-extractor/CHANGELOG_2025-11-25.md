# Changelog - 2025-11-25

## Resumo

Implementacao de **Boundary Detection** para documentos genericos e **Testes de Invariancia Multi-Sistema**.

---

## Novos Arquivos

### src/core/intelligence/

| Arquivo | Linhas | Descricao |
|---------|--------|-----------|
| `boundary_config.py` | ~340 | Configuracao adaptavel de boundary detection |
| `boundary_detector.py` | ~280 | Detector conservador de boundaries |

### src/schemas/

| Arquivo | Linhas | Descricao |
|---------|--------|-----------|
| `validation_artifacts.json` | ~300 | Schema JSON de artefatos por sistema (PJe, ESAJ, EPROC, STF, STJ) |

### tests/

| Arquivo | Testes | Descricao |
|---------|--------|-----------|
| `test_boundary_detection.py` | 27 | Testes de boundary detection e preservacao |
| `test_invariance.py` | 11 | Testes de invariancia multi-sistema |

### tests/fixtures/invariance/

| Arquivo | Descricao |
|---------|-----------|
| `README.md` | Documentacao das fixtures |
| `peticao_inicial/texto_base.txt` | Texto puro (sem artefatos) |
| `peticao_inicial/com_artefatos_pje.txt` | Texto + artefatos PJe |
| `peticao_inicial/com_artefatos_esaj.txt` | Texto + artefatos ESAJ |
| `peticao_inicial/com_artefatos_eproc.txt` | Texto + artefatos EPROC |

### docs/

| Arquivo | Descricao |
|---------|-----------|
| `SEMANTIC_IDENTITY.md` | Documentacao sobre semantic vs byte identity |
| `flowchart_prompt_25112025.txt` | Prompt para geracao de flowchart |

---

## Arquivos Modificados

### src/core/intelligence/__init__.py

**Adicoes:**
- Exporta `BoundaryConfig`, `BoundaryPattern`, `DocumentClass`
- Exporta `BoundaryDetector`, `detect_boundaries_conservative`, `has_boundary_markers`
- Exporta factory methods: `get_conservative_config`, `get_formal_document_config`, `get_compact_document_config`, `get_disabled_config`

### src/core/intelligence/segmenter.py

**Adicoes (+180 linhas):**
- `refine_anexos_section()` - Refina secoes ANEXOS com boundary detection
- `segment_with_boundary_refinement()` - Metodo combinado (segmentacao + refinamento)
- `_line_to_page()` - Helper para converter linha para pagina

---

## Funcionalidades Implementadas

### 1. Boundary Detection (Deteccao de Limites entre Documentos)

**Problema resolvido:** Secoes ANEXOS agrupavam todos os documentos como bloco unico.

**Solucao:** Detector conservador que identifica inicio de:
- Procuracoes (`PROCURACAO AD JUDICIA`)
- Contratos (`CONTRATO DE PRESTACAO DE SERVICOS`)
- Notas Fiscais (`DANFE`, `NF-E`)
- Comprovantes (`COMPROVANTE DE PAGAMENTO`)
- Documentos numerados (`DOC. 1`, `ANEXO I`)

**Principios de seguranca:**
- `min_confidence = 0.8` (so separa quando muito confiante)
- Boundary = INICIO do proximo documento (nunca fim do atual)
- Preservacao total de conteudo (testes garantem reconstrucao)
- Na duvida, NAO separa (falso negativo > falso positivo)

### 2. Testes de Invariancia Multi-Sistema

**Principio testado:** A mesma peticao protocolada em PJe, ESAJ ou EPROC deve produzir classificacao IDENTICA apos remocao de artefatos.

**Testes implementados:**
- `test_invariancia_semantica` - Texto limpo == texto base
- `test_invariancia_entre_sistemas` - PJe limpo == ESAJ limpo == EPROC limpo
- `test_texto_reconstruido_igual_original` - Zero perda de conteudo

### 3. Schema de Artefatos de Validacao

**Problema resolvido:** Artefatos de validacao estavam em codigo Python, dificultando separacao arquitetural.

**Solucao:** `validation_artifacts.json` com 57 patterns documentados:
- PJe: 7 patterns
- ESAJ: 8 patterns
- EPROC: 6 patterns
- PROJUDI: 5 patterns
- STF: 7 patterns
- STJ: 8 patterns
- UNIVERSAL: 6 patterns

---

## Testes

### Resultados

```
tests/test_boundary_detection.py: 27 passed
tests/test_invariance.py: 11 passed
tests/test_detector.py: 11 passed
tests/test_cleaner.py: 3 passed
----------------------------------------
Total: 52 passed
```

### Cobertura

| Modulo | Testes |
|--------|--------|
| boundary_config | 8 |
| boundary_detector | 7 |
| preservacao | 4 |
| edge_cases | 5 |
| invariancia | 7 |

---

## Decisoes Arquiteturais

| Decisao | Justificativa |
|---------|---------------|
| Confidence minima 0.8 | Evita fragmentacao incorreta de documentos |
| Boundary = inicio | Preserva rodapes, assinaturas, clausulas finais |
| Schema JSON separado | Separacao clara system-aware vs system-agnostic |
| Fixtures sinteticas | Testes rapidos; fixtures reais para edge cases de encoding |

---

## Proximos Passos Sugeridos

1. **Fixtures reais de encoding** - BOM, CRLF/LF, Latin-1 (do verbose-correct-doodle)
2. **Robustez OCR** - Melhorar remocao de marca d'agua para PDFs sujos
3. **Metrica de sucesso** - 80% conteudo legivel para PDFs muito sujos
4. **Teste end-to-end** - Pipeline completa PDF → structure.json

---

*Changelog gerado em 2025-11-25*

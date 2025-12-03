# PROMPT PARA GEMINI - Criar Interface/App do Legal Text Extractor

## CONTEXTO

Você vai criar uma interface/aplicação para executar o **Legal Text Extractor**, um sistema de extração de texto de documentos jurídicos brasileiros. Este documento contém TODA a informação necessária para entender o workflow e integrar o extrator de forma eficiente.

---

## 1. VISÃO GERAL DO SISTEMA

### O que é
Sistema de extração inteligente de texto de PDFs jurídicos brasileiros, com:
- Pipeline de 4 estágios (Layout → Vision → Extraction → Classification)
- Detecção automática de 7 sistemas judiciais (PJE, ESAJ, EPROC, PROJUDI, STF, STJ)
- 75+ padrões regex para limpeza de assinaturas digitais e certificações
- 3 engines de extração (PDFPlumber, Tesseract OCR, Marker)
- Classificação semântica de 12 tipos de peças processuais
- Sistema de aprendizado de padrões (Context Store)

### Localização do Código
```
/home/user/Claude-Code-Projetos/agentes/legal-text-extractor/
```

---

## 2. ARQUITETURA DA PIPELINE

```
PDF Original
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 01: CARTÓGRAFO (Layout Analysis)                      │
│  Arquivo: src/steps/step_01_layout.py                       │
│  Classe: LayoutAnalyzer                                     │
│  Input: PDF                                                 │
│  Output: outputs/{doc_id}/layout.json                       │
│  Função: Detecta tarjas laterais, classifica páginas        │
│          (NATIVE vs RASTER_NEEDED), define safe_bbox        │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 02: SANEADOR (Vision Pipeline)                        │
│  Arquivo: src/steps/step_02_vision.py                       │
│  Classe: VisionProcessor                                    │
│  Input: layout.json + PDF                                   │
│  Output: outputs/{doc_id}/images/page_XXX.png               │
│  Função: Renderiza páginas RASTER, aplica OpenCV            │
│          (grayscale, Otsu threshold, denoise)               │
│  NOTA: Só executa se houver páginas RASTER_NEEDED           │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 03: EXTRATOR (Text Extraction)                        │
│  Arquivo: src/steps/step_03_extract.py                      │
│  Classe: TextExtractor                                      │
│  Input: layout.json + PDF + images/ (opcional)              │
│  Output: outputs/{doc_id}/final.md                          │
│  Função: Extrai texto via PDFPlumber (NATIVE) ou            │
│          Tesseract OCR (RASTER), aplica limpeza semântica   │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 04: BIBLIOTECÁRIO (Semantic Classification)           │
│  Arquivo: src/steps/step_04_classify.py                     │
│  Classe: SemanticClassifier                                 │
│  Input: final.md                                            │
│  Output: outputs/{doc_id}/semantic_structure.json           │
│          outputs/{doc_id}/final_tagged.md                   │
│  Função: Classifica peças processuais (12 categorias),      │
│          segmenta documento em seções                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. ESTRUTURA DE ARQUIVOS

```
legal-text-extractor/
├── main.py                          # Entry point principal
├── requirements.txt                 # Dependências Python
├── src/
│   ├── config.py                    # Configurações centralizadas
│   ├── steps/
│   │   ├── step_01_layout.py        # Análise de layout
│   │   ├── step_02_vision.py        # Processamento de imagem
│   │   ├── step_03_extract.py       # Extração de texto
│   │   └── step_04_classify.py      # Classificação semântica
│   ├── engines/
│   │   ├── base.py                  # Interface ExtractionEngine
│   │   ├── pdfplumber_engine.py     # Engine nativa (0.5GB RAM)
│   │   ├── tesseract_engine.py      # OCR (1GB RAM)
│   │   ├── marker_engine.py         # Premium (8GB RAM) - STUB
│   │   ├── engine_selector.py       # Seleção automática
│   │   ├── selector.py              # Escalação progressiva
│   │   └── cleaning_engine.py       # Limpeza adaptativa
│   ├── core/
│   │   ├── cleaner.py               # DocumentCleaner principal
│   │   ├── detector.py              # Detecção de sistema judicial
│   │   ├── patterns.py              # 75+ padrões regex
│   │   ├── normalizer.py            # Normalização de texto
│   │   └── intelligence/
│   │       ├── segmenter.py         # Segmentação de peças
│   │       ├── definitions.py       # Taxonomia legal
│   │       ├── cleaner_advanced.py  # Limpeza avançada
│   │       └── boundary_detector.py # Detecção de limites
│   ├── context/
│   │   ├── store.py                 # ContextStore (aprendizado)
│   │   ├── models.py                # Data models
│   │   └── signature.py             # Cálculo de assinaturas
│   ├── exporters/
│   │   ├── text.py                  # Export .txt
│   │   ├── markdown.py              # Export .md
│   │   └── json.py                  # Export .json
│   └── pipeline/
│       └── orchestrator.py          # Orquestrador completo
├── inputs/                          # PDFs de entrada
├── outputs/                         # Resultados processados
│   └── {doc_id}/
│       ├── layout.json
│       ├── images/
│       ├── final.md
│       ├── semantic_structure.json
│       └── final_tagged.md
└── tests/                           # Testes unitários
```

---

## 4. API PRINCIPAL - Como Usar

### 4.1 Uso Básico (main.py)

```python
from pathlib import Path
from main import LegalTextExtractor

# Inicializar
extractor = LegalTextExtractor()

# Processar PDF
result = extractor.process_pdf(
    pdf_path=Path("documento.pdf"),
    system=None,          # Auto-detect (PJE, ESAJ, etc)
    blacklist=None,       # Termos adicionais a remover
    output_format="text"  # "text", "markdown", "json"
)

# Acessar resultado
print(f"Sistema: {result.system_name} ({result.confidence}%)")
print(f"Redução: {result.reduction_pct:.1f}%")
print(f"Texto: {result.text[:500]}...")

# Salvar
extractor.save(result, "output.txt", format="text")
extractor.save(result, "output.md", format="markdown")
extractor.save(result, "output.json", format="json")
```

### 4.2 Estrutura do ExtractionResult

```python
@dataclass
class ExtractionResult:
    text: str                      # Texto limpo extraído
    sections: list[Section]        # Seções do documento
    system: str                    # Código: 'pje', 'esaj', etc
    system_name: str               # Nome completo do sistema
    confidence: int                # Confiança da detecção (0-100)
    original_length: int           # Caracteres antes da limpeza
    final_length: int              # Caracteres após limpeza
    reduction_pct: float           # Percentual de redução
    patterns_removed: list[str]    # Padrões aplicados
```

### 4.3 Uso por Steps Individuais (CLI)

```bash
# Ativar ambiente virtual
cd /home/user/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate

# STEP 01: Análise de Layout
python -m src.steps.step_01_layout inputs/processo.pdf
# Output: outputs/processo/layout.json

# STEP 02: Processamento de Imagem (se necessário)
python -m src.steps.step_02_vision \
    --layout-json outputs/processo/layout.json \
    --pdf-path inputs/processo.pdf \
    --doc-id processo
# Output: outputs/processo/images/page_*.png

# STEP 03: Extração de Texto
python -m src.steps.step_03_extract \
    --layout-json outputs/processo/layout.json \
    --pdf-path inputs/processo.pdf \
    --images-dir outputs/processo/images
# Output: outputs/processo/final.md

# STEP 04: Classificação Semântica
python -m src.steps.step_04_classify \
    --input-md outputs/processo/final.md
# Output: outputs/processo/semantic_structure.json
#         outputs/processo/final_tagged.md
```

---

## 5. ENGINES DE EXTRAÇÃO

### Hierarquia de Qualidade
| Engine | RAM | Qualidade | Uso |
|--------|-----|-----------|-----|
| **Marker** | 8GB | 1.0 (melhor) | PDFs complexos, tabelas |
| **PDFPlumber** | 0.5GB | 0.9 | Texto nativo (não escaneado) |
| **Tesseract** | 1GB | 0.7 | OCR para scans |

### Seleção Automática (engine_selector.py)
```python
# Lógica de seleção:
# 1. Se PDF tem ≥80% texto nativo → PDFPlumber
# 2. Se PDF escaneado + RAM ≥8GB → Marker
# 3. Fallback → Tesseract OCR
```

### Escalação Progressiva (selector.py)
```python
# Se confidence < 0.85:
#   Tesseract → Marker (se PDF + RAM ok)
#   Compara similaridade textual
#   Retorna melhor resultado
```

---

## 6. SISTEMAS JUDICIAIS SUPORTADOS

### Detecção Automática (detector.py)
| Sistema | Prioridade | Fingerprints | Descrição |
|---------|------------|--------------|-----------|
| **STF** | 1 (alta) | `supremo tribunal federal`, `e-stf`, `pkcs #7` | Supremo Tribunal Federal |
| **STJ** | 1 (alta) | `superior tribunal de justiça`, `e-stj` | Superior Tribunal de Justiça |
| **PJE** | 2 (média) | `processo judicial eletrônico`, `pje`, código verificação | CNJ - Nacional |
| **ESAJ** | 2 (média) | `e-saj`, `softplan`, `tjsp.jus.br` | TJSP e outros estados |
| **EPROC** | 2 (média) | `eproc`, `trf4.jus.br`, `.p7s` | TRFs |
| **PROJUDI** | 3 (baixa) | `projudi`, `processo judicial digital` | Variações regionais |
| **GENERIC** | fallback | padrões ICP-Brasil | Sistema não identificado |

### Padrões de Limpeza por Sistema (patterns.py)
- **PJE**: 6 padrões (código verificação, timestamp, URL validação, assinatura dupla)
- **ESAJ**: 7 padrões (código documento, conferência digital, QR Code, brasão TJSP)
- **EPROC**: 5 padrões (arquivo .p7s, verificador ITI, selo PAdES)
- **STF**: 7 padrões (marca d'água CPF, assinatura PKCS7, Projeto Victor)
- **STJ**: 8 padrões (código verificação, timestamp BRT, QR Code)
- **UNIVERSAL**: 15 padrões (aplicados a TODOS os sistemas)

---

## 7. CLASSIFICAÇÃO DE PEÇAS PROCESSUAIS

### 12 Categorias (definitions.py)
1. **PETIÇÃO_INICIAL** - "Excelentíssimo Senhor Doutor Juiz"
2. **SENTENÇA** - Decisão judicial de primeira instância
3. **ACÓRDÃO** - Decisão de tribunal colegial
4. **CONTESTAÇÃO** - Resposta do réu
5. **RÉPLICA** - Resposta à contestação
6. **EMBARGOS** - Embargos de declaração
7. **DESPACHO** - Ordem processual
8. **DECISÃO** - Decisão interlocutória
9. **CERTIDÃO** - Atestado de fatos processuais
10. **ATA_DE_AUDIÊNCIA** - Registro de audiência
11. **ANEXOS** - Documentos anexados (procuração, contratos, etc)
12. **INDETERMINADO** - Fallback

### Formato de Saída (semantic_structure.json)
```json
{
  "doc_id": "processo_123",
  "total_pages": 50,
  "total_sections": 8,
  "pages": [
    {"page": 1, "type": "PETICAO_INICIAL", "confidence": 0.92, "is_section_start": true}
  ],
  "sections": [
    {"section_id": 1, "type": "PETICAO_INICIAL", "start_page": 1, "end_page": 15, "confidence": 0.92}
  ],
  "taxonomy_version": "1.0.0"
}
```

---

## 8. CONTEXT STORE (Aprendizado)

### Funcionalidade
- Armazena padrões observados durante processamento
- Busca padrões similares via cosine similarity (threshold: 0.85)
- Sugere engine e bbox para páginas similares
- Auto-depreca padrões após 3 divergências

### API (context/store.py)
```python
from src.context import ContextStore

store = ContextStore(db_path=Path("context.db"))
caso = store.get_or_create_caso("0001234-56.2024.8.26.0001", "pje")

# Buscar padrão similar
hint = store.find_similar_pattern(
    caso_id=caso.id,
    signature_vector=[0.1, 0.2, ...],  # 10 features
    pattern_type=PatternType.HEADER
)

# Aprender com resultado
store.learn_from_page(
    caso_id=caso.id,
    signature=signature,
    result=observation_result,
    hint=hint
)
```

### Engine-Aware Updates
- Engine inferior NÃO sobrescreve engine superior
- Ranking: Marker (1.0) > PDFPlumber (0.9) > Tesseract (0.7)

---

## 9. DEPENDÊNCIAS (requirements.txt)

```
# Core
pdfplumber>=0.11.0
pillow>=12.0.0
typer>=0.20.0
rich>=14.0.0
pydantic>=2.0.0

# Vision Pipeline (step_02)
pdf2image>=1.16.0
opencv-python-headless>=4.8.0
numpy>=1.24.0

# OCR
pytesseract>=0.3.10

# Outros
psutil>=5.9.0
```

### Requisitos de Sistema
```bash
# Tesseract OCR (para PDFs escaneados)
sudo apt install tesseract-ocr tesseract-ocr-por

# Poppler (para pdf2image)
sudo apt install poppler-utils
```

---

## 10. FORMATO DOS OUTPUTS

### layout.json (Step 01)
```json
{
  "doc_id": "processo",
  "total_pages": 50,
  "pages": [
    {
      "page_num": 1,
      "type": "NATIVE",
      "complexity": "native_clean",
      "recommended_engine": "pdfplumber",
      "needs_cleaning": false,
      "safe_bbox": [0, 0, 590, 832],
      "has_tarja": false,
      "char_count": 1450
    },
    {
      "page_num": 2,
      "type": "RASTER_NEEDED",
      "complexity": "raster_dirty",
      "recommended_engine": "marker",
      "needs_cleaning": true,
      "cleaning_reason": ["watermark_detected"],
      "safe_bbox": [20, 0, 570, 832],
      "has_tarja": true,
      "tarja_x_cut": 570.0,
      "char_count": 12
    }
  ]
}
```

### final.md (Step 03)
```markdown
## [[PAGE_001]] [TYPE: NATIVE]
TRIBUNAL REGIONAL FEDERAL DA 3ª REGIÃO
Seção Judiciária de São Paulo
...

## [[PAGE_002]] [TYPE: OCR]
PODER JUDICIÁRIO
JUSTIÇA FEDERAL
...
```

### final_tagged.md (Step 04)
```markdown
---
### INICIO DE SECAO: PETICAO_INICIAL
## [[PAGE_001]] [TYPE: NATIVE] [SEMANTIC: PETICAO_INICIAL] [CONF: 0.92]
EXCELENTÍSSIMO SENHOR DOUTOR JUIZ...
```

---

## 11. FLUXO PARA INTERFACE

### Workflow Recomendado para UI

```
┌─────────────────────────────────────────────────────────────┐
│  1. UPLOAD DO PDF                                           │
│     - Aceitar arquivo PDF                                   │
│     - Mostrar preview (primeira página)                     │
│     - Exibir metadados (tamanho, páginas)                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  2. CONFIGURAÇÃO (Opcional)                                 │
│     - Sistema judicial: [Auto-detect ▼] PJE/ESAJ/STF/etc   │
│     - Blacklist customizada: [textarea]                     │
│     - Formato de saída: [Text ▼] Markdown/JSON             │
│     - Aprendizado: [☐] Ativar Context Store                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  3. PROCESSAMENTO (Progress Bar)                            │
│     [████████░░░░░░░░░░░░] 40% - Analisando layout...      │
│                                                             │
│     Steps:                                                  │
│     ✓ Cartógrafo (layout.json)        [0.5s]               │
│     ⏳ Saneador (imagens)              [em progresso]       │
│     ○ Extrator (final.md)                                   │
│     ○ Bibliotecário (structure.json)                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  4. RESULTADO                                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  RESUMO                                              │   │
│  │  Sistema: PJe - Processo Judicial Eletrônico        │   │
│  │  Confiança: 95%                                      │   │
│  │  Redução: 21.5% (125,000 → 98,125 chars)            │   │
│  │  Páginas: 50 (45 NATIVE, 5 OCR)                     │   │
│  │  Seções: 8 peças processuais                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  SEÇÕES IDENTIFICADAS                                │   │
│  │  1. Petição Inicial (pág 1-15) [conf: 0.92]         │   │
│  │  2. Contestação (pág 16-28) [conf: 0.88]            │   │
│  │  3. Réplica (pág 29-35) [conf: 0.85]                │   │
│  │  4. Sentença (pág 36-42) [conf: 0.95]               │   │
│  │  5. Anexos (pág 43-50) [conf: 0.78]                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  TEXTO EXTRAÍDO                                      │   │
│  │  [Tabs: Completo | Por Seção | Raw Markdown]        │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │ TRIBUNAL REGIONAL FEDERAL DA 3ª REGIÃO      │    │   │
│  │  │ Seção Judiciária de São Paulo               │    │   │
│  │  │ ...                                          │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [📥 Download TXT] [📥 Download MD] [📥 Download JSON]     │
└─────────────────────────────────────────────────────────────┘
```

### Integração com Backend

```python
# Exemplo de API endpoint (FastAPI)
from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import tempfile

from main import LegalTextExtractor

app = FastAPI()
extractor = LegalTextExtractor()

@app.post("/extract")
async def extract_pdf(
    file: UploadFile = File(...),
    system: str = None,
    output_format: str = "json"
):
    # Salvar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        # Processar
        result = extractor.process_pdf(
            pdf_path=tmp_path,
            system=system
        )

        # Retornar resultado
        return {
            "success": True,
            "system": result.system,
            "system_name": result.system_name,
            "confidence": result.confidence,
            "original_length": result.original_length,
            "final_length": result.final_length,
            "reduction_pct": result.reduction_pct,
            "patterns_removed": len(result.patterns_removed),
            "text": result.text if output_format == "text" else None,
            "sections": [
                {
                    "type": s.type,
                    "content": s.content,
                    "confidence": s.confidence
                }
                for s in result.sections
            ] if output_format == "json" else None
        }
    finally:
        tmp_path.unlink()  # Limpar arquivo temporário

@app.get("/systems")
def list_systems():
    """Lista sistemas judiciais suportados"""
    return {
        "systems": [
            {"code": "pje", "name": "PJe - Processo Judicial Eletrônico"},
            {"code": "esaj", "name": "ESAJ - Sistema de Automação da Justiça"},
            {"code": "eproc", "name": "EPROC - Sistema de Processo Eletrônico"},
            {"code": "projudi", "name": "PROJUDI - Processo Judicial Digital"},
            {"code": "stf", "name": "STF - Supremo Tribunal Federal"},
            {"code": "stj", "name": "STJ - Superior Tribunal de Justiça"},
        ]
    }
```

---

## 12. CONSIDERAÇÕES IMPORTANTES

### Performance
| Operação | Tempo Médio | Notas |
|----------|-------------|-------|
| Step 01 (Layout) | ~50ms/página | Apenas pdfplumber |
| Step 02 (Vision) | ~200ms/página | Só para RASTER_NEEDED |
| Step 03 (Extract) | ~500ms/página | PDFPlumber ou OCR |
| Step 04 (Classify) | ~100ms total | Regex matching |
| **Total (NATIVE)** | ~0.6s/página | Sem OCR |
| **Total (com OCR)** | ~1.5s/página | Com Tesseract |

### Limitações Atuais
1. **Marker Engine**: Stub (NotImplementedError) - aguarda sistema com ≥8GB RAM
2. **OCR**: Apenas Tesseract implementado
3. **Context Store**: schema.sql precisa ser criado

### Erros Comuns
```python
# PDF escaneado sem images_dir
ValueError: "Página X é RASTER_NEEDED mas images_dir não foi fornecido"

# Tesseract não instalado
RuntimeError: "Tesseract não encontrado. Instale com: sudo apt install tesseract-ocr"

# PDF corrompido
pdfplumber.exceptions.PDFSyntaxError: "..."
```

---

## 13. CHECKLIST PARA IMPLEMENTAÇÃO DA INTERFACE

### Funcionalidades Essenciais
- [ ] Upload de PDF (drag & drop + botão)
- [ ] Seleção de sistema judicial (dropdown com auto-detect)
- [ ] Progress bar durante processamento
- [ ] Exibição do texto extraído (com syntax highlighting)
- [ ] Download em múltiplos formatos (TXT, MD, JSON)
- [ ] Exibição de estatísticas (redução, confiança, padrões)

### Funcionalidades Avançadas
- [ ] Preview do PDF original (lado a lado com texto)
- [ ] Navegação por seções/peças processuais
- [ ] Blacklist customizada (textarea)
- [ ] Histórico de processamentos
- [ ] Processamento em lote (múltiplos PDFs)
- [ ] Context Store (aprendizado entre documentos do mesmo caso)

### UX Recomendações
- Mostrar preview da primeira página durante upload
- Indicar claramente se PDF é NATIVE ou precisa OCR
- Permitir copiar texto de seções específicas
- Exportar apenas seções selecionadas
- Destacar visualmente as seções no texto

---

## 14. EXEMPLO DE EXECUÇÃO COMPLETA

```bash
# 1. Preparar ambiente
cd /home/user/Claude-Code-Projetos/agentes/legal-text-extractor
source .venv/bin/activate

# 2. Processar PDF de exemplo
python -c "
from pathlib import Path
from main import LegalTextExtractor

extractor = LegalTextExtractor()
result = extractor.process_pdf('test-documents/fixtures/fixture_test.pdf')

print('=== RESULTADO ===')
print(f'Sistema: {result.system_name}')
print(f'Confiança: {result.confidence}%')
print(f'Redução: {result.reduction_pct:.1f}%')
print(f'Original: {result.original_length:,} chars')
print(f'Final: {result.final_length:,} chars')
print(f'Padrões removidos: {len(result.patterns_removed)}')
print()
print('=== PRIMEIROS 500 CARACTERES ===')
print(result.text[:500])
"
```

---

**FIM DO PROMPT**

Use este documento como referência completa para criar a interface/app que integra com o Legal Text Extractor. O sistema está pronto para uso programático via `main.py` ou via CLI com os steps individuais.

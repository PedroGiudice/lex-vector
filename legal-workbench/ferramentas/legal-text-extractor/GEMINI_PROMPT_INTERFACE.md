# PROMPT PARA GEMINI - Criar Interface/App do Legal Text Extractor

## CONTEXTO

Você vai criar uma interface/aplicação para executar o **Legal Text Extractor**, um sistema de extração de texto de documentos jurídicos brasileiros. Este documento contém TODA a informação necessária para entender o workflow e integrar o extrator de forma eficiente.

---

## ⚠️ ESTADO ATUAL DO SISTEMA & API

> **CRÍTICO**: O sistema possui dois pontos de entrada. Você deve usar APENAS O SEGUNDO.

### ❌ API 1: `LegalTextExtractor` (main.py) - NÃO USAR
- Legado. Não suporta os motores avançados (Marker/OCR) nem callback de progresso. Ignore.

### ✅ API 2: `PipelineOrchestrator` (src/pipeline/orchestrator.py) - TARGET
- **Arquitetura:** Pipeline completo de 4 estágios.
- **Motores:** Suporta PDFPlumber, Tesseract e **Marker (10GB RAM)**.
- **Observabilidade:** O método `process(pdf_path, progress_callback=...)` agora aceita uma função de callback para reportar progresso em tempo real.
- **Uso Obrigatório:** Sua interface deve instanciar e usar esta classe.

### REQUISITO DE ARQUITETURA
1. Todos os 3 engines funcionam (PDFPlumber, Tesseract, Marker).
2. O `PipelineOrchestrator` deve ser mantido em **cache** (memória) para não recarregar modelos pesados.

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
/home/user/Claude-Code-Projetos/ferramentas/legal-text-extractor/
```

## 1.1 AMBIENTE DE EXECUÇÃO & TECH STACK (MANDATÓRIO)

1.  **Framework:** Streamlit (Python puro).
2.  **Ambiente Host:** WSL2 (Ubuntu 24.04).
    * Use sempre `pathlib.Path` para caminhos (ex: `/tmp/...`).
    * **NÃO** use caminhos Windows (`C:\`).
3.  **Ponte de Arquivos (Memory -> Disk):**
    * O Streamlit recebe uploads como `BytesIO` (memória).
    * O `PipelineOrchestrator` exige um `pathlib.Path` (disco).
    * **Sua Solução:** Crie uma função `save_temp_file` que salve o upload em `/tmp/`, retorne o `Path` para o processamento e limpe depois.
4.  **Gestão de Recursos (CRÍTICO):**
    * Use `@st.cache_resource` para carregar o `PipelineOrchestrator` (evita travar o PC recarregando o Marker de 10GB).
    * Use `st.session_state` para manter os resultados na tela ao trocar de abas.

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
│  Função: Extrai texto com escalonamento automático:         │
│          - PDFPlumber: texto nativo (rápido, 0.5GB RAM)     │
│          - Tesseract OCR: scans simples (1GB RAM)           │
│          - Marker: PDFs complexos (MELHOR, 10-12GB RAM)     │
│  NOTA: Marker é o engine PREMIUM - maior qualidade,         │
│        preserva layout, tabelas e formatação complexa       │
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
├── main.py                          # Entry point (API simples)
├── requirements.txt                 # Dependências Python
├── src/
│   ├── config.py                    # Configurações centralizadas
│   │
│   ├── steps/                       # PIPELINE DE 4 ESTÁGIOS
│   │   ├── step_01_layout.py        # Cartógrafo (19KB)
│   │   ├── step_02_vision.py        # Saneador (12KB)
│   │   ├── step_03_extract.py       # Extrator (17KB)
│   │   └── step_04_classify.py      # Bibliotecário (10KB)
│   │
│   ├── engines/                     # MOTORES DE EXTRAÇÃO
│   │   ├── base.py                  # Interface ExtractionEngine
│   │   ├── pdfplumber_engine.py     # ✅ Funcional (0.5GB RAM)
│   │   ├── tesseract_engine.py      # ✅ Funcional (1GB RAM)
│   │   ├── marker_engine.py         # ✅ Engine PREMIUM (10GB RAM)
│   │   ├── selector.py              # Escalação progressiva
│   │   └── cleaning_engine.py       # Limpeza adaptativa
│   │
│   ├── core/                        # LÓGICA PRINCIPAL
│   │   ├── cleaner.py               # DocumentCleaner
│   │   ├── detector.py              # Detecção de sistema judicial
│   │   ├── patterns.py              # 75+ padrões regex
│   │   └── intelligence/            # Módulos de IA
│   │       ├── segmenter.py         # Segmentação de peças
│   │       └── definitions.py       # Taxonomia legal
│   │
│   ├── context/                     # APRENDIZADO
│   │   ├── store.py                 # ContextStore (SQLite)
│   │   ├── models.py                # Data models
│   │   └── signature.py             # Cálculo de assinaturas
│   │
│   ├── extractors/                  # EXTRATORES LEGADOS
│   │   ├── text_extractor.py        # Extração de texto
│   │   └── ocr_extractor.py         # ⚠️ NotImplementedError
│   │
│   ├── exporters/                   # EXPORTAÇÃO
│   │   ├── text.py                  # Export .txt
│   │   ├── markdown.py              # Export .md
│   │   └── json.py                  # Export .json
│   │
│   ├── pipeline/                    # ORQUESTRAÇÃO
│   │   └── orchestrator.py          # PipelineOrchestrator (usar este!)
│   │
│   ├── analyzers/                   # Analisadores auxiliares
│   ├── learning/                    # A/B testing, métricas
│   ├── memory/                      # Sessões de memória
│   ├── prompts/                     # Templates de prompts
│   └── schemas/                     # Schemas de validação
│
├── inputs/                          # PDFs de entrada
├── outputs/                         # Resultados processados
│   └── {doc_id}/
│       ├── layout.json
│       ├── images/
│       ├── final.md
│       └── semantic_structure.json
└── tests/                           # Testes unitários
```

---

## 4. API PRINCIPAL - Como Usar (Backend)

### 4.1 Uso via PipelineOrchestrator (Obrigatório)

```python
from pathlib import Path
from src.pipeline.orchestrator import PipelineOrchestrator

# 1. Instanciar (Idealmente em cache)
orchestrator = PipelineOrchestrator()

# 2. Definir Callback de Progresso (para UI)
def meu_callback(current, total, msg):
    print(f"[{current}/{total}] {msg}")

# 3. Processar
result = orchestrator.process(
    pdf_path=Path("/tmp/temp_upload.pdf"),
    progress_callback=meu_callback
)

# 4. Acessar Resultados (PipelineResult)
if result.success:
    print(f"Páginas: {result.total_pages}")
    print(f"Texto Final: {result.text[:100]}...")
    print(f"Metadados: {result.metadata}") # Contém system_name, confidence, etc
    print(f"Avisos: {result.warnings}")
4.2 Objeto de Retorno (PipelineResult)
O orquestrador retorna um objeto PipelineResult (ver src/pipeline/orchestrator.py), contendo:

text: String final (Markdown) com o conteúdo extraído.

layout: Dict com estrutura das páginas (usado para debug).

metadata: Dict contendo system_name, confidence, doc_id, etc.

success: Booleano indicando se o pipeline rodou até o fim.

warnings: Lista de strings com erros não-fatais.

 '''
---

## 5. ENGINES DE EXTRAÇÃO

### Hierarquia de Qualidade
| Engine | RAM | Qualidade | Uso |
|--------|-----|-----------|-----|
| **Marker** ⭐ | 10-12GB | 1.0 (MELHOR) | PDFs complexos, tabelas, layout preservado |
| **PDFPlumber** | 0.5GB | 0.9 | Texto nativo (não escaneado) |
| **Tesseract** | 1GB | 0.7 | OCR para scans simples |

> **IMPORTANTE**: Marker é o engine PREMIUM do sistema. Quando disponível (RAM suficiente),
> produz resultados significativamente superiores para documentos complexos.

### Seleção Automática (engine_selector.py)
```python
# Lógica de seleção:
# 1. Se PDF tem ≥80% texto nativo → PDFPlumber (rápido)
# 2. Se PDF escaneado/complexo + RAM ≥10GB → Marker (MELHOR resultado)
# 3. Fallback se RAM insuficiente → Tesseract OCR
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

# Marker Engine (PREMIUM - requer 10-12GB RAM)
marker-pdf>=1.0.0

# Sistema
psutil>=5.9.0
```

> **NOTA**: O `marker-pdf` deve ser instalado separadamente:
> ```bash
> pip install marker-pdf
> ```
> Instalação demora ~5min e baixa modelos de ML (~2GB).

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

## 11. ARQUITETURA DA INTERFACE (STREAMLIT)

O arquivo `app.py` deve operar como um "Direct Import Monolith" (sem APIs externas), importando diretamente de `src/`.

### Estrutura Lógica do Código
1.  **Setup & Imports:**
    ```python
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent)) # Garante visibilidade do src/
    from src.pipeline.orchestrator import PipelineOrchestrator
    ```

2.  **Carregamento Seguro (Cache):**
    Instancie o orquestrador dentro de uma função com `@st.cache_resource`.

3.  **Callback de Progresso (Visual):**
    Crie uma função para conectar o backend à UI:
    ```python
    def update_ui(current, total, message):
        # Atualiza st.progress() e st.status()
        pass
    
    # No botão de processar:
    orchestrator.process(pdf_path, progress_callback=update_ui)
    ```

4.  **Layout da Tela:**
    * **Sidebar:** Upload, Seletor de Sistema (Auto/PJE/ESAJ...), Botão "Processar".
    * **Área Principal (Status):** Use `st.status` expandido para mostrar o log do callback ("Lendo página 1...", "Extraindo com Marker...").
    * **Área Principal (Abas de Resultado):**
        * **Tab 1 Documento:** Texto final (`result.text`).
        * **Tab 2 Estrutura:** JSON (`result.sections` e `result.metadata`).
        * **Tab 3 Debug:** Tabela com `result.patterns_removed` e métricas de confiança.

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

### Requisitos de Sistema para Marker
1. **Marker Engine**: Requer sistema com ≥10GB RAM dedicada (WSL2 ou nativo)
2. **OCR Fallback**: Tesseract usado quando RAM insuficiente para Marker
3. **Context Store**: Aprendizado automático de padrões entre documentos

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

## 14. EXEMPLO DE FLUXO INTERNO (Mental Model)

```python
# O App deve simular este fluxo:

# 1. Recebe arquivo do Streamlit (BytesIO)
uploaded_file = st.file_uploader(...)

# 2. Salva em disco (WSL2 path)
temp_path = save_temp_file(uploaded_file)

# 3. Recupera Orquestrador do Cache
orchestrator = get_orchestrator()

# 4. Executa com Callback visual
with st.status("Processando...") as status:
    def update_bar(current, total, msg):
        status.update(label=f"{msg} ({current}/{total})")
        my_bar.progress(current / total)
    
    result = orchestrator.process(temp_path, progress_callback=update_bar)

# 5. Exibe resultados
st.markdown(result.text)
st.json(result.metadata)

```

---

**FIM DO PROMPT**
   ```
Use este documento como referência completa para criar a interface/app que integra com o Legal Text Extractor. O sistema está pronto para uso programático via `main.py` ou via CLI com os steps individuais.
   ```

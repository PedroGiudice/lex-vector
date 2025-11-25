"""
MEMÓRIA DE SESSÃO: 2025-11-24
Legal Text Extractor - Refatoração Pipeline 3 Estágios

Este arquivo documenta as decisões arquiteturais e estado do projeto
para continuidade entre sessões de desenvolvimento.
"""

# =============================================================================
# DECISÕES ARQUITETURAIS CRÍTICAS
# =============================================================================

DECISAO_REMOCAO_SDK = """
REMOVIDO: Uso de Claude API/SDK para separação de seções
ADOTADO: Pipeline algorítmica 100% local (Python/OpenCV/Tesseract)
MOTIVO: Custo proibitivo de LLM para autos volumosos (5.000+ páginas)
"""

FILOSOFIA_PROJETO = """
A "inteligência" de extração deve ser ALGORÍTMICA (Python/OpenCV),
NÃO baseada em chamadas de API.

Interface final será TUI (textual), MAS NÃO AGORA.
Foco atual: ENGINE (scripts de backend).
"""

# =============================================================================
# ARQUITETURA IMPLEMENTADA
# =============================================================================

PIPELINE_3_ESTAGIOS = {
    "step_01_layout": {
        "nome": "Cartógrafo",
        "arquivo": "src/steps/step_01_layout.py",
        "linhas": 280,
        "algoritmo": "Histograma de densidade de caracteres",
        "output": "outputs/{doc_id}/layout.json",
        "status": "COMPLETO",
    },
    "step_02_vision": {
        "nome": "Saneador",
        "arquivo": "src/steps/step_02_vision.py",
        "linhas": 390,
        "algoritmo": "OpenCV: Grayscale -> Otsu -> Denoise",
        "output": "outputs/{doc_id}/images/page_XX.png",
        "status": "COMPLETO",
    },
    "step_03_extract": {
        "nome": "Extrator",
        "arquivo": "src/steps/step_03_extract.py",
        "linhas": 460,
        "algoritmo": "pdfplumber (NATIVE) + Tesseract (OCR)",
        "output": "outputs/{doc_id}/final.md",
        "status": "COMPLETO",
    },
}

# =============================================================================
# ARQUIVOS PRESERVADOS (NÃO MODIFICAR)
# =============================================================================

CORE_PRESERVADO = [
    "src/core/patterns.py",    # 75+ regex de limpeza
    "src/core/cleaner.py",     # Orquestrador de limpeza
    "src/core/detector.py",    # Auto-detecção de sistemas
    "src/core/normalizer.py",  # Normalização pós-limpeza
]

# =============================================================================
# ARQUIVOS A IGNORAR (CÓDIGO LEGADO)
# =============================================================================

CODIGO_LEGADO_NAO_USAR = [
    "src/analyzers/",   # Claude API (não usar)
    "src/learning/",    # Claude API (não usar)
    "src/prompts/",     # Claude prompts (não usar)
]

# =============================================================================
# PDFS DE TESTE DISPONÍVEIS
# =============================================================================

PDFS_TESTE = {
    "fixture_test.pdf": {
        "tamanho": "178KB",
        "paginas": 3,
        "tipos": ["NATIVE", "RASTER_NEEDED", "TARJA"],
        "proposito": "Teste da pipeline completa",
    },
    "1057607-11.2024.8.26.0002.pdf": {
        "tamanho": "25.8 MB",
        "sistema": "PJe",
        "proposito": "Teste com tarjas laterais reais",
    },
    "Forscher x Salesforce - íntegra 25.09.2025.PDF": {
        "tamanho": "2.5 MB",
        "sistema": "Misto",
        "proposito": "Teste com conteúdo digital variado",
    },
    "Luiz Victor x Salesforce - Inicial e docs - 04.11.2025.pdf": {
        "tamanho": "43.6 MB",
        "sistema": "Misto",
        "proposito": "Teste com volume grande (inicial + documentos)",
    },
}

# =============================================================================
# DEPENDÊNCIAS NECESSÁRIAS
# =============================================================================

DEPENDENCIAS_PYTHON = [
    "pdfplumber",
    "pdf2image",
    "opencv-python-headless",
    "numpy",
    "pytesseract",
    "typer",
    "pillow",
    "reportlab",
]

DEPENDENCIAS_SISTEMA = [
    "poppler-utils",           # sudo apt install poppler-utils
    "tesseract-ocr",           # sudo apt install tesseract-ocr
    "tesseract-ocr-por",       # sudo apt install tesseract-ocr-por
]

# =============================================================================
# PRÓXIMOS PASSOS
# =============================================================================

PROXIMOS_PASSOS = """
1. Instalar dependências no ambiente de casa:
   pip install pdf2image opencv-python-headless numpy
   sudo apt install poppler-utils tesseract-ocr tesseract-ocr-por

2. Testar pipeline com fixture:
   cd agentes/legal-text-extractor
   source .venv/bin/activate
   python src/steps/step_01_layout.py test-documents/fixture_test.pdf

3. Validar output final.md

4. Testar com PDFs reais (os 3 adicionados)
"""

# =============================================================================
# OUTPUT ESPERADO (final.md)
# =============================================================================

FORMATO_OUTPUT = """
## [[PAGE_001]] [TYPE: NATIVE]
(Conteúdo textual limpo da página 1...)

## [[PAGE_002]] [TYPE: OCR]
(Conteúdo extraído via Tesseract da página 2...)

## [[PAGE_003]] [TYPE: NATIVE]
(Conteúdo com tarja removida da página 3...)

PROPÓSITO: Preservar fronteiras de página para segmentação semântica futura.
"""

# =============================================================================
# COMMITS REALIZADOS NESTA SESSÃO
# =============================================================================

COMMITS = [
    {
        "hash": "baee1c4",
        "mensagem": "feat(legal-text-extractor): adiciona gerador de fixtures e dependências vision",
    },
    {
        "hash": "8141790",
        "mensagem": "feat(legal-text-extractor): implementa step_03_extract.py (Extrator)",
    },
]

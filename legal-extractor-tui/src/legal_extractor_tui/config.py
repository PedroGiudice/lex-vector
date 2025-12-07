"""Configuration constants for Legal Extractor TUI."""

from pathlib import Path

# App metadata
APP_NAME = "Legal Extractor TUI"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Extract and clean text from Brazilian legal documents"

# Paths
LEGAL_EXTRACTOR_PATH = Path("/home/cmr-auto/claude-work/repos/Claude-Code-Projetos/ferramentas/legal-text-extractor")
STYLES_DIR = Path(__file__).parent / "styles"

# Supported judicial systems
JUDICIAL_SYSTEMS = {
    "auto": ("Automático", "Detecta automaticamente o sistema judicial"),
    "pje": ("PJE", "Processo Judicial Eletrônico - CNJ"),
    "esaj": ("E-SAJ", "Sistema do TJSP"),
    "eproc": ("EPROC", "Sistema do TRF4"),
    "projudi": ("PROJUDI", "Processo Digital"),
    "stf": ("STF", "Supremo Tribunal Federal"),
    "stj": ("STJ", "Superior Tribunal de Justiça"),
}

# Output formats
OUTPUT_FORMATS = {
    "text": ("Texto", ".txt", "Texto simples sem formatação"),
    "markdown": ("Markdown", ".md", "Texto formatado com seções"),
    "json": ("JSON", ".json", "Estruturado com metadados"),
}

# Processing stages
EXTRACTION_STAGES = [
    ("extracting", "Extraindo texto", "Lendo conteúdo do PDF..."),
    ("cleaning", "Limpando", "Removendo ruídos e assinaturas..."),
    ("analyzing", "Analisando", "Identificando seções do documento..."),
]

# Colors (for non-theme elements)
COLORS = {
    "success": "#50fa7b",
    "warning": "#f1fa8c",
    "error": "#ff5555",
    "info": "#8be9fd",
}

# ASCII Art logo
LOGO_SMALL = '''
╔═══════════════════════════════════╗
║  LEGAL EXTRACTOR TUI  v0.1.0      ║
║  Extração de Documentos Jurídicos ║
╚═══════════════════════════════════╝
'''

LOGO_LARGE = '''
██╗     ███████╗ ██████╗  █████╗ ██╗
██║     ██╔════╝██╔════╝ ██╔══██╗██║
██║     █████╗  ██║  ███╗███████║██║
██║     ██╔══╝  ██║   ██║██╔══██║██║
███████╗███████╗╚██████╔╝██║  ██║███████╗
╚══════╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
        EXTRACTOR TUI v0.1.0
'''

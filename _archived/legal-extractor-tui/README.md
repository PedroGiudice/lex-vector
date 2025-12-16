# Legal Extractor TUI

> ⚠️ **DEPRECADO**: Este projeto foi descontinuado. Use `legal-workbench/ferramentas/legal-text-extractor/` como a implementação ativa.

Terminal User Interface (TUI) for Brazilian Legal Document Text Extraction.

## Features

- Extract text from Brazilian legal PDFs (PJe, ESAJ, eProc, Projudi, STF, STJ)
- Automatic judicial system detection
- Intelligent text cleaning and noise removal
- Optional section analysis using Claude AI
- Export to multiple formats (TXT, Markdown, JSON)
- Real-time progress tracking

## Installation

```bash
# Create and activate virtual environment (required on Ubuntu 24.04+)
cd legal-extractor-tui
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e ".[dev]"
```

## Usage

```bash
# Always activate venv first
source .venv/bin/activate

# Run with default theme (neon)
python -m legal_extractor_tui

# Run with specific theme
python -m legal_extractor_tui --theme matrix

# Run with a PDF file
python -m legal_extractor_tui documento.pdf

# Available themes: neon, matrix, synthwave, dark, light
```

## Requirements

- Python 3.11+
- Textual (TUI framework)
- pdfplumber (PDF extraction)
- Claude API key (optional, for section analysis)

## Development

```bash
# Setup (one-time)
cd legal-extractor-tui
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/
```

## License

MIT

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

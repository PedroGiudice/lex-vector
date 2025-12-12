# Configuration Update Summary

**Date:** 2025-11-27
**Status:** ✅ Complete

## Files Updated

### 1. `pyproject.toml`
**Changes:**
- Project name: `tui-template` → `legal-extractor-tui`
- Description: Updated to "TUI for Brazilian Legal Document Text Extraction"
- Added legal-specific keywords: `["tui", "legal", "pdf", "extraction", "textual"]`
- Added PyPI classifiers for Legal Industry
- Added dependencies:
  - `pdfplumber>=0.11.0` (PDF text extraction)
  - `pillow>=10.0.0` (Image processing)
- Updated entry point: `legal-extractor-tui` → `legal_extractor_tui.__main__:main`
- Versioned dev dependencies (pytest>=8.0.0, ruff>=0.1.0, mypy>=1.8.0)
- Simplified mypy config to `strict = true`

### 2. `src/legal_extractor_tui/__init__.py`
**Changes:**
- Docstring: Updated to describe legal document extraction
- Added `__app_name__` and `__author__` metadata
- Changed import: `TUIApp` → `LegalExtractorApp`
- Updated `__all__` exports

### 3. `src/legal_extractor_tui/__main__.py`
**Changes:**
- Simplified argument parsing (removed NoReturn type, parse_args function)
- Theme choices: Short names (`neon`, `matrix`, etc.) instead of full names
- Added `file` positional argument for initial PDF file
- Added theme_map to convert short names to full theme names
- Updated app import and instantiation: `TUIApp` → `LegalExtractorApp`
- Passes `initial_file` parameter to app constructor

### 4. `src/legal_extractor_tui/config.py`
**Changes:**
- Complete rewrite for legal domain
- Added legal extractor path constant
- Added `JUDICIAL_SYSTEMS` dictionary (7 Brazilian court systems)
- Added `OUTPUT_FORMATS` dictionary (text, markdown, json)
- Added `EXTRACTION_STAGES` list (extracting, cleaning, analyzing)
- Added semantic color constants
- Added ASCII art logos (small and large)
- Removed generic TUI template constants

## New Configuration Constants

### Judicial Systems
```python
JUDICIAL_SYSTEMS = {
    "auto": ("Automático", "Detecta automaticamente o sistema judicial"),
    "pje": ("PJE", "Processo Judicial Eletrônico - CNJ"),
    "esaj": ("E-SAJ", "Sistema do TJSP"),
    "eproc": ("EPROC", "Sistema do TRF4"),
    "projudi": ("PROJUDI", "Processo Digital"),
    "stf": ("STF", "Supremo Tribunal Federal"),
    "stj": ("STJ", "Superior Tribunal de Justiça"),
}
```

### Output Formats
```python
OUTPUT_FORMATS = {
    "text": ("Texto", ".txt", "Texto simples sem formatação"),
    "markdown": ("Markdown", ".md", "Texto formatado com seções"),
    "json": ("JSON", ".json", "Estruturado com metadados"),
}
```

### Extraction Stages
```python
EXTRACTION_STAGES = [
    ("extracting", "Extraindo texto", "Lendo conteúdo do PDF..."),
    ("cleaning", "Limpando", "Removendo ruídos e assinaturas..."),
    ("analyzing", "Analisando", "Identificando seções do documento..."),
]
```

## CLI Usage

### Before
```bash
tui-app --theme vibe-neon --dev
```

### After
```bash
# No file
legal-extractor-tui --theme neon --dev

# With initial file
legal-extractor-tui --theme matrix documento.pdf

# Help
legal-extractor-tui --help
```

## Dependencies Added

### Production
- `pdfplumber>=0.11.0` - PDF text extraction library
- `pillow>=10.0.0` - Image processing for PDF rendering

### Development
- All dev dependencies now have minimum versions specified

## Next Steps

1. Update `app.py` to implement `LegalExtractorApp` class
2. Create widgets for:
   - File browser (PDF selection)
   - Judicial system selector
   - Output format selector
   - Progress indicator (3 stages)
   - Preview panel (extracted text)
3. Integrate with existing legal-text-extractor agent
4. Create tests for extraction pipeline
5. Update README.md with legal extractor specific documentation

## Validation

```bash
# Verify package structure
cd /home/cmr-auto/claude-work/repos/Claude-Code-Projetos/legal-extractor-tui
grep "legal-extractor-tui" pyproject.toml

# Check config constants
head -20 src/legal_extractor_tui/config.py

# List all package files
find src/legal_extractor_tui -name "*.py"
```

## Files Not Modified

The following files were **not changed** and may still reference old names:
- `src/legal_extractor_tui/app.py` (still imports TUIApp base)
- All widget files in `src/legal_extractor_tui/widgets/`
- All screen files in `src/legal_extractor_tui/screens/`
- All theme files in `src/legal_extractor_tui/themes/`
- Tests in `tests/`

These will need to be updated in subsequent tasks.

---

**Status:** Configuration layer complete. Ready for app implementation.

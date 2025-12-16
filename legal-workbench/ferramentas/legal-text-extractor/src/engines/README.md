# Multi-Engine Architecture for PDF Extraction

## Overview

This module implements a flexible, resource-aware architecture for PDF text extraction with automatic engine selection and fallback.

### Key Features

1. **Multiple extraction engines** with different capabilities:
   - `pdfplumber`: Fast native text extraction (0.5GB RAM)
   - `tesseract`: OCR for scanned documents (1GB RAM)
   - `marker`: High-quality layout-preserving extraction (8GB RAM, stub)
   - `surya`, `docling`: Additional OCR options (future)

2. **Automatic engine selection** based on:
   - PDF characteristics (native text ratio)
   - Available system resources (RAM)
   - Installed dependencies

3. **Graceful fallback** if primary engine fails

4. **Resource detection** to avoid crashes on low-RAM systems

## Architecture

### Base Classes (`base.py`)

```python
@dataclass
class ExtractionResult:
    text: str
    pages: int
    engine_used: str
    confidence: float  # 0.0-1.0
    metadata: dict
    warnings: list[str]

class ExtractionEngine(ABC):
    name: str
    min_ram_gb: float
    dependencies: list[str]
    
    @abstractmethod
    def extract(pdf_path) -> ExtractionResult
    
    @abstractmethod
    def is_available() -> bool
    
    def check_resources() -> tuple[bool, str]
```

### Engine Selector (`engine_selector.py`)

```python
class EngineSelector:
    def analyze_pdf(pdf_path) -> dict
    def get_available_engines() -> list[ExtractionEngine]
    def select_engine(pdf_path, force_engine=None) -> ExtractionEngine
    def extract_with_fallback(pdf_path, max_retries=3) -> ExtractionResult
```

### Selection Logic

1. **Analyze PDF**:
   - Count pages with extractable text
   - Calculate native text ratio (0.0-1.0)
   - Determine if PDF is "text-native" (>80% has text)

2. **Select Engine**:
   - If native text → `pdfplumber` (fastest)
   - If scanned AND RAM >= 8GB → `marker` (best quality)
   - Else → Best available OCR engine (`tesseract`, `surya`, `docling`)

3. **Fallback Chain**:
   - Try primary engine
   - If fails, try next available engine
   - Up to `max_retries` attempts

## Usage

### Basic Usage

```python
from engines import get_selector
from pathlib import Path

selector = get_selector()
result = selector.extract_with_fallback(Path("document.pdf"))

print(f"Extracted {len(result.text)} chars using {result.engine_used}")
print(f"Confidence: {result.confidence:.2f}")
```

### Force Specific Engine

```python
# Force tesseract even if pdfplumber would be better
result = selector.extract_with_fallback(
    Path("document.pdf"),
    force_engine="tesseract"
)
```

### Check Available Engines

```python
available = selector.get_available_engines()
for engine in available:
    print(f"{engine.name}: {engine.min_ram_gb}GB RAM required")
```

### Analyze PDF Before Extraction

```python
analysis = selector.analyze_pdf(Path("document.pdf"))
print(f"Pages: {analysis['pages']}")
print(f"Native text: {analysis['native_text_ratio']:.0%}")
print(f"Is text-native: {analysis['has_native_text']}")
```

## Implemented Engines

### PDFPlumberEngine (`pdfplumber_engine.py`)

- **Status**: Fully implemented ✓
- **RAM**: 0.5GB
- **Speed**: Fast (~1-2s per page)
- **Best for**: Native text PDFs (digital documents)
- **Limitations**: Poor on scanned documents

### TesseractEngine (`tesseract_engine.py`)

- **Status**: Fully implemented ✓
- **RAM**: 1GB
- **Speed**: Moderate (~3-5s per page)
- **Best for**: Scanned documents without native text
- **Features**:
  - Image preprocessing (grayscale, denoise, threshold)
  - Confidence scoring per page
  - Multiple language support

### MarkerEngine (`marker_engine.py`)

- **Status**: STUB (not implemented)
- **RAM**: 8GB minimum
- **Speed**: Slow but high quality
- **Best for**: Complex layouts (tables, multi-column)
- **Features** (when implemented):
  - Layout preservation
  - Markdown output with formatting
  - Table extraction
  - Image extraction

**Why stub?** Current development system has only 8GB total RAM. Marker requires ~8GB available, leaving no room for OS. Will be implemented when accessing higher-RAM system.

## Adding New Engines

1. **Create engine class** in `src/engines/your_engine.py`:

```python
from .base import ExtractionEngine, ExtractionResult

class YourEngine(ExtractionEngine):
    name = "your_engine"
    min_ram_gb = 2.0
    dependencies = ["your_package"]
    
    def is_available(self) -> bool:
        # Check if package is installed
        try:
            import your_package
            return True
        except ImportError:
            return False
    
    def extract(self, pdf_path: Path) -> ExtractionResult:
        # Your extraction logic
        text = extract_text_somehow(pdf_path)
        
        return ExtractionResult(
            text=text,
            pages=num_pages,
            engine_used=self.name,
            confidence=0.9,
            metadata={"custom_field": "value"},
        )
```

2. **Register in selector** (`engine_selector.py`):

```python
engine_specs = [
    # ... existing engines
    ("your_engine", "YourEngine"),
]
```

3. **Export in __init__.py**:

```python
from .your_engine import YourEngine

__all__ = [
    # ... existing exports
    "YourEngine",
]
```

## Design Decisions

### Why Singletons?

Both `EngineSelector` and `CleanerEngine` use singleton pattern via `get_*()` functions:

- Avoid re-importing/re-instantiating heavy dependencies
- Cache analysis results across calls
- Consistent state throughout application

### Why Separate Cleaning?

`CleanerEngine` is separate from extraction engines:

- Cleaning is PDF content-independent (works on any text)
- Extraction is PDF format-dependent (native vs scanned)
- Separation of concerns: extraction → cleaning → output

### Why Optional Dependencies?

Engines use `try/except ImportError`:

- Not all users need all engines
- Avoid forcing heavy dependencies (Tesseract, Marker)
- Graceful degradation: use what's available

## Performance Considerations

### RAM Usage

| Engine | Typical RAM | Peak RAM |
|--------|-------------|----------|
| pdfplumber | 100-200MB | 500MB |
| tesseract | 200-400MB | 1GB |
| marker | 4-6GB | 8GB+ |

### Speed (approximate, per page)

| Engine | Text PDF | Scanned PDF |
|--------|----------|-------------|
| pdfplumber | 0.1s | N/A (fails) |
| tesseract | 1s | 3-5s |
| marker | 2s | 10-15s |

### Recommendations

- **Low RAM (< 2GB)**: Use pdfplumber only
- **Moderate RAM (2-4GB)**: pdfplumber + tesseract
- **High RAM (8GB+)**: All engines including marker

## Testing

Run example:

```bash
cd examples/
python engine_selector_example.py
```

Expected output:
- Lists available engines
- Analyzes test PDFs
- Shows engine selection logic
- Demonstrates fallback behavior

## Future Enhancements

1. **Implement MarkerEngine** when higher-RAM system available
2. **Add Surya engine** for modern OCR alternative
3. **Add Docling engine** for document understanding
4. **Cache analysis results** to avoid re-analyzing same PDFs
5. **Parallel extraction** for multi-page PDFs (batch processing)
6. **Quality metrics** to compare engine outputs

## Troubleshooting

### No engines available

```
ERROR: No extraction engines available on this system
```

**Solution**: Install at least one engine:

```bash
pip install pdfplumber  # Minimal, fast
# OR
pip install pytesseract opencv-python-headless pdf2image
sudo apt install tesseract-ocr tesseract-ocr-por
```

### Marker not available

```
Engine marker unavailable: marker requires 8.0GB RAM, only 2.3GB available
```

**Solution**: This is expected on low-RAM systems. Marker is optional and other engines will be used instead.

### All engines failed

```
RuntimeError: All 3 engines failed:
  pdfplumber failed: ...
  tesseract failed: ...
```

**Solution**: Check PDF file integrity. If PDF is corrupted or password-protected, all engines may fail.

## References

- **pdfplumber**: https://github.com/jsvine/pdfplumber
- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **Marker**: https://github.com/VikParuchuri/marker
- **Surya**: https://github.com/VikParuchuri/surya
- **Docling**: https://github.com/DS4SD/docling

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

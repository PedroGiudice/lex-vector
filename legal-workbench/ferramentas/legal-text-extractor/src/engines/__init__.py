"""
Engines module for text extraction.

Architecture (Marker-only):
- MarkerEngine: Primary and ONLY extraction engine
  - Automatically detects native text vs scanned pages
  - Uses pdftext for native, Surya OCR for scanned
  - Preserves layout, tables, and structure

- MarkerConfig: Configuration options for Marker
  - disable_image_extraction: Reduces output size by ~98%
  - paginate_output: Preserves page references
  - drop_repeated_text: Removes headers/footers noise

- CleanerEngine: Post-processing for judicial system artifacts
"""

from .base import ExtractionEngine, ExtractionResult
from .cleaning_engine import CleanerEngine, DetectionResult, get_cleaner
from .marker_engine import MarkerEngine, MarkerConfig

__all__ = [
    # Base interfaces
    "ExtractionEngine",
    "ExtractionResult",

    # Primary extraction engine
    "MarkerEngine",
    "MarkerConfig",

    # Post-processing
    "CleanerEngine",
    "DetectionResult",
    "get_cleaner",
]

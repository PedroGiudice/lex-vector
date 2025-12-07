"""
Engines module for text processing.

This module provides:
- Base classes for extraction engines
- Concrete extraction engines (PDFPlumber, Tesseract, Marker)
- Cleaning engine for judicial system artifacts
- Engine selector with intelligent fallback
"""

from .base import ExtractionEngine, ExtractionResult
from .cleaning_engine import CleanerEngine, DetectionResult, get_cleaner
from .engine_selector import EngineSelector, get_selector
from .pdfplumber_engine import PDFPlumberEngine
from .tesseract_engine import TesseractEngine
from .marker_engine import MarkerEngine

__all__ = [
    # Base interfaces
    "ExtractionEngine",
    "ExtractionResult",

    # Extraction engines
    "PDFPlumberEngine",
    "TesseractEngine",
    "MarkerEngine",

    # Cleaning
    "CleanerEngine",
    "DetectionResult",
    "get_cleaner",

    # Selection
    "EngineSelector",
    "get_selector",
]

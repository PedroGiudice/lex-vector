"""
Intelligent engine selection with resource detection and fallback.

Selection strategy:
1. Detect PDF characteristics (native text ratio)
2. Check available system resources (RAM, dependencies)
3. Select optimal engine based on:
   - PDF type (text-native vs scanned)
   - Available engines
   - Resource constraints
4. Fallback chain if selected engine fails
"""

import logging
from pathlib import Path
from typing import Optional
import importlib.util
import psutil
import pdfplumber

from .base import ExtractionEngine, ExtractionResult


logger = logging.getLogger(__name__)


class EngineSelector:
    """
    Selects optimal extraction engine based on PDF characteristics and system resources.

    Workflow:
    1. analyze_pdf() - Determine if PDF has native text
    2. get_available_engines() - Check which engines can run
    3. select_engine() - Choose best engine for this PDF
    4. extract_with_fallback() - Try selected engine, fallback if needed
    """

    # Threshold for considering PDF as "text-native"
    NATIVE_TEXT_THRESHOLD = 0.8  # 80% of pages have text

    def __init__(self):
        """Initialize selector and register available engines."""
        self.engines: dict[str, type[ExtractionEngine]] = {}
        self._register_engines()

    def _register_engines(self):
        """Register all available engine classes."""
        # Try to import each engine - gracefully skip if not available
        engine_specs = [
            ("pdfplumber", "PDFPlumberEngine", ["pdfplumber"]),
            ("tesseract", "TesseractEngine", ["pytesseract", "PIL"]),
            ("marker", "MarkerEngine", ["marker"]),
            ("surya", "SuryaEngine", ["surya"]),
            ("docling", "DoclingEngine", ["docling"]),
        ]

        for module_name, class_name, deps in engine_specs:
            try:
                # Try to import the module
                module = importlib.import_module(f".{module_name}_engine", package="src.engines")
                engine_class = getattr(module, class_name)
                self.engines[engine_class.name] = engine_class
                logger.debug(f"Registered engine: {engine_class.name}")
            except ImportError as e:
                logger.debug(f"Engine {class_name} not available: {e}")
                continue

    def analyze_pdf(self, pdf_path: Path) -> dict[str, any]:
        """
        Analyze PDF characteristics to guide engine selection.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Analysis dict with:
            - pages: Total page count
            - has_native_text: True if most pages have extractable text
            - native_text_ratio: Proportion of pages with text (0.0-1.0)
            - avg_chars_per_page: Average character count per page
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            pages_with_text = 0
            total_chars = 0

            for page in pdf.pages:
                text = page.extract_text() or ""
                chars = len(text.strip())
                total_chars += chars

                # Consider page as "having text" if >50 chars
                if chars > 50:
                    pages_with_text += 1

            native_ratio = pages_with_text / total_pages if total_pages > 0 else 0.0
            avg_chars = total_chars / total_pages if total_pages > 0 else 0

            return {
                "pages": total_pages,
                "has_native_text": native_ratio >= self.NATIVE_TEXT_THRESHOLD,
                "native_text_ratio": native_ratio,
                "avg_chars_per_page": avg_chars,
            }

    def get_available_engines(self) -> list[ExtractionEngine]:
        """
        Get list of engines that can run on current system.

        Checks:
        - Dependencies are installed
        - Sufficient RAM is available

        Returns:
            List of instantiated engines, sorted by capability
        """
        available = []

        for engine_class in self.engines.values():
            try:
                engine = engine_class()
                if engine.is_available():
                    available.append(engine)
                    logger.debug(f"Engine available: {engine.name}")
                else:
                    ok, reason = engine.check_resources()
                    logger.debug(f"Engine {engine.name} unavailable: {reason}")
            except Exception as e:
                logger.warning(f"Failed to instantiate {engine_class.name}: {e}")

        # Sort by preference: marker > surya > docling > tesseract > pdfplumber
        preference_order = ["marker", "surya", "docling", "tesseract", "pdfplumber"]
        available.sort(
            key=lambda e: preference_order.index(e.name)
            if e.name in preference_order
            else 999
        )

        return available

    def select_engine(
        self,
        pdf_path: Path,
        force_engine: Optional[str] = None
    ) -> Optional[ExtractionEngine]:
        """
        Select optimal engine for given PDF.

        Args:
            pdf_path: Path to PDF file
            force_engine: If provided, force this engine (bypass logic)

        Returns:
            Selected engine instance, or None if no engine available

        Selection logic:
        1. If PDF has native text (80%+) -> Pdfplumber
        2. If Marker available AND RAM >= 8GB -> Marker
        3. If Surya/Docling available -> Use them
        4. Fallback -> Tesseract (if available)
        """
        available = self.get_available_engines()

        if not available:
            logger.error("No extraction engines available")
            return None

        # Force specific engine if requested
        if force_engine:
            for engine in available:
                if engine.name.lower() == force_engine.lower():
                    logger.info(f"Forcing engine: {engine.name}")
                    return engine
            logger.warning(f"Forced engine {force_engine} not available")
            return None

        # Analyze PDF
        analysis = self.analyze_pdf(pdf_path)
        logger.info(
            f"PDF analysis: {analysis['pages']} pages, "
            f"{analysis['native_text_ratio']:.0%} native text"
        )

        # Strategy: If mostly native text, use pdfplumber (fastest)
        if analysis["has_native_text"]:
            for engine in available:
                if engine.name == "pdfplumber":
                    logger.info("Selected pdfplumber (native text detected)")
                    return engine

        # Strategy: Prefer marker for scanned docs if RAM available
        available_ram_gb = psutil.virtual_memory().available / (1024 ** 3)
        for engine in available:
            if engine.name == "marker" and available_ram_gb >= 8.0:
                logger.info(
                    f"Selected marker (scanned PDF, {available_ram_gb:.1f}GB RAM available)"
                )
                return engine

        # Strategy: Use best available OCR engine
        for engine in available:
            if engine.name in ["surya", "docling", "tesseract"]:
                logger.info(f"Selected {engine.name} (OCR fallback)")
                return engine

        # Last resort: Use any available engine
        logger.warning(f"Using fallback engine: {available[0].name}")
        return available[0]

    def extract_with_fallback(
        self,
        pdf_path: Path,
        force_engine: Optional[str] = None,
        max_retries: int = 3
    ) -> ExtractionResult:
        """
        Extract text with automatic fallback on failure.

        Args:
            pdf_path: Path to PDF file
            force_engine: Optional engine name to force
            max_retries: Maximum number of engines to try

        Returns:
            ExtractionResult from successful engine

        Raises:
            RuntimeError: All engines failed

        Fallback chain:
        1. Selected engine (based on PDF analysis)
        2. Next available engine
        3. Next available engine
        ... (up to max_retries)
        """
        available = self.get_available_engines()

        if not available:
            raise RuntimeError("No extraction engines available on this system")

        # Get primary engine
        primary = self.select_engine(pdf_path, force_engine)
        if not primary:
            raise RuntimeError("Could not select engine")

        # Build fallback chain: primary + other available engines
        fallback_chain = [primary]
        for engine in available:
            if engine.name != primary.name and len(fallback_chain) < max_retries:
                fallback_chain.append(engine)

        # Try each engine in chain
        errors = []
        for i, engine in enumerate(fallback_chain):
            try:
                logger.info(
                    f"Attempting extraction with {engine.name} "
                    f"({i+1}/{len(fallback_chain)})"
                )
                result = engine.extract(pdf_path)
                logger.info(
                    f"Success: {engine.name} extracted {len(result.text)} chars "
                    f"from {result.pages} pages (confidence: {result.confidence:.2f})"
                )
                return result

            except Exception as e:
                error_msg = f"{engine.name} failed: {e}"
                logger.warning(error_msg)
                errors.append(error_msg)

        # All engines failed
        raise RuntimeError(
            f"All {len(fallback_chain)} engines failed:\n" + "\n".join(errors)
        )


def get_selector() -> EngineSelector:
    """Get or create singleton EngineSelector instance."""
    global _selector
    if _selector is None:
        _selector = EngineSelector()
    return _selector


# Singleton instance
_selector: Optional[EngineSelector] = None

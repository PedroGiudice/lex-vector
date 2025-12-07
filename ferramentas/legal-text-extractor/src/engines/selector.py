"""Engine selector with progressive escalation for OCR extraction."""

import difflib
import logging
import time
from pathlib import Path
from typing import Literal

from PIL import Image

from .base import (
    ConfidenceLevel,
    OCREngine,
    OCRResult,
    ResultFlag,
)
from .tesseract_engine import TesseractEngine

logger = logging.getLogger(__name__)


def get_available_ram_gb() -> float:
    """Get available RAM in GB."""
    try:
        import psutil
        return psutil.virtual_memory().available / (1024**3)
    except ImportError:
        return 8.0  # Assume 8GB if psutil not available


def get_total_ram_gb() -> float:
    """Get total RAM in GB."""
    try:
        import psutil
        return psutil.virtual_memory().total / (1024**3)
    except ImportError:
        return 16.0  # Assume 16GB if psutil not available


class EngineSelector:
    """
    Selects and escalates OCR engines based on page complexity and confidence.

    Strategy:
    1. Use recommended engine from layout analysis
    2. If confidence < threshold → escalate to more powerful engine
    3. Resolve conflicts between engine outputs

    Escalation order:
    - For Images: Tesseract only (Marker doesn't support images)
    - For PDFs: Tesseract (fast, light) → Marker (accurate, heavy)

    NOTE: Marker only works with PDFs, not individual images.
    """

    CONFIDENCE_THRESHOLD = 0.85
    SIMILARITY_HIGH = 0.90
    SIMILARITY_MEDIUM = 0.75

    def __init__(
        self,
        force_low_confidence: bool = False,
        confidence_threshold: float = 0.85,
    ):
        """
        Initialize engine selector.

        Args:
            force_low_confidence: Force low confidence for testing escalation
            confidence_threshold: Threshold below which to escalate
        """
        self.force_low_confidence = force_low_confidence
        self.CONFIDENCE_THRESHOLD = confidence_threshold

        # Initialize engines
        self._tesseract: OCREngine | None = None
        self._marker: OCREngine | None = None

        self._init_engines()

    def _init_engines(self) -> None:
        """Initialize available engines."""
        # Tesseract is always primary (fast, always available)
        try:
            self._tesseract = TesseractEngine()
            if self._tesseract.is_available():
                logger.info("✓ TesseractEngine available")
            else:
                logger.warning("TesseractEngine not available (tesseract not installed)")
                self._tesseract = None
        except Exception as e:
            logger.warning(f"Failed to initialize TesseractEngine: {e}")
            self._tesseract = None

        # Marker is secondary (high quality, resource intensive, PDF-only)
        try:
            from .marker_engine import MarkerEngine, MARKER_AVAILABLE
            if MARKER_AVAILABLE:
                self._marker = MarkerEngine()
                if self._marker.is_available():
                    logger.info("✓ MarkerEngine available (PDF only)")
                else:
                    logger.info("MarkerEngine available but insufficient resources")
                    self._marker = None
            else:
                logger.info("MarkerEngine not available (marker-pdf not installed)")
        except ImportError:
            logger.info("MarkerEngine not available (marker_engine.py not found)")
            self._marker = None
        except Exception as e:
            logger.warning(f"Failed to initialize MarkerEngine: {e}")
            self._marker = None

    @property
    def primary(self) -> OCREngine | None:
        """Get primary engine (Tesseract)."""
        return self._tesseract

    @property
    def fallback(self) -> OCREngine | None:
        """Get fallback engine (Marker - PDF only)."""
        return self._marker

    @property
    def available_engines(self) -> list[str]:
        """List available engine names."""
        engines = []
        if self._tesseract and self._tesseract.is_available():
            engines.append("tesseract")
        if self._marker and self._marker.is_available():
            engines.append("marker")
        return engines

    def select_engine(
        self,
        complexity: str,
        recommended: str | None = None,
    ) -> OCREngine | None:
        """
        Select best engine based on complexity and recommendation.

        Args:
            complexity: PageComplexity value
            recommended: Recommended engine from layout analysis

        Returns:
            Best available engine for the task
        """
        # If specific engine recommended and available, use it
        if recommended == "marker" and self._marker and self._marker.is_available():
            return self._marker

        if recommended == "tesseract" and self._tesseract and self._tesseract.is_available():
            return self._tesseract

        # Complex pages prefer Marker if available
        if complexity in ["raster_dirty", "raster_degraded", "COMPLEX", "VERY_COMPLEX"]:
            if self._marker and self._marker.is_available():
                return self._marker

        # Default to Tesseract
        if self._tesseract and self._tesseract.is_available():
            return self._tesseract

        # Last resort: any available engine
        if self._marker and self._marker.is_available():
            return self._marker

        return None

    def extract_with_escalation(
        self,
        image: Image.Image | Path,
        complexity: str = "MODERATE",
        recommended_engine: str | None = None,
        allow_escalation: bool = True,
        pdf_path: Path | None = None,
    ) -> OCRResult:
        """
        Extract text with automatic escalation if confidence is low.

        Args:
            image: PIL Image or path to image file
            complexity: Page complexity level
            recommended_engine: Engine recommended by layout analysis
            allow_escalation: Whether to allow escalation to heavier engine
            pdf_path: Path to original PDF (required for Marker escalation)

        Returns:
            OCRResult with extracted text and metadata

        Note:
            Marker escalation only works if pdf_path is provided, since
            Marker doesn't support individual images.
        """
        # Check if we can escalate to Marker
        can_escalate_to_marker = (
            allow_escalation
            and self._marker is not None
            and self._marker.is_available()
            and pdf_path is not None
            and pdf_path.suffix.lower() == '.pdf'
        )

        # Load image if path provided
        if isinstance(image, Path):
            image = Image.open(image)

        # Select primary engine
        primary = self.select_engine(complexity, recommended_engine)

        if primary is None:
            raise RuntimeError("No OCR engine available")

        logger.info(f"Extracting with {primary.name} (complexity={complexity})")

        # Extract with primary engine
        start = time.time()
        result = primary.extract_from_image(image)

        # Force low confidence for testing
        if self.force_low_confidence:
            result = OCRResult(
                text=result.text,
                confidence=0.50,
                confidence_level=ConfidenceLevel.LOW,
                engine_used=result.engine_used,
                processing_time_seconds=result.processing_time_seconds,
                flag=result.flag,
                alternatives=result.alternatives,
            )

        logger.info(
            f"  {primary.name}: confidence={result.confidence:.2f} "
            f"({result.confidence_level.value})"
        )

        # Check if escalation needed
        if result.confidence >= self.CONFIDENCE_THRESHOLD:
            return result

        # Cannot escalate if primary is already Marker (terminal)
        if primary.name == "marker":
            if result.confidence < 0.60:
                result = OCRResult(
                    text=result.text,
                    confidence=result.confidence,
                    confidence_level=result.confidence_level,
                    engine_used=result.engine_used,
                    processing_time_seconds=result.processing_time_seconds,
                    flag=ResultFlag.NEEDS_REVIEW,
                    alternatives=result.alternatives,
                )
            return result

        # Check if we can escalate
        if not can_escalate_to_marker:
            if result.confidence < 0.60:
                logger.warning(
                    f"  Low confidence ({result.confidence:.2f}) but cannot escalate "
                    f"(pdf_path required for Marker)"
                )
                result = OCRResult(
                    text=result.text,
                    confidence=result.confidence,
                    confidence_level=result.confidence_level,
                    engine_used=result.engine_used,
                    processing_time_seconds=result.processing_time_seconds,
                    flag=ResultFlag.NEEDS_REVIEW,
                    alternatives=result.alternatives,
                )
            return result

        logger.info(f"  ⚠ Low confidence ({result.confidence:.2f}), escalating to Marker (PDF)...")

        # Extract with fallback (using PDF path)
        fallback_result = self._marker.extract_from_pdf(pdf_path)
        fallback_result = OCRResult(
            text=fallback_result.text,
            confidence=fallback_result.confidence,
            confidence_level=fallback_result.confidence_level,
            engine_used=fallback_result.engine_used,
            processing_time_seconds=fallback_result.processing_time_seconds,
            flag=ResultFlag.ESCALATED,
            alternatives=fallback_result.alternatives,
        )

        logger.info(
            f"  {self._marker.name}: confidence={fallback_result.confidence:.2f} "
            f"({fallback_result.confidence_level.value})"
        )

        # Resolve best result
        return self._resolve(result, fallback_result)

    def _resolve(self, primary: OCRResult, fallback: OCRResult) -> OCRResult:
        """
        Resolve which result to use after escalation.

        Uses text similarity to determine confidence in results.
        """
        similarity = difflib.SequenceMatcher(
            None, primary.text, fallback.text
        ).ratio()

        logger.info(f"  Text similarity: {similarity:.2f}")

        total_time = primary.processing_time_seconds + fallback.processing_time_seconds

        # High similarity: trust fallback (Marker typically better)
        if similarity > self.SIMILARITY_HIGH:
            return OCRResult(
                text=fallback.text,
                confidence=max(primary.confidence, fallback.confidence),
                confidence_level=ConfidenceLevel.HIGH,
                engine_used=f"{primary.engine_used}+{fallback.engine_used}",
                processing_time_seconds=total_time,
                flag=ResultFlag.ESCALATED,
                alternatives=[primary],
            )

        # Medium similarity: use fallback but note uncertainty
        if similarity > self.SIMILARITY_MEDIUM:
            return OCRResult(
                text=fallback.text,
                confidence=(primary.confidence + fallback.confidence) / 2,
                confidence_level=ConfidenceLevel.MEDIUM,
                engine_used=f"{primary.engine_used}+{fallback.engine_used}",
                processing_time_seconds=total_time,
                flag=ResultFlag.ESCALATED,
                alternatives=[primary],
            )

        # Low similarity: needs manual review
        return OCRResult(
            text=fallback.text,  # Default to Marker output
            confidence=min(primary.confidence, fallback.confidence),
            confidence_level=ConfidenceLevel.LOW,
            engine_used=f"{primary.engine_used}+{fallback.engine_used}",
            processing_time_seconds=total_time,
            flag=ResultFlag.NEEDS_REVIEW,
            alternatives=[primary],
        )

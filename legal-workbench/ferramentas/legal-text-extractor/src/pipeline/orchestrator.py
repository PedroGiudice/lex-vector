"""
PipelineOrchestrator - Integrates all extraction components.

Workflow:
1. Analyze PDF layout (step_01)
2. For each page:
   a. Compute signature
   b. Query ContextStore for hints
   c. Select engine (considering hints)
   d. Extract text (per-page granular extraction)
   e. Learn from result (feed back to ContextStore)
3. Return final markdown

Features:
- Optional learning mode (with/without ContextStore)
- Automatic engine selection with fallback
- Pattern-based optimization hints
- Feedback loop for continuous improvement
- Per-page extraction with progress callbacks (Streamlit integration)
- Generator mode for lazy/streaming consumption
"""

import logging
from pathlib import Path
from typing import Optional, Callable, Generator, Iterator
from dataclasses import dataclass, field
from datetime import datetime

# Per-page extraction imports
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

from src.context import (
    ContextStore,
    PatternHint,
    ObservationResult,
    SignatureVector,
    EngineType,
    PatternType,
    Caso,
)
from src.context.signature import (
    compute_signature_from_layout,
    PageSignatureInput,
    infer_pattern_type,
)
from src.engines import EngineSelector, get_selector
from src.engines.base import ExtractionResult
from src.steps.step_01_layout import LayoutAnalyzer
from src.config import PageType, PageComplexity, COMPLEXITY_ENGINE_MAP

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """
    Result from complete pipeline extraction.

    Attributes:
        text: Final extracted text (markdown)
        total_pages: Number of pages processed
        success: Overall success status
        metadata: Additional metadata
        patterns_learned: Number of patterns learned (0 if no ContextStore)
        processing_time_ms: Total processing time in milliseconds
        warnings: List of warnings during processing
        layout: Layout analysis result (optional)
    """
    text: str
    total_pages: int
    success: bool
    metadata: dict = field(default_factory=dict)
    patterns_learned: int = 0
    processing_time_ms: Optional[int] = None
    warnings: list[str] = field(default_factory=list)
    layout: Optional[dict] = None


class PipelineOrchestrator:
    """
    Orchestrates the complete PDF extraction pipeline.

    Integrates:
    - LayoutAnalyzer: Analyzes PDF structure
    - ContextStore: Learns and suggests patterns (optional)
    - EngineSelector: Selects best extraction engine
    - Extraction engines: Extracts text

    Workflow:
    1. Analyze layout
    2. For each page:
       - Compute signature
       - Query ContextStore for hints
       - Select engine (considering hints)
       - Extract text
       - Learn from result
    3. Combine results
    """

    def __init__(
        self,
        context_db_path: Optional[Path] = None,
        caso_info: Optional[dict] = None,
    ):
        """
        Initialize pipeline orchestrator.

        Args:
            context_db_path: Path to ContextStore database (None = no learning)
            caso_info: Case information dict with keys:
                - numero_cnj: CNJ process number
                - sistema: System name ('pje', 'eproc', etc)
        """
        # Initialize ContextStore if db_path provided
        self.context_store: Optional[ContextStore] = None
        self.caso: Optional[Caso] = None

        if context_db_path is not None:
            self.context_store = ContextStore(db_path=context_db_path)
            logger.info(f"ContextStore enabled: {context_db_path}")

            # Create/get caso if info provided
            if caso_info:
                self.caso = self.context_store.get_or_create_caso(
                    numero_cnj=caso_info.get("numero_cnj", "UNKNOWN"),
                    sistema=caso_info.get("sistema", "UNKNOWN"),
                )
                logger.info(f"Case loaded: {self.caso.numero_cnj} (id={self.caso.id})")
        else:
            logger.info("ContextStore disabled - one-off extraction mode")

        # Initialize LayoutAnalyzer
        self.layout_analyzer = LayoutAnalyzer()

        # Initialize EngineSelector
        self.engine_selector: EngineSelector = get_selector()

        # Cache for Marker results (Marker processes entire PDF at once)
        # Key: pdf_path.resolve(), Value: dict with 'pages' list of text per page
        self._marker_cache: dict[Path, dict] = {}

    def clear_marker_cache(self, pdf_path: Optional[Path] = None) -> None:
        """
        Clear the Marker cache to free memory.

        Args:
            pdf_path: If provided, only clear cache for this specific PDF.
                     If None, clear entire cache.

        Use this method when:
        - Processing multiple PDFs sequentially to prevent memory buildup
        - After finishing processing a PDF to release resources
        """
        if pdf_path is not None:
            resolved = pdf_path.resolve()
            if resolved in self._marker_cache:
                del self._marker_cache[resolved]
                logger.debug(f"Marker cache cleared for: {pdf_path.name}")
        else:
            self._marker_cache.clear()
            logger.debug("Marker cache cleared completely")

    def process(
        self,
        pdf_path: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> PipelineResult:
        """
        Process a PDF through the complete pipeline.

        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback for UI progress updates.
                Signature: (current_page: int, total_pages: int, status_message: str) -> None
                Called before processing each page.

        Returns:
            PipelineResult with extracted text and metadata

        Raises:
            FileNotFoundError: PDF not found
            RuntimeError: No extraction engines available
        """
        start_time = datetime.now()
        warnings = []
        patterns_learned = 0

        try:
            # 1. Layout analysis
            logger.info(f"Analyzing layout: {pdf_path.name}")
            if progress_callback:
                progress_callback(0, 0, "Analyzing PDF layout...")

            layout = self.layout_analyzer.analyze(pdf_path)
            total_pages = layout["total_pages"]
            logger.info(f"Layout analyzed: {total_pages} pages")

            # 2. Process each page
            page_texts = []
            for idx, page_data in enumerate(layout["pages"]):
                page_num = page_data["page_num"]

                # Notify progress callback
                if progress_callback:
                    progress_callback(
                        page_num,
                        total_pages,
                        f"Extracting page {page_num}/{total_pages}..."
                    )

                try:
                    page_result = self._process_page(pdf_path, page_data, layout)
                    page_texts.append(page_result["text"])

                    # Learn from result if ContextStore active
                    if page_result.get("observation"):
                        patterns_learned += 1

                except Exception as e:
                    warning = f"Failed to process page {page_data['page_num']}: {e}"
                    logger.warning(warning)
                    warnings.append(warning)
                    page_texts.append("")  # Empty text for failed page

            # 3. Combine text
            final_text = self._combine_page_texts(page_texts)

            # 4. Clean text
            final_text = self._clean_text(final_text)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                text=final_text,
                total_pages=total_pages,
                success=True,
                metadata={
                    "pdf_path": str(pdf_path),
                    "doc_id": layout["doc_id"],
                    "learning_enabled": self.context_store is not None,
                    "caso_id": self.caso.id if self.caso else None,
                },
                patterns_learned=patterns_learned,
                processing_time_ms=int(processing_time),
                warnings=warnings,
                layout=layout,
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                text="",
                total_pages=0,
                success=False,
                metadata={"error": str(e)},
                processing_time_ms=int(processing_time),
                warnings=[f"Pipeline failure: {e}"],
            )

    def process_generator(
        self,
        pdf_path: Path,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Generator[dict, None, PipelineResult]:
        """
        Process a PDF yielding results page-by-page for streaming consumption.

        This is a generator variant of process() that yields intermediate results
        as each page is processed, enabling:
        - UI progress updates without callbacks
        - Memory-efficient streaming for large documents
        - Early stopping if needed

        Args:
            pdf_path: Path to PDF file
            progress_callback: Optional callback (same as process())

        Yields:
            dict with keys:
                - page_num: Current page number (1-indexed)
                - total_pages: Total pages in document
                - text: Extracted text for this page
                - engine_used: Engine that was used
                - success: Whether this page succeeded
                - error: Error message if failed (optional)

        Returns:
            PipelineResult (accessible via generator.send(None) after completion
            or by iterating to exhaustion)

        Example:
            >>> orchestrator = PipelineOrchestrator()
            >>> gen = orchestrator.process_generator(Path("document.pdf"))
            >>> for page_result in gen:
            ...     print(f"Page {page_result['page_num']}: {len(page_result['text'])} chars")
            >>> # Final result is returned when generator exhausts
        """
        start_time = datetime.now()
        warnings = []
        patterns_learned = 0
        page_texts = []

        try:
            # 1. Layout analysis
            logger.info(f"Analyzing layout: {pdf_path.name}")
            if progress_callback:
                progress_callback(0, 0, "Analyzing PDF layout...")

            layout = self.layout_analyzer.analyze(pdf_path)
            total_pages = layout["total_pages"]
            logger.info(f"Layout analyzed: {total_pages} pages")

            # 2. Process and yield each page
            for idx, page_data in enumerate(layout["pages"]):
                page_num = page_data["page_num"]

                # Notify progress callback
                if progress_callback:
                    progress_callback(
                        page_num,
                        total_pages,
                        f"Extracting page {page_num}/{total_pages}..."
                    )

                try:
                    page_result = self._process_page(pdf_path, page_data, layout)
                    page_texts.append(page_result["text"])

                    # Learn from result if ContextStore active
                    if page_result.get("observation"):
                        patterns_learned += 1

                    # Yield page result for streaming consumption
                    yield {
                        "page_num": page_num,
                        "total_pages": total_pages,
                        "text": page_result["text"],
                        "engine_used": page_data.get("recommended_engine", "pdfplumber"),
                        "success": True,
                    }

                except Exception as e:
                    warning = f"Failed to process page {page_num}: {e}"
                    logger.warning(warning)
                    warnings.append(warning)
                    page_texts.append("")  # Empty text for failed page

                    # Yield failure info for this page
                    yield {
                        "page_num": page_num,
                        "total_pages": total_pages,
                        "text": "",
                        "engine_used": None,
                        "success": False,
                        "error": str(e),
                    }

            # 3. Combine and clean text
            final_text = self._combine_page_texts(page_texts)
            final_text = self._clean_text(final_text)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                text=final_text,
                total_pages=total_pages,
                success=True,
                metadata={
                    "pdf_path": str(pdf_path),
                    "doc_id": layout["doc_id"],
                    "learning_enabled": self.context_store is not None,
                    "caso_id": self.caso.id if self.caso else None,
                },
                patterns_learned=patterns_learned,
                processing_time_ms=int(processing_time),
                warnings=warnings,
                layout=layout,
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            return PipelineResult(
                text="",
                total_pages=0,
                success=False,
                metadata={"error": str(e)},
                processing_time_ms=int(processing_time),
                warnings=[f"Pipeline failure: {e}"],
            )

    def _process_page(
        self,
        pdf_path: Path,
        page_data: dict,
        layout: dict,
    ) -> dict:
        """
        Process a single page.

        Args:
            pdf_path: Path to PDF
            page_data: Page data from layout analysis
            layout: Full layout dict (for page dimensions)

        Returns:
            Dict with:
            - text: Extracted text
            - observation: ObservationResult (if learning enabled)
        """
        page_num = page_data["page_num"]
        logger.debug(f"Processing page {page_num}")

        # Compute signature
        signature = self._compute_page_signature(page_data)

        # Query ContextStore for hints (if enabled)
        hint = None
        if self.context_store and self.caso:
            hint = self.context_store.find_similar_pattern(
                caso_id=self.caso.id,
                signature_vector=signature.features,
            )

            if hint:
                logger.debug(
                    f"Found hint for page {page_num}: "
                    f"similarity={hint.similarity:.3f}, "
                    f"engine={hint.suggested_engine.value if hint.suggested_engine else 'none'}"
                )

        # Select engine (considering hint)
        engine_name = self._select_engine_for_page(page_data, hint)

        # Extract text for this page using the selected engine
        text = self._extract_page_text(pdf_path, page_num, engine_name, page_data)

        # Create ObservationResult
        observation = self._create_observation(
            page_data, engine_name, text, signature
        )

        # Learn from result (if ContextStore enabled)
        if self.context_store and self.caso and observation:
            try:
                self.context_store.learn_from_page(
                    caso_id=self.caso.id,
                    signature=signature,
                    result=observation,
                    hint=hint,
                )
                logger.debug(f"Learned from page {page_num}")
            except Exception as e:
                logger.warning(f"Failed to learn from page {page_num}: {e}")

        return {
            "text": text,
            "observation": observation,
        }

    def _compute_page_signature(self, page_data: dict) -> SignatureVector:
        """
        Compute signature for a page.

        Args:
            page_data: Page data from layout analysis

        Returns:
            SignatureVector
        """
        # Use signature computation from context module
        return compute_signature_from_layout(page_data)

    def _select_engine_for_page(
        self,
        page_data: dict,
        hint: Optional[PatternHint] = None,
    ) -> str:
        """
        Select best engine for a page.

        Args:
            page_data: Page data from layout analysis
            hint: Pattern hint from ContextStore (optional)

        Returns:
            Engine name (e.g., 'pdfplumber', 'tesseract')
        """
        # If hint is strong and suggests an engine, use it
        if hint and hint.should_use and hint.suggested_engine:
            logger.debug(f"Using hint engine: {hint.suggested_engine.value}")
            return hint.suggested_engine.value

        # Otherwise, use recommended engine from layout analysis
        recommended = page_data.get("recommended_engine")
        if recommended:
            logger.debug(f"Using recommended engine: {recommended}")
            return recommended

        # Fallback: Use complexity mapping
        complexity = page_data.get("complexity", PageComplexity.NATIVE_CLEAN)
        engine = COMPLEXITY_ENGINE_MAP.get(complexity, "pdfplumber")
        logger.debug(f"Using fallback engine: {engine}")
        return engine

    def _extract_page_text(
        self,
        pdf_path: Path,
        page_num: int,
        engine_name: str,
        page_data: Optional[dict] = None,
    ) -> str:
        """
        Extract text from a single page using the specified engine.

        This is a REAL per-page extraction implementation that:
        1. Uses the selected engine to extract ONLY the specified page
        2. Applies safe_bbox cropping when available (pdfplumber)
        3. Uses caching for Marker (which processes entire PDFs)

        Args:
            pdf_path: Path to PDF
            page_num: Page number (1-indexed)
            engine_name: Engine to use ('pdfplumber', 'tesseract', 'marker')
            page_data: Optional page metadata from layout (contains safe_bbox)

        Returns:
            Extracted text for this page
        """
        try:
            if engine_name == "pdfplumber":
                return self._extract_page_pdfplumber(pdf_path, page_num, page_data)
            elif engine_name == "tesseract":
                return self._extract_page_tesseract(pdf_path, page_num, page_data)
            elif engine_name == "marker":
                return self._extract_page_marker(pdf_path, page_num)
            else:
                # Fallback to pdfplumber for unknown engines
                logger.warning(f"Unknown engine '{engine_name}', falling back to pdfplumber")
                return self._extract_page_pdfplumber(pdf_path, page_num, page_data)
        except Exception as e:
            logger.error(f"Extraction failed for page {page_num} with {engine_name}: {e}")
            return ""

    def _extract_page_pdfplumber(
        self,
        pdf_path: Path,
        page_num: int,
        page_data: Optional[dict] = None,
    ) -> str:
        """
        Extract text from a single page using pdfplumber.

        Uses safe_bbox from page_data to crop the extraction area,
        excluding headers, footers, and lateral bars (tarjas).

        Args:
            pdf_path: Path to PDF
            page_num: Page number (1-indexed)
            page_data: Page metadata with safe_bbox

        Returns:
            Extracted text for this page
        """
        if not PDFPLUMBER_AVAILABLE:
            raise RuntimeError("pdfplumber not available")

        with pdfplumber.open(pdf_path) as pdf:
            # pdfplumber uses 0-indexed pages
            page = pdf.pages[page_num - 1]

            # Apply safe_bbox if available
            if page_data and "safe_bbox" in page_data:
                safe_bbox = tuple(page_data["safe_bbox"])
                x0, y0, x1, y1 = safe_bbox

                # Crop and filter chars strictly by X coordinate
                # (handles rotated text in tarjas)
                cropped = page.crop(safe_bbox)
                cropped_with_filter = cropped.filter(
                    lambda obj: (
                        obj["object_type"] != "char"
                        or (obj["x0"] >= x0 and obj["x1"] <= x1)
                    )
                )
                text = cropped_with_filter.extract_text()
            else:
                # No safe_bbox, extract entire page
                text = page.extract_text()

            return text or ""

    def _extract_page_tesseract(
        self,
        pdf_path: Path,
        page_num: int,
        page_data: Optional[dict] = None,
    ) -> str:
        """
        Extract text from a single page using Tesseract OCR.

        Converts only the specified page to an image and applies OCR.

        Args:
            pdf_path: Path to PDF
            page_num: Page number (1-indexed)
            page_data: Page metadata (unused for tesseract, kept for interface consistency)

        Returns:
            Extracted text via OCR
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract dependencies not available (pytesseract, pdf2image)")

        # Convert only the specific page (first_page and last_page are 1-indexed)
        images = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=page_num,
            last_page=page_num,
        )

        if not images:
            logger.warning(f"pdf2image returned no images for page {page_num}")
            return ""

        # Extract text from the single page image
        image = images[0]
        text = pytesseract.image_to_string(image, lang="por", config="--psm 3")
        return text or ""

    def _extract_page_marker(
        self,
        pdf_path: Path,
        page_num: int,
    ) -> str:
        """
        Extract text from a single page using Marker.

        LIMITATION: Marker processes entire PDFs, not individual pages.
        This method caches the full extraction and returns the requested page.

        The cache is stored in self._marker_cache keyed by pdf_path.resolve().

        Args:
            pdf_path: Path to PDF
            page_num: Page number (1-indexed)

        Returns:
            Extracted text for the specified page (from cache)
        """
        resolved_path = pdf_path.resolve()

        # Check cache first
        if resolved_path not in self._marker_cache:
            logger.info(f"Marker: Processing entire PDF for caching... ({pdf_path.name})")

            try:
                from marker.converters.pdf import PdfConverter
                from marker.models import create_model_dict

                models = create_model_dict()
                converter = PdfConverter(artifact_dict=models)
                rendered = converter(str(pdf_path))

                # Split markdown by pages if possible
                # Marker output format varies; this is a best-effort split
                full_text = rendered.markdown

                # Try to extract per-page text if Marker provides page info
                if hasattr(rendered, 'pages') and rendered.pages:
                    # rendered.pages is a list of page objects
                    page_texts = []
                    for page_obj in rendered.pages:
                        if hasattr(page_obj, 'text'):
                            page_texts.append(page_obj.text)
                        elif hasattr(page_obj, 'markdown'):
                            page_texts.append(page_obj.markdown)
                        else:
                            # Fallback: empty string for this page
                            page_texts.append("")

                    self._marker_cache[resolved_path] = {
                        "pages": page_texts,
                        "full_text": full_text,
                    }
                else:
                    # Fallback: store full text as single page
                    # This means all pages will return the same text
                    logger.warning(
                        "Marker: No per-page info available, "
                        "storing full text (limitation for multi-page PDFs)"
                    )
                    self._marker_cache[resolved_path] = {
                        "pages": [full_text],
                        "full_text": full_text,
                    }

            except ImportError:
                raise RuntimeError("Marker not available (marker-pdf not installed)")
            except Exception as e:
                logger.error(f"Marker extraction failed: {e}")
                raise

        # Return cached page text
        cached = self._marker_cache[resolved_path]
        pages = cached["pages"]

        # page_num is 1-indexed, list is 0-indexed
        idx = page_num - 1
        if idx < len(pages):
            return pages[idx]
        else:
            # If page index out of range, return full text or empty
            logger.warning(
                f"Marker cache: page {page_num} not found (only {len(pages)} pages cached), "
                "returning full text"
            )
            return cached.get("full_text", "")

    def _create_observation(
        self,
        page_data: dict,
        engine_name: str,
        text: str,
        signature: SignatureVector,
    ) -> Optional[ObservationResult]:
        """
        Create ObservationResult from extraction.

        Args:
            page_data: Page data from layout
            engine_name: Engine used
            text: Extracted text
            signature: Page signature

        Returns:
            ObservationResult or None if creation fails
        """
        try:
            # Map engine name to EngineType
            engine_type = self._engine_name_to_type(engine_name)

            # Infer pattern type
            page_input = PageSignatureInput.from_layout_page(page_data)
            pattern_type, _ = infer_pattern_type(page_input)

            # Estimate confidence based on text quality
            confidence = self._estimate_confidence(text, page_data)

            return ObservationResult(
                page_num=page_data["page_num"],
                engine_used=engine_type,
                confidence=confidence,
                text_length=len(text),
                bbox=page_data.get("safe_bbox"),
                pattern_type=pattern_type,
                success=len(text) > 0,
            )
        except Exception as e:
            logger.warning(f"Failed to create observation: {e}")
            return None

    def _engine_name_to_type(self, engine_name: str) -> EngineType:
        """Map engine name string to EngineType enum."""
        mapping = {
            "pdfplumber": EngineType.PDFPLUMBER,
            "tesseract": EngineType.TESSERACT,
            "marker": EngineType.MARKER,
        }
        return mapping.get(engine_name.lower(), EngineType.PDFPLUMBER)

    def _estimate_confidence(self, text: str, page_data: dict) -> float:
        """
        Estimate extraction confidence based on text quality.

        Args:
            text: Extracted text
            page_data: Page data from layout

        Returns:
            Confidence score (0.0-1.0)
        """
        if not text:
            return 0.0

        # Base confidence on text length vs expected
        char_count = page_data.get("char_count", 0)
        if char_count == 0:
            # Raster page - OCR confidence
            # Heuristic: assume good OCR if got reasonable text
            return 0.7 if len(text) > 100 else 0.5
        else:
            # Native page - compare extraction vs expected
            ratio = len(text) / max(char_count, 1)
            # Expect extracted text to be similar to char count
            # (some variation due to whitespace/formatting)
            if 0.8 <= ratio <= 1.5:
                return 0.95
            elif 0.5 <= ratio <= 2.0:
                return 0.8
            else:
                return 0.6

    def _combine_page_texts(self, page_texts: list[str]) -> str:
        """
        Combine page texts into single document.

        Args:
            page_texts: List of text strings (one per page)

        Returns:
            Combined text
        """
        # Simple newline-based combination
        # Real implementation might add page breaks, headers, etc.
        return "\n\n".join(filter(None, page_texts))

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Simple cleanup
        # Real implementation would:
        # - Remove duplicate spaces
        # - Fix encoding issues
        # - Remove artifacts
        # - Normalize line breaks

        lines = text.split("\n")
        # Remove empty lines at start/end
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        return "\n".join(lines)

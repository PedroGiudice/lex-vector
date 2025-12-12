"""Worker for legal text extraction operations.

This worker integrates the legal-text-extractor agent to process PDF files
asynchronously, providing progress updates and handling errors gracefully.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

from legal_extractor_tui.messages.extractor_messages import (
    ExtractionCancelled,
    ExtractionCompleted,
    ExtractionError,
    ExtractionProgress,
    ExtractionStarted,
)
from legal_extractor_tui.workers.base_worker import BaseWorker

# Add legal-text-extractor to path
LEGAL_EXTRACTOR_PATH = Path(__file__).parent.parent.parent.parent.parent / "agentes" / "legal-text-extractor"
if LEGAL_EXTRACTOR_PATH not in [Path(p) for p in sys.path]:
    sys.path.insert(0, str(LEGAL_EXTRACTOR_PATH))

# Import legal-text-extractor components
from main import ExtractionResult, LegalTextExtractor  # noqa: E402

logger = logging.getLogger(__name__)


class ExtractionWorker(BaseWorker):
    """Worker that processes PDFs using legal-text-extractor.

    This worker handles the complete extraction pipeline:
    1. Text extraction from PDF (with OCR fallback if needed)
    2. System detection and text cleaning
    3. Section analysis (optional, requires API key)

    The worker runs in the background and emits progress messages
    that can be handled by the TUI to update the UI.

    Attributes:
        extractor: LegalTextExtractor instance
        current_stage: Current processing stage (for cancellation tracking)

    Example:
        ```python
        worker = ExtractionWorker(app)
        result = await worker.run(
            pdf_path=Path("document.pdf"),
            system="auto",
            separate_sections=True
        )
        ```
    """

    def __init__(self, app) -> None:
        """Initialize the extraction worker.

        Args:
            app: The Textual application instance
        """
        super().__init__(app)
        self.extractor = LegalTextExtractor()
        self.current_stage = "idle"

    async def run(
        self,
        pdf_path: Path | str,
        system: str = "auto",
        separate_sections: bool = False,
        custom_blacklist: list[str] | None = None,
        output_format: str = "text",
    ) -> dict | None:
        """Execute the extraction pipeline.

        Processes a PDF file through extraction, cleaning, and optional
        section analysis. Emits progress messages at each stage.

        Args:
            pdf_path: Path to the PDF file to process
            system: Judicial system code or "auto" for auto-detection
            separate_sections: Whether to perform section analysis via API
            custom_blacklist: Additional terms to remove during cleaning
            output_format: Output format ("text", "markdown", "json")

        Returns:
            Dictionary with extraction results, or None if cancelled

        Raises:
            ExtractionError: Emitted as message if processing fails
        """
        pdf_path = Path(pdf_path)
        start_time = time.time()

        # Validate file exists
        if not pdf_path.exists():
            error_msg = f"File not found: {pdf_path}"
            logger.error(error_msg)
            self.post_message(
                ExtractionError(
                    error=FileNotFoundError(error_msg),
                    stage="validation",
                    message=error_msg,
                )
            )
            return None

        # Validate file is PDF
        if pdf_path.suffix.lower() != ".pdf":
            error_msg = f"Not a PDF file: {pdf_path}"
            logger.error(error_msg)
            self.post_message(
                ExtractionError(
                    error=ValueError(error_msg),
                    stage="validation",
                    message=error_msg,
                )
            )
            return None

        # Start extraction
        self.post_message(
            ExtractionStarted(
                file_path=pdf_path,
                system=system,
                separate_sections=separate_sections,
            )
        )
        logger.info(f"Starting extraction: {pdf_path.name}")

        try:
            # Stage 1: Extract text from PDF
            self.current_stage = "extracting"
            if self.is_cancelled:
                self.post_message(ExtractionCancelled(stage=self.current_stage))
                return None

            self.post_message(
                ExtractionProgress(
                    stage="extracting",
                    progress=0.1,
                    message="Extracting text from PDF...",
                    details={"file": pdf_path.name},
                )
            )

            # Run extraction in thread pool to avoid blocking
            result = await self._run_extraction(
                pdf_path=pdf_path,
                system=system,
                separate_sections=separate_sections,
                custom_blacklist=custom_blacklist,
            )

            if result is None:  # Cancelled during extraction
                return None

            # Stage 2: Extraction complete
            self.current_stage = "completed"
            elapsed = time.time() - start_time

            self.post_message(
                ExtractionCompleted(
                    result=self._result_to_dict(result),
                    elapsed_time=elapsed,
                )
            )

            logger.info(
                f"Extraction completed: {pdf_path.name} "
                f"({elapsed:.2f}s, {result.final_length:,} chars)"
            )

            return self._result_to_dict(result)

        except NotImplementedError as e:
            # OCR not yet implemented
            error_msg = "OCR extraction not yet implemented (scanned PDF detected)"
            logger.warning(error_msg)
            self.post_message(
                ExtractionError(
                    error=e,
                    stage=self.current_stage,
                    message=error_msg,
                )
            )
            return None

        except Exception as e:
            # Unexpected error
            error_msg = f"Extraction failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.post_message(
                ExtractionError(
                    error=e,
                    stage=self.current_stage,
                    message=error_msg,
                )
            )
            return None

    async def _run_extraction(
        self,
        pdf_path: Path,
        system: str,
        separate_sections: bool,
        custom_blacklist: list[str] | None,
    ) -> ExtractionResult | None:
        """Run the extraction pipeline with progress tracking.

        This method wraps the synchronous LegalTextExtractor.process_pdf()
        and provides progress updates at each stage.

        Args:
            pdf_path: Path to PDF file
            system: Judicial system code
            separate_sections: Whether to analyze sections
            custom_blacklist: Custom terms to remove

        Returns:
            ExtractionResult or None if cancelled
        """
        # Check for scanned PDF (before expensive extraction)
        if self.is_cancelled:
            self.post_message(ExtractionCancelled(stage="extracting"))
            return None

        is_scanned = await asyncio.to_thread(
            self.extractor.text_extractor.is_scanned,
            pdf_path,
        )

        if is_scanned:
            raise NotImplementedError("OCR extraction not implemented")

        # Stage 1: Text extraction
        self.post_message(
            ExtractionProgress(
                stage="extracting",
                progress=0.2,
                message="Reading PDF pages...",
            )
        )

        if self.is_cancelled:
            self.post_message(ExtractionCancelled(stage="extracting"))
            return None

        raw_text = await asyncio.to_thread(
            self.extractor.text_extractor.extract,
            pdf_path,
        )

        logger.info(f"Extracted {len(raw_text):,} characters")

        # Stage 2: Cleaning
        self.current_stage = "cleaning"
        self.post_message(
            ExtractionProgress(
                stage="cleaning",
                progress=0.5,
                message="Detecting judicial system...",
            )
        )

        if self.is_cancelled:
            self.post_message(ExtractionCancelled(stage="cleaning"))
            return None

        cleaning_result = await asyncio.to_thread(
            self.extractor.cleaner.clean,
            raw_text,
            system,
            custom_blacklist,
        )

        logger.info(
            f"System detected: {cleaning_result.stats.system_name} "
            f"({cleaning_result.stats.confidence}% confidence)"
        )

        self.post_message(
            ExtractionProgress(
                stage="cleaning",
                progress=0.7,
                message=f"Cleaning text ({cleaning_result.stats.system_name})...",
                details={
                    "system": cleaning_result.stats.system_name,
                    "confidence": cleaning_result.stats.confidence,
                    "reduction_pct": cleaning_result.stats.reduction_pct,
                },
            )
        )

        # Stage 3: Section analysis (optional)
        sections = []
        self.current_stage = "analyzing"

        if separate_sections:
            self.post_message(
                ExtractionProgress(
                    stage="analyzing",
                    progress=0.8,
                    message="Analyzing document sections...",
                )
            )

            if self.is_cancelled:
                self.post_message(ExtractionCancelled(stage="analyzing"))
                return None

            try:
                sections = await asyncio.to_thread(
                    self.extractor.section_analyzer.analyze,
                    cleaning_result.text,
                )
                logger.info(f"Identified {len(sections)} sections")
            except Exception as e:
                # Section analysis failed - use single section fallback
                logger.warning(f"Section analysis failed: {e}")
                sections = self._create_single_section(cleaning_result.text)
        else:
            # No section analysis requested
            sections = self._create_single_section(cleaning_result.text)

        self.post_message(
            ExtractionProgress(
                stage="analyzing",
                progress=0.95,
                message="Finalizing results...",
            )
        )

        # Build result
        result = ExtractionResult(
            text=cleaning_result.text,
            sections=sections,
            system=cleaning_result.stats.system,
            system_name=cleaning_result.stats.system_name,
            confidence=cleaning_result.stats.confidence,
            original_length=cleaning_result.stats.original_length,
            final_length=cleaning_result.stats.final_length,
            reduction_pct=cleaning_result.stats.reduction_pct,
            patterns_removed=cleaning_result.stats.patterns_removed,
        )

        return result

    def _create_single_section(self, text: str) -> list[Any]:
        """Create a single section containing the entire document.

        Args:
            text: Document text

        Returns:
            List with single Section object
        """
        from analyzers.section_analyzer import Section

        return [
            Section(
                type="documento_completo",
                content=text,
                start_pos=0,
                end_pos=len(text),
                confidence=1.0,
            )
        ]

    def _result_to_dict(self, result: ExtractionResult) -> dict:
        """Convert ExtractionResult to dictionary for message passing.

        Args:
            result: ExtractionResult instance

        Returns:
            Dictionary representation of the result
        """
        return {
            "text": result.text,
            "system": result.system,
            "system_name": result.system_name,
            "confidence": result.confidence,
            "original_length": result.original_length,
            "final_length": result.final_length,
            "reduction_pct": result.reduction_pct,
            "patterns_removed": result.patterns_removed,
            "sections": [
                {
                    "type": s.type,
                    "content": s.content,
                    "start_pos": getattr(s, "start_pos", 0),
                    "end_pos": getattr(s, "end_pos", len(s.content)),
                    "confidence": s.confidence,
                }
                for s in result.sections
            ],
        }

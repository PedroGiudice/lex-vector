"""Workers for background task execution.

This package provides worker classes for handling long-running operations
in the background without blocking the Textual UI.

Available Workers:
    - BaseWorker: Abstract base class for all workers
    - PipelineWorker: Multi-step pipeline executor with progress tracking
    - ExtractionWorker: Legal text extraction from PDF files
    - PipelineStep: Configuration for individual pipeline steps

Example:
    ```python
    from legal_extractor_tui.workers import ExtractionWorker

    # Create and run extraction worker
    worker = ExtractionWorker(app)
    result = await worker.run(
        pdf_path=Path("document.pdf"),
        system="auto",
        separate_sections=True
    )
    ```
"""

from legal_extractor_tui.workers.base_worker import BaseWorker
from legal_extractor_tui.workers.extraction_worker import ExtractionWorker
from legal_extractor_tui.workers.pipeline_worker import PipelineStep, PipelineWorker

__all__ = [
    "BaseWorker",
    "PipelineWorker",
    "PipelineStep",
    "ExtractionWorker",
]

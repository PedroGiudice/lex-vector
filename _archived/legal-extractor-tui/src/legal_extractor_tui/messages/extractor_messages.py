"""Messages for legal text extraction operations.

These messages track the lifecycle of PDF extraction, from initiation
through text extraction, cleaning, section analysis, and completion.
"""

from pathlib import Path
from textual.message import Message


class FileSelected(Message):
    """Emitted when a PDF file is selected for processing.

    Attributes:
        path: Path to the selected PDF file
    """

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path


class SystemChanged(Message):
    """Emitted when judicial system selection changes.

    Attributes:
        system: Selected system code (auto, pje, esaj, eproc, projudi, stf, stj)
    """

    def __init__(self, system: str) -> None:
        super().__init__()
        self.system = system


class ConfigChanged(Message):
    """Emitted when extraction configuration changes.

    Attributes:
        config: Configuration dictionary with updated settings
    """

    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = config


class ExportRequested(Message):
    """Emitted when user requests to export results.

    Attributes:
        format: Export format (txt, md, json)
        destination: Optional destination path
    """

    def __init__(self, format: str, destination: Path | None = None) -> None:
        super().__init__()
        self.format = format
        self.destination = destination


class ExtractionStarted(Message):
    """Emitted when PDF extraction begins.

    Attributes:
        file_path: Path to the PDF being processed
        system: Judicial system ("auto" or specific system code)
        separate_sections: Whether section analysis is enabled
    """

    def __init__(
        self,
        file_path: Path,
        system: str = "auto",
        separate_sections: bool = False,
    ) -> None:
        super().__init__()
        self.file_path = file_path
        self.system = system
        self.separate_sections = separate_sections


class ExtractionProgress(Message):
    """Emitted during extraction to indicate progress.

    Attributes:
        stage: Current stage ("extracting", "cleaning", "analyzing")
        progress: Progress as float 0.0-1.0
        message: Human-readable status message
        details: Optional additional details (e.g., system detected)
    """

    def __init__(
        self,
        stage: str,
        progress: float,
        message: str,
        details: dict | None = None,
    ) -> None:
        super().__init__()
        self.stage = stage
        self.progress = progress
        self.message = message
        self.details = details or {}


class ExtractionCompleted(Message):
    """Emitted when extraction completes successfully.

    Attributes:
        result: Dictionary with extraction result data
        elapsed_time: Total processing time in seconds
    """

    def __init__(self, result: dict, elapsed_time: float) -> None:
        super().__init__()
        self.result = result
        self.elapsed_time = elapsed_time


class ExtractionError(Message):
    """Emitted when extraction fails.

    Attributes:
        error: Exception that caused the failure
        stage: Stage where error occurred
        message: Human-readable error message
    """

    def __init__(
        self,
        error: Exception,
        stage: str,
        message: str,
    ) -> None:
        super().__init__()
        self.error = error
        self.stage = stage
        self.message = message


class ExtractionCancelled(Message):
    """Emitted when extraction is cancelled by user.

    Attributes:
        stage: Stage where cancellation occurred
    """

    def __init__(self, stage: str) -> None:
        super().__init__()
        self.stage = stage

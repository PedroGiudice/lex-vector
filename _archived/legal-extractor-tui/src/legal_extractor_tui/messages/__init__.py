"""Message definitions for Legal Extractor TUI.

This package contains all custom Textual messages used for
inter-component communication.
"""

from .extractor_messages import (
    ConfigChanged,
    ExportRequested,
    ExtractionCancelled,
    ExtractionCompleted,
    ExtractionError,
    ExtractionProgress,
    ExtractionStarted,
    FileSelected,
    SystemChanged,
)
from .pipeline_messages import (
    PipelineAborted,
    PipelineCompleted,
    PipelineStarted,
    StepCompleted,
    StepError,
    StepProgress,
    StepStarted,
)
from .system_messages import (
    FileLoaded,
    LogLevel,
    LogMessage,
    StatusUpdate,
)

__all__ = [
    # Extractor messages
    "FileSelected",
    "SystemChanged",
    "ConfigChanged",
    "ExportRequested",
    "ExtractionStarted",
    "ExtractionProgress",
    "ExtractionCompleted",
    "ExtractionError",
    "ExtractionCancelled",
    # Pipeline messages
    "PipelineStarted",
    "StepStarted",
    "StepProgress",
    "StepCompleted",
    "StepError",
    "PipelineCompleted",
    "PipelineAborted",
    # System messages
    "LogLevel",
    "LogMessage",
    "StatusUpdate",
    "FileLoaded",
]

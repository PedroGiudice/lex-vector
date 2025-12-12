"""System-level messages for TUI Template.

Messages for logging, status updates, and file operations.
"""

from dataclasses import dataclass
from enum import Enum
from textual.message import Message


class LogLevel(str, Enum):
    """Log message severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class LogMessage(Message):
    """Emitted when a log message should be displayed.

    Attributes:
        message: Log message text
        level: Severity level
        source: Component or module that generated the message
    """
    message: str
    level: LogLevel = LogLevel.INFO
    source: str | None = None


@dataclass
class StatusUpdate(Message):
    """Emitted when application status changes.

    Attributes:
        status: Status text to display
        style: Rich style string for status formatting
    """
    status: str
    style: str = "dim"


@dataclass
class FileLoaded(Message):
    """Emitted when a file is successfully loaded.

    Attributes:
        path: File path that was loaded
        size_bytes: File size in bytes
    """
    path: str
    size_bytes: int

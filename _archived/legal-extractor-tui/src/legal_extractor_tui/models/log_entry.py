"""Log entry models for TUI Template.

Pydantic models for structured logging with Rich formatting support.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from rich.text import Text


class LogLevel(str, Enum):
    """Log severity levels with display properties."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

    @property
    def color(self) -> str:
        """Get Rich color for this log level."""
        return {
            self.DEBUG: "dim cyan",
            self.INFO: "cyan",
            self.WARNING: "yellow",
            self.ERROR: "red",
            self.SUCCESS: "green",
        }[self]

    @property
    def icon(self) -> str:
        """Get icon/emoji for this log level."""
        return {
            self.DEBUG: "🔍",
            self.INFO: "ℹ️",
            self.WARNING: "⚠️",
            self.ERROR: "❌",
            self.SUCCESS: "✅",
        }[self]


class LogEntry(BaseModel):
    """Structured log entry with formatting capabilities.

    Attributes:
        message: Log message text
        level: Severity level
        source: Component/module that generated the log
        timestamp: When the log was created
        metadata: Additional structured data
    """
    message: str
    level: LogLevel = Field(default=LogLevel.INFO)
    source: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict | None = Field(default=None)

    def format_rich(self, include_timestamp: bool = True, include_icon: bool = True) -> Text:
        """Format log entry as Rich Text object.

        Args:
            include_timestamp: Whether to include timestamp
            include_icon: Whether to include level icon

        Returns:
            Formatted Rich Text object
        """
        text = Text()

        # Timestamp
        if include_timestamp:
            text.append(self.timestamp.strftime("%H:%M:%S"), style="dim")
            text.append(" ")

        # Icon
        if include_icon:
            text.append(self.level.icon + " ")

        # Level badge
        text.append(f"[{self.level.value.upper()}]", style=f"bold {self.level.color}")
        text.append(" ")

        # Source
        if self.source:
            text.append(f"({self.source}) ", style="dim italic")

        # Message
        text.append(self.message, style=self.level.color)

        return text

    def __str__(self) -> str:
        """Plain text representation."""
        parts = [self.timestamp.strftime("%Y-%m-%d %H:%M:%S")]
        parts.append(f"[{self.level.value.upper()}]")
        if self.source:
            parts.append(f"({self.source})")
        parts.append(self.message)
        return " ".join(parts)

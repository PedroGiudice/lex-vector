"""Log panel widget with colored log levels and timestamps.

Example:
    ```python
    from legal_extractor_tui.widgets.log_panel import LogPanel

    log_panel = LogPanel(show_timestamps=True)
    log_panel.info("Application started")
    log_panel.warning("Low memory")
    log_panel.error("Connection failed")
    log_panel.success("Task completed")
    ```
"""

from datetime import datetime

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import RichLog


class LogPanel(RichLog):
    """Log panel with colored levels and optional timestamps.

    Attributes:
        show_timestamps: Whether to display timestamps with log messages
        MAX_LINES: Maximum number of log lines to retain
    """

    MAX_LINES = 10000

    show_timestamps: reactive[bool] = reactive(True)

    def __init__(
        self,
        show_timestamps: bool = True,
        *,
        max_lines: int | None = None,
        min_width: int = 78,
        wrap: bool = True,
        highlight: bool = True,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the log panel.

        Args:
            show_timestamps: Whether to show timestamps
            max_lines: Maximum lines to retain (defaults to MAX_LINES)
            min_width: Minimum width of the log panel
            wrap: Whether to wrap long lines
            highlight: Whether to apply syntax highlighting
            markup: Whether to interpret Rich markup
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(
            max_lines=max_lines or self.MAX_LINES,
            min_width=min_width,
            wrap=wrap,
            highlight=highlight,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
        )
        self.show_timestamps = show_timestamps

    def _format_timestamp(self) -> str:
        """Generate formatted timestamp.

        Returns:
            Formatted timestamp string
        """
        return datetime.now().strftime("%H:%M:%S")

    def _format_message(self, level: str, message: str, style: str) -> Text:
        """Format a log message with level and optional timestamp.

        Args:
            level: Log level (DEBUG, INFO, etc.)
            message: Log message text
            style: Rich style for the level indicator

        Returns:
            Formatted Text object
        """
        text = Text()

        if self.show_timestamps:
            text.append(f"[{self._format_timestamp()}] ", style="dim")

        text.append(f"[{level:8}] ", style=style)
        text.append(message)

        return text

    def add_log(self, message: str, level: str = "INFO", style: str = "cyan") -> None:
        """Log a message with custom level and style.

        Args:
            message: Message to log
            level: Log level label
            style: Rich style for the level

        Example:
            ```python
            log_panel.add_log("Custom message", level="CUSTOM", style="magenta")
            ```
        """
        formatted = self._format_message(level, message, style)
        self.write(formatted)

    def debug(self, message: str) -> None:
        """Log a debug message.

        Args:
            message: Debug message to log
        """
        self.add_log(message, level="DEBUG", style="dim")

    def info(self, message: str) -> None:
        """Log an info message.

        Args:
            message: Info message to log
        """
        self.add_log(message, level="INFO", style="cyan")

    def warning(self, message: str) -> None:
        """Log a warning message.

        Args:
            message: Warning message to log
        """
        self.add_log(message, level="WARNING", style="yellow")

    def error(self, message: str) -> None:
        """Log an error message.

        Args:
            message: Error message to log
        """
        self.add_log(message, level="ERROR", style="red bold")

    def success(self, message: str) -> None:
        """Log a success message.

        Args:
            message: Success message to log
        """
        self.add_log(message, level="SUCCESS", style="green bold")

    def separator(self, char: str = "─", style: str = "dim") -> None:
        """Write a separator line.

        Args:
            char: Character to use for the separator
            style: Rich style for the separator

        Example:
            ```python
            log_panel.separator("=", "blue")
            ```
        """
        text = Text(char * 80, style=style)
        self.write(text)

    def header(self, title: str, style: str = "bold cyan") -> None:
        """Write a formatted header.

        Args:
            title: Header text
            style: Rich style for the header

        Example:
            ```python
            log_panel.header("Pipeline Execution Started")
            log_panel.separator()
            ```
        """
        self.separator()
        text = Text(f" {title} ", style=style)
        self.write(text)
        self.separator()

    def watch_show_timestamps(self, show_timestamps: bool) -> None:
        """React to show_timestamps changes.

        Args:
            show_timestamps: New timestamp visibility state
        """
        # This is a reactive property - changing it will affect future logs
        # We don't need to redraw existing logs
        pass

"""Status bar widget with system metrics and runtime information.

Example:
    ```python
    from legal_extractor_tui.widgets.status_bar import StatusBar

    status_bar = StatusBar()
    status_bar.set_status("Processing files...")

    # Metrics update automatically via timer
    # CPU and RAM shown in real-time
    ```
"""

import time
from datetime import timedelta

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Label

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class StatusBar(Horizontal):
    """Status bar displaying system metrics and application status.

    Attributes:
        cpu_percent: Current CPU usage percentage
        ram_percent: Current RAM usage percentage
    """

    # CSS moved to widgets.tcss for centralized theme management

    cpu_percent: reactive[float] = reactive(0.0, init=False)
    ram_percent: reactive[float] = reactive(0.0, init=False)

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the status bar.

        Args:
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self._start_time = time.time()
        self._status_message = "Ready"

    def compose(self) -> ComposeResult:
        """Compose the status bar layout.

        Yields:
            Labels for status message and metrics with separators
        """
        yield Label(self._status_message, classes="status-message", id="status-message")
        yield Label("│", classes="separator")
        yield Label(self._format_runtime(), classes="runtime-metric", id="runtime")
        yield Label("│", classes="separator")
        yield Label(self._format_cpu(), classes="cpu-metric", id="cpu")
        yield Label("│", classes="separator")
        yield Label(self._format_ram(), classes="ram-metric", id="ram")

    def on_mount(self) -> None:
        """Set up periodic metric updates when widget is mounted."""
        # Update metrics every 2 seconds
        self._metrics_timer = self.set_interval(2.0, self._update_metrics)
        # Update runtime every second
        self._runtime_timer = self.set_interval(1.0, self._update_runtime)

    def on_unmount(self) -> None:
        """Clean up timers when widget is unmounted."""
        if hasattr(self, '_metrics_timer') and self._metrics_timer:
            self._metrics_timer.stop()
        if hasattr(self, '_runtime_timer') and self._runtime_timer:
            self._runtime_timer.stop()

    def _get_cpu_percent(self) -> float:
        """Get current CPU usage percentage.

        Returns:
            CPU usage percentage (0-100)
        """
        if PSUTIL_AVAILABLE:
            return psutil.cpu_percent(interval=0.1)
        else:
            # Mock data when psutil not available
            return 0.0

    def _get_ram_percent(self) -> float:
        """Get current RAM usage percentage.

        Returns:
            RAM usage percentage (0-100)
        """
        if PSUTIL_AVAILABLE:
            return psutil.virtual_memory().percent
        else:
            # Mock data when psutil not available
            return 0.0

    def _update_metrics(self) -> None:
        """Update CPU and RAM metrics."""
        self.cpu_percent = self._get_cpu_percent()
        self.ram_percent = self._get_ram_percent()

    def _update_runtime(self) -> None:
        """Update runtime display."""
        runtime_label = self.query_one("#runtime", Label)
        runtime_label.update(self._format_runtime())

    def _format_cpu(self) -> str:
        """Format CPU metric for display.

        Returns:
            Formatted CPU string with icon
        """
        return f"CPU: {self.cpu_percent:4.1f}%"

    def _format_ram(self) -> str:
        """Format RAM metric for display.

        Returns:
            Formatted RAM string with icon
        """
        return f"RAM: {self.ram_percent:4.1f}%"

    def _format_runtime(self) -> str:
        """Format runtime for display.

        Returns:
            Formatted runtime string with icon
        """
        elapsed = time.time() - self._start_time
        delta = timedelta(seconds=int(elapsed))

        # Format as HH:MM:SS
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if delta.days > 0:
            return f"Runtime: {delta.days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"Runtime: {hours:02d}:{minutes:02d}:{seconds:02d}"

    def watch_cpu_percent(self, cpu_percent: float) -> None:
        """React to CPU percentage changes.

        Args:
            cpu_percent: New CPU percentage
        """
        cpu_label = self.query_one("#cpu", Label)
        cpu_label.update(self._format_cpu())

    def watch_ram_percent(self, ram_percent: float) -> None:
        """React to RAM percentage changes.

        Args:
            ram_percent: New RAM percentage
        """
        ram_label = self.query_one("#ram", Label)
        ram_label.update(self._format_ram())

    def set_status(self, message: str) -> None:
        """Update the status message.

        Args:
            message: Status message to display

        Example:
            ```python
            status_bar.set_status("Processing file 5 of 100...")
            status_bar.set_status("Idle")
            status_bar.set_status("[red]Error:[/] Failed to connect")
            ```
        """
        self._status_message = message
        status_label = self.query_one("#status-message", Label)
        status_label.update(message)

    def reset_runtime(self) -> None:
        """Reset the runtime counter to zero."""
        self._start_time = time.time()
        self._update_runtime()

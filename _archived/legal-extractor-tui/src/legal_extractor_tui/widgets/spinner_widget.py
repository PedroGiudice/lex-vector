"""Universal spinner widget supporting Rich and custom spinners.

This module provides a SpinnerWidget that can display animations from:
- Rich library's built-in spinner collection
- Custom spinners defined in spinners.py
"""

from typing import Literal

from rich.spinner import Spinner as RichSpinner
from textual.reactive import reactive
from textual.widgets import Static
from textual.timer import Timer

from .spinners import CUSTOM_SPINNERS, SpinnerDefinition


class SpinnerWidget(Static):
    """Universal spinner widget with pause/resume control.

    Supports two sources of spinners:
    - "rich": Built-in Rich library spinners (dots, line, etc)
    - "custom": Custom spinners from spinners.py (claude, matrix, etc)

    Example:
        ```python
        # Rich spinner
        spinner1 = SpinnerWidget("dots", source="rich", text="Loading...")

        # Custom spinner
        spinner2 = SpinnerWidget("claude", source="custom", text="Processing...")

        # Control
        spinner1.pause()
        spinner1.set_text("Almost done...")
        spinner1.resume()
        ```
    """

    is_spinning: reactive[bool] = reactive(True)
    """Whether the spinner is currently animating."""

    def __init__(
        self,
        spinner_name: str = "dots",
        source: Literal["rich", "custom"] = "rich",
        text: str = "",
        style: str = "cyan",
        speed: float = 1.0,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        """Initialize spinner widget.

        Args:
            spinner_name: Name of spinner to use
            source: Source of spinner ("rich" or "custom")
            text: Optional text to display next to spinner
            style: Text style (color)
            speed: Animation speed multiplier (1.0 = normal)
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)

        self.spinner_name = spinner_name
        self.source = source
        self.text = text
        self.style = style
        self.speed = speed
        self._frame_index = 0
        self._timer: Timer | None = None

        # Load spinner definition
        if source == "rich":
            try:
                self._rich_spinner = RichSpinner(spinner_name)
                self._frames = list(self._rich_spinner.frames)
                self._interval_ms = int(self._rich_spinner.interval * 1000 / speed)
            except Exception:
                # Fallback to dots if spinner not found
                self._rich_spinner = RichSpinner("dots")
                self._frames = list(self._rich_spinner.frames)
                self._interval_ms = int(self._rich_spinner.interval * 1000 / speed)
        else:  # custom
            spinner_def = CUSTOM_SPINNERS.get(spinner_name)
            if not spinner_def:
                # Fallback to claude spinner
                spinner_def = CUSTOM_SPINNERS["claude"]

            self._rich_spinner = None
            self._frames = list(spinner_def.frames)
            self._interval_ms = int(spinner_def.interval_ms / speed)

    def on_mount(self) -> None:
        """Start animation when widget is mounted."""
        self._start_animation()
        self._update_display()

    def _start_animation(self) -> None:
        """Start or restart the animation timer."""
        if self._timer:
            self._timer.stop()

        if self.is_spinning:
            self._timer = self.set_interval(
                self._interval_ms / 1000,
                self._advance_frame,
                pause=False
            )

    def _advance_frame(self) -> None:
        """Advance to next animation frame."""
        if not self.is_spinning:
            return

        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self._update_display()

    def _update_display(self) -> None:
        """Update the displayed content."""
        frame = self._frames[self._frame_index]

        if self.text:
            content = f"[{self.style}]{frame}[/] {self.text}"
        else:
            content = f"[{self.style}]{frame}[/]"

        self.update(content)

    def pause(self) -> None:
        """Pause the spinner animation."""
        self.is_spinning = False
        if self._timer:
            self._timer.pause()

    def resume(self) -> None:
        """Resume the spinner animation."""
        self.is_spinning = True
        if self._timer:
            self._timer.resume()
        else:
            self._start_animation()

    def set_text(self, text: str) -> None:
        """Update the text displayed next to spinner.

        Args:
            text: New text to display
        """
        self.text = text
        self._update_display()

    def set_style(self, style: str) -> None:
        """Update the spinner style/color.

        Args:
            style: New style (color) to apply
        """
        self.style = style
        self._update_display()

    def on_unmount(self) -> None:
        """Clean up timer when widget is unmounted."""
        if self._timer:
            self._timer.stop()
            self._timer = None

    def watch_is_spinning(self, is_spinning: bool) -> None:
        """React to changes in spinning state.

        Args:
            is_spinning: New spinning state
        """
        if is_spinning:
            self._start_animation()
        elif self._timer:
            self._timer.pause()

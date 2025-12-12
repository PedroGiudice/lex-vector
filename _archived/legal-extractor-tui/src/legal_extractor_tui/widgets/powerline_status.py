"""
Powerline-style widgets for Textual.

This module provides a set of widgets for creating status bars and headers
in the style of the popular Powerline VIM plugin.

- PowerlineBar: The core widget that renders segments with separators.
- PowerlineHeader: A header widget with app name, version, and an optional clock.
- PowerlineFooter: A footer widget that renders segments from right to left.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, Label

# --- Constants for Powerline Glyphs ---

# Defines the glyphs used for separators.
# Use Nerd Fonts or a similar patched font for these to render correctly.
PL_LEFT_SOLID = ""
PL_RIGHT_SOLID = ""
PL_LEFT_DASH = ""
PL_RIGHT_DASH = ""

# ASCII fallbacks for terminals without patched fonts
ASCII_LEFT = ">"
ASCII_RIGHT = "<"


@dataclasses.dataclass
class PowerlineSegment:
    """
    Represents a single segment in a Powerline bar.

    Attributes:
        text: The text content of the segment.
        fg: The foreground (text) color.
        bg: The background color of the segment.
        icon: An optional icon to display before the text.
    """
    text: str
    fg: str
    bg: str
    icon: str | None = None


class PowerlineBar(Static):
    """
    A base widget that renders a list of Powerline segments with separators.
    """

    # CSS moved to widgets.tcss for centralized theme management

    # A list of segments to render.
    segments: reactive[list[PowerlineSegment]] = reactive([])
    # If true, use special Powerline fonts; otherwise, use ASCII fallbacks.
    use_powerline_fonts: reactive[bool] = reactive(True)

    def __init__(
        self,
        segments: list[PowerlineSegment] | None = None,
        use_powerline_fonts: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.segments = segments or []
        self.use_powerline_fonts = use_powerline_fonts

    def render(self) -> str:
        """Renders the segments into a Powerline bar."""
        if not self.segments:
            return ""

        separator = PL_LEFT_SOLID if self.use_powerline_fonts else ASCII_LEFT
        parts = []

        # Render the first segment
        first = self.segments[0]
        icon = f"{first.icon} " if first.icon else ""
        parts.append(f"[@{first.fg} on {first.bg}] {icon}{first.text} [/]")

        # Render subsequent segments
        for i in range(len(self.segments) - 1):
            current = self.segments[i]
            next_seg = self.segments[i + 1]

            # Add separator
            parts.append(f"[@{current.bg} on {next_seg.bg}]{separator}[/]")

            # Add next segment's content
            icon = f"{next_seg.icon} " if next_seg.icon else ""
            parts.append(f"[@{next_seg.fg} on {next_seg.bg}] {icon}{next_seg.text} [/]")

        # Add final blank separator to fill the line
        last_bg = self.segments[-1].bg
        parts.append(f"[@{last_bg} on default]{separator}[/]")

        return "".join(parts)


class PowerlineHeader(Widget):
    """
    A Powerline-style header widget.

    Displays application name, version, and an optional live clock on the right.
    """

    # CSS moved to widgets.tcss for centralized theme management

    time: reactive[datetime] = reactive(datetime.now)

    def __init__(
        self,
        app_name: str = "My App",
        version: str = "1.0",
        show_time: bool = True,
        use_powerline_fonts: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.app_name = app_name
        self.version = version
        self.show_time = show_time
        self.use_powerline_fonts = use_powerline_fonts
        self.timer = None  # Timer will be set in on_mount

    def on_mount(self) -> None:
        """Set up timer when widget is mounted."""
        self.timer = self.set_interval(1, self._update_time)

    def _update_time(self) -> None:
        """Callback to update the reactive time attribute."""
        self.time = datetime.now()

    def on_unmount(self) -> None:
        """Clean up the timer when widget is unmounted."""
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()

    def compose(self) -> ComposeResult:
        """Compose the header with left and right aligned sections."""
        left_segments = [
            PowerlineSegment(self.app_name, "$foreground", "$primary", icon="🚀"),
            PowerlineSegment(self.version, "$foreground", "$primary-darken-1"),
        ]
        with Container(classes="header-left"):
            yield PowerlineBar(segments=left_segments, use_powerline_fonts=self.use_powerline_fonts)

        if self.show_time:
            time_str = self.time.strftime("%H:%M:%S")
            right_segments = [
                PowerlineSegment(time_str, "$foreground", "$success", icon="🕒"),
            ]
            # PowerlineFooter handles right-to-left rendering
            with Container(classes="header-right"):
                yield PowerlineFooter(segments=right_segments, use_powerline_fonts=self.use_powerline_fonts)


class PowerlineFooter(Static):
    """
    A Powerline-style footer widget that renders segments from right to left.
    """

    # CSS moved to widgets.tcss for centralized theme management
    
    # A list of segments to render.
    segments: reactive[list[PowerlineSegment]] = reactive([])
    # If true, use special Powerline fonts; otherwise, use ASCII fallbacks.
    use_powerline_fonts: reactive[bool] = reactive(True)

    def __init__(
        self,
        segments: list[PowerlineSegment] | None = None,
        use_powerline_fonts: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.segments = segments or []
        self.use_powerline_fonts = use_powerline_fonts

    def render(self) -> str:
        """Renders the segments in a right-to-left Powerline bar."""
        if not self.segments:
            return ""

        separator = PL_RIGHT_SOLID if self.use_powerline_fonts else ASCII_RIGHT
        parts = []

        # Add initial blank separator
        first_bg = self.segments[0].bg
        parts.append(f"[@{first_bg} on default]{separator}[/]")

        # Render the first segment (which will be the rightmost)
        first = self.segments[0]
        icon = f"{first.icon} " if first.icon else ""
        parts.append(f"[@{first.fg} on {first.bg}] {icon}{first.text} [/]")

        # Render subsequent segments
        for i in range(len(self.segments) - 1):
            current = self.segments[i]
            next_seg = self.segments[i + 1]

            # Add separator
            parts.append(f"[@{next_seg.bg} on {current.bg}]{separator}[/]")

            # Add next segment's content
            icon = f"{next_seg.icon} " if next_seg.icon else ""
            parts.append(f"[@{next_seg.fg} on {next_seg.bg}] {icon}{next_seg.text} [/]")

        # Join the parts in reverse order to achieve the right-to-left effect
        return "".join(reversed(parts))


# --- Example Application ---
class PowerlineApp(App):
    """A simple Textual app to demonstrate Powerline widgets."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main-content {
        padding: 1;
        width: 100%;
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield PowerlineHeader(app_name="Textual Powerline", version="v0.1.0")
        yield Container(
            Label("This is the main content area."),
            Label("Try resizing the window!"),
            id="main-content"
        )
        
        footer_segments = [
            PowerlineSegment("INFO", "$background", "$warning"),
            PowerlineSegment("UTF-8", "$foreground", "$primary-darken-1"),
            PowerlineSegment("READY", "$foreground", "$success", icon="✅"),
        ]
        yield PowerlineFooter(segments=footer_segments)


if __name__ == "__main__":
    app = PowerlineApp()
    app.run()

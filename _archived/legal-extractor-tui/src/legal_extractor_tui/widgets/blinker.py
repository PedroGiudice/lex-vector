"""Blinking cursor widgets for terminal-style input display.

This module provides cursor widgets that blink like terminal cursors:
- Blinker: Simple blinking character (block, line, underscore, dot)
- InputCursor: Full input display with prompt, text, and blinking cursor
"""

from typing import Literal

from textual.reactive import reactive
from textual.widgets import Static


# Cursor character definitions (visible, hidden)
CURSOR_CHARS = {
    "block": ("█", " "),
    "line": ("│", " "),
    "underscore": ("_", " "),
    "dot": ("●", "○"),
}


class Blinker(Static):
    """A blinking cursor character.

    Alternates between visible and hidden states at regular intervals,
    similar to terminal text cursors.

    Example:
        ```python
        # Block cursor blinking every 530ms
        cursor = Blinker(cursor_type="block")

        # Fast dot cursor (300ms)
        dot = Blinker(cursor_type="dot", blink_rate_ms=300)

        # Control
        cursor.pause()   # Stop blinking (stays visible)
        cursor.resume()  # Resume blinking
        ```
    """

    visible: reactive[bool] = reactive(True)
    """Whether the cursor is currently in visible state."""

    def __init__(
        self,
        cursor_type: Literal["block", "line", "underscore", "dot"] = "block",
        blink_rate_ms: int = 530,
        style: str = "reverse",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        """Initialize blinking cursor.

        Args:
            cursor_type: Type of cursor character to display
            blink_rate_ms: Milliseconds between blink toggles
            style: Text style for cursor
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)

        self.cursor_type = cursor_type
        self.blink_rate_ms = blink_rate_ms
        self.cursor_style = style
        self._is_blinking = True

        # Get cursor characters
        self._visible_char, self._hidden_char = CURSOR_CHARS[cursor_type]

    def on_mount(self) -> None:
        """Start blinking when widget is mounted."""
        self._update_display()
        self._blink_timer = self.set_interval(self.blink_rate_ms / 1000, self._toggle)

    def on_unmount(self) -> None:
        """Clean up timer when widget is unmounted."""
        if hasattr(self, '_blink_timer') and self._blink_timer:
            self._blink_timer.stop()

    def _toggle(self) -> None:
        """Toggle cursor visibility."""
        if self._is_blinking:
            self.visible = not self.visible

    def _update_display(self) -> None:
        """Update the displayed cursor character."""
        char = self._visible_char if self.visible else self._hidden_char
        self.update(f"[{self.cursor_style}]{char}[/]")

    def watch_visible(self, visible: bool) -> None:
        """React to visibility changes.

        Args:
            visible: New visibility state
        """
        self._update_display()

    def pause(self) -> None:
        """Pause blinking (cursor stays visible)."""
        self._is_blinking = False
        self.visible = True

    def resume(self) -> None:
        """Resume blinking animation."""
        self._is_blinking = True


class InputCursor(Static):
    """Terminal-style input display with prompt, text, and blinking cursor.

    Displays a complete input line with:
    - Optional prompt (e.g., "$ ", "> ")
    - Current input text
    - Blinking cursor at end

    Example:
        ```python
        # Command prompt
        input_widget = InputCursor(prompt="$ ")

        # User types
        input_widget.set_input("ls -la")
        # Display: "$ ls -la█"

        # Character-by-character
        input_widget.append("h")
        input_widget.append("i")
        input_widget.backspace()
        # Display: "$ h█"

        # Clear input
        input_widget.clear()
        # Display: "$ █"
        ```
    """

    cursor_visible: reactive[bool] = reactive(True)
    """Whether the cursor is currently visible."""

    def __init__(
        self,
        prompt: str = "",
        initial_text: str = "",
        cursor_type: Literal["block", "line", "underscore", "dot"] = "block",
        blink_rate_ms: int = 530,
        prompt_style: str = "bold cyan",
        text_style: str = "white",
        cursor_style: str = "reverse",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        """Initialize input cursor widget.

        Args:
            prompt: Prompt string (e.g., "$ ", "> ")
            initial_text: Initial input text
            cursor_type: Type of cursor character
            blink_rate_ms: Cursor blink rate in milliseconds
            prompt_style: Style for prompt
            text_style: Style for input text
            cursor_style: Style for cursor
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)

        self.prompt = prompt
        self.input_text = initial_text
        self.cursor_type = cursor_type
        self.blink_rate_ms = blink_rate_ms
        self.prompt_style = prompt_style
        self.text_style = text_style
        self.cursor_style = cursor_style
        self._is_blinking = True

        # Get cursor characters
        self._visible_char, self._hidden_char = CURSOR_CHARS[cursor_type]

    def on_mount(self) -> None:
        """Start cursor blinking when widget is mounted."""
        self._update_display()
        self._cursor_timer = self.set_interval(self.blink_rate_ms / 1000, self._toggle_cursor)

    def on_unmount(self) -> None:
        """Clean up timer when widget is unmounted."""
        if hasattr(self, '_cursor_timer') and self._cursor_timer:
            self._cursor_timer.stop()

    def _toggle_cursor(self) -> None:
        """Toggle cursor visibility."""
        if self._is_blinking:
            self.cursor_visible = not self.cursor_visible

    def _update_display(self) -> None:
        """Update the complete input display."""
        # Build prompt part
        if self.prompt:
            prompt_part = f"[{self.prompt_style}]{self.prompt}[/]"
        else:
            prompt_part = ""

        # Build text part
        if self.input_text:
            text_part = f"[{self.text_style}]{self.input_text}[/]"
        else:
            text_part = ""

        # Build cursor part
        cursor_char = self._visible_char if self.cursor_visible else self._hidden_char
        cursor_part = f"[{self.cursor_style}]{cursor_char}[/]"

        # Combine all parts
        content = f"{prompt_part}{text_part}{cursor_part}"
        self.update(content)

    def watch_cursor_visible(self, visible: bool) -> None:
        """React to cursor visibility changes.

        Args:
            visible: New cursor visibility state
        """
        self._update_display()

    def set_input(self, text: str) -> None:
        """Set the input text.

        Args:
            text: New input text to display
        """
        self.input_text = text
        self._update_display()

    def append(self, char: str) -> None:
        """Append a character to the input text.

        Args:
            char: Character to append
        """
        self.input_text += char
        self._update_display()

    def backspace(self) -> None:
        """Remove the last character from input text."""
        if self.input_text:
            self.input_text = self.input_text[:-1]
            self._update_display()

    def clear(self) -> None:
        """Clear all input text."""
        self.input_text = ""
        self._update_display()

    def pause_cursor(self) -> None:
        """Pause cursor blinking (cursor stays visible)."""
        self._is_blinking = False
        self.cursor_visible = True

    def resume_cursor(self) -> None:
        """Resume cursor blinking."""
        self._is_blinking = True

    def set_prompt(self, prompt: str) -> None:
        """Update the prompt string.

        Args:
            prompt: New prompt to display
        """
        self.prompt = prompt
        self._update_display()

"""Preview Modal Screen - Full text preview in floating modal."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical, Horizontal, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class PreviewModalScreen(ModalScreen):
    """Modal screen for viewing full extracted text.

    Attributes:
        text: The full extracted text to display
        metadata: Dict with filename, length, system info
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=True),
        Binding("q", "dismiss", "Close"),
    ]

    def __init__(
        self,
        text: str = "",
        metadata: dict | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._text = text
        self._metadata = metadata or {}

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Center():
            with Middle():
                with Vertical(id="preview-dialog"):
                    # Header
                    with Horizontal(classes="preview-header"):
                        yield Label("📄 Preview: Extracted Text", classes="preview-title")
                        char_count = len(self._text)
                        yield Label(f"[{char_count:,} chars]", classes="preview-badge")

                    # Content - scrollable full text
                    with VerticalScroll(id="preview-content"):
                        yield Static(self._text or "No text available", id="preview-text-full")

                    # Footer with buttons
                    with Horizontal(classes="preview-footer"):
                        yield Button("Close [Esc]", id="close-btn", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "close-btn":
            self.dismiss()

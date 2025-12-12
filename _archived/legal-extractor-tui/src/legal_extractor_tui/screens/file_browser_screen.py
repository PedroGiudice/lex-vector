"""File browser modal screen for selecting PDF files.

This module provides a modal screen with a file browser for selecting
PDF files to process.
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from legal_extractor_tui.widgets.file_browser import FileBrowser, FileSelected


class FileBrowserScreen(ModalScreen[Path | None]):
    """Modal screen for browsing and selecting PDF files.

    This screen displays a file browser filtered to show only PDF files.
    When a file is selected, the screen is dismissed and returns the
    selected path.

    Keybindings:
        - Escape: Close without selecting
        - q: Close without selecting

    Returns:
        Path to selected PDF file, or None if cancelled
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("q", "cancel", "Cancel", show=False),
    ]

    def __init__(
        self,
        initial_path: str | Path = ".",
        name: str | None = None,
    ) -> None:
        """Initialize file browser screen.

        Args:
            initial_path: Directory to start browsing from
            name: Optional name for the screen
        """
        super().__init__(name=name)
        self._initial_path = Path(initial_path)

    def compose(self) -> ComposeResult:
        """Compose the file browser modal layout.

        Yields:
            Centered modal with file browser and cancel button
        """
        with Center():
            with Middle():
                with Vertical(id="file-browser-dialog"):
                    yield Static("Select PDF File", id="browser-title")
                    yield FileBrowser(
                        path=self._initial_path,
                        filter_extensions=[".pdf"],
                        title="",
                        id="file-browser"
                    )
                    yield Button("Cancel [Esc]", id="cancel-btn", variant="error")

    def on_file_selected(self, event: FileSelected) -> None:
        """Handle file selection from browser.

        Args:
            event: FileSelected message with selected path
        """
        # Stop event propagation
        event.stop()

        # Only accept PDF files
        if event.path.suffix.lower() == ".pdf" and event.path.is_file():
            self.dismiss(event.path)
        else:
            # Show error or just ignore non-PDF selections
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle cancel button press.

        Args:
            event: Button pressed event
        """
        if event.button.id == "cancel-btn":
            self.action_cancel()

    def action_cancel(self) -> None:
        """Cancel file selection and close screen."""
        self.dismiss(None)

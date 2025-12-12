"""File selector widget for choosing PDF files to process.

Example:
    ```python
    from legal_extractor_tui.widgets.file_selector import FileSelector
    from legal_extractor_tui.messages.extractor_messages import FileSelected

    selector = FileSelector()

    @on(FileSelected)
    def handle_file_selected(self, event: FileSelected) -> None:
        print(f"Selected: {event.path}")
        print(f"Size: {event.path.stat().st_size} bytes")
    ```
"""

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, Static

from legal_extractor_tui.messages.extractor_messages import FileSelected

from textual.message import Message


class FileSelector(Vertical):
    """Widget for selecting PDF files to process.

    Displays current file path, browse button, and file information.
    Validates that selected files are PDFs.
    """

    class BrowseRequested(Message):
        """Emitted when user clicks Browse button."""
        pass

    # CSS moved to widgets.tcss for centralized theme management

    selected_path: reactive[str] = reactive("")
    file_size: reactive[str] = reactive("N/A")
    file_valid: reactive[bool] = reactive(False)
    error_message: reactive[str] = reactive("")

    def __init__(
        self,
        initial_path: str = "",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize file selector.

        Args:
            initial_path: Initial file path to display
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self.selected_path = initial_path

    def compose(self) -> ComposeResult:
        """Compose the file selector layout.

        Yields:
            Title, input field, browse button, and file info display
        """
        yield Label("Select PDF File", classes="selector-title")

        with Horizontal(classes="file-input-container"):
            yield Input(
                value=self.selected_path,
                placeholder="/path/to/document.pdf",
                id="file-path-input"
            )
            yield Button("Browse", id="browse-button", variant="primary")

        with Vertical(classes="file-info", id="file-info-panel"):
            with Horizontal(classes="file-info-row"):
                yield Label("File:", classes="file-info-label")
                yield Label(self._get_filename(), classes="file-info-value", id="filename-label")

            with Horizontal(classes="file-info-row"):
                yield Label("Size:", classes="file-info-label")
                yield Label(self.file_size, classes="file-info-value", id="filesize-label")

            with Horizontal(classes="file-info-row"):
                yield Label("Status:", classes="file-info-label")
                yield Label(
                    "Ready" if self.file_valid else "No file selected",
                    classes="file-info-value",
                    id="status-label"
                )

        # Persistent status label - updated dynamically
        yield Label("", classes="status-message", id="status-message")

    def _get_filename(self) -> str:
        """Get filename from current path.

        Returns:
            Filename or "N/A" if no file selected
        """
        if self.selected_path:
            return Path(self.selected_path).name
        return "N/A"

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format.

        Args:
            size_bytes: File size in bytes

        Returns:
            Formatted size string (e.g., "2.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _validate_file(self, path: str) -> tuple[bool, str]:
        """Validate that file exists and is a PDF.

        Args:
            path: File path to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not path:
            return False, ""

        file_path = Path(path)

        if not file_path.exists():
            return False, "File does not exist"

        if not file_path.is_file():
            return False, "Path is not a file"

        if file_path.suffix.lower() != '.pdf':
            return False, "File must be a PDF (.pdf extension)"

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            return False, "File is not readable (permission denied)"

        return True, ""

    def _update_file_info(self, path: str) -> None:
        """Update file information display.

        Args:
            path: File path to get information from
        """
        self.selected_path = path
        is_valid, error = self._validate_file(path)
        self.file_valid = is_valid
        self.error_message = error

        if is_valid:
            file_path = Path(path)
            size_bytes = file_path.stat().st_size
            self.file_size = self._format_file_size(size_bytes)
        else:
            self.file_size = "N/A"

        # Update UI elements
        if self.is_mounted:
            filename_label = self.query_one("#filename-label", Label)
            filename_label.update(self._get_filename())

            filesize_label = self.query_one("#filesize-label", Label)
            filesize_label.update(self.file_size)

            status_label = self.query_one("#status-label", Label)
            status_label.update("Ready" if is_valid else f"Error: {error}" if error else "No file selected")

            # Update error/valid message
            self._update_status_message()

    def _update_status_message(self) -> None:
        """Update error or valid status message display."""
        try:
            status_msg = self.query_one("#status-message", Label)
            # Reset classes
            status_msg.remove_class("error", "valid")

            if self.error_message:
                status_msg.update(self.error_message)
                status_msg.add_class("error")
            elif self.file_valid:
                status_msg.update("Valid PDF file selected")
                status_msg.add_class("valid")
            else:
                status_msg.update("")
        except Exception:
            pass  # Widget not yet mounted

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle manual path entry.

        Args:
            event: Input submission event
        """
        path = event.value.strip()
        self._update_file_info(path)

        # If valid, emit FileSelected message
        if self.file_valid:
            self.post_message(FileSelected(Path(path)))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes.

        Args:
            event: Input change event
        """
        # Only validate on blur or submit to avoid constant errors while typing
        pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle browse button click.

        Args:
            event: Button press event
        """
        if event.button.id == "browse-button":
            # Emit message for parent to handle (show FileBrowser modal)
            self.post_message(self.BrowseRequested())

    def set_path(self, path: str | Path) -> None:
        """Set the file path programmatically.

        Args:
            path: Path to set

        Example:
            ```python
            selector.set_path("/home/user/document.pdf")
            ```
        """
        path_str = str(path)
        self._update_file_info(path_str)

        # Update input field
        if self.is_mounted:
            input_field = self.query_one("#file-path-input", Input)
            input_field.value = path_str

        # If valid, emit FileSelected message
        if self.file_valid:
            self.post_message(FileSelected(Path(path_str)))

    def get_selected_file(self) -> Path | None:
        """Get the currently selected file path.

        Returns:
            Path object if valid file selected, None otherwise
        """
        if self.file_valid and self.selected_path:
            return Path(self.selected_path)
        return None

    def clear_selection(self) -> None:
        """Clear the current file selection."""
        self._update_file_info("")
        if self.is_mounted:
            input_field = self.query_one("#file-path-input", Input)
            input_field.value = ""

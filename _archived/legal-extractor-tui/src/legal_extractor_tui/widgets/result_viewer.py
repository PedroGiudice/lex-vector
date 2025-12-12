"""Markdown viewer widget for displaying results and documentation.

Example:
    ```python
    from legal_extractor_tui.widgets.result_viewer import ResultViewer

    viewer = ResultViewer()

    # Load markdown content
    viewer.load_content("# Results\\n\\nProcessing completed successfully.")

    # Load from file
    viewer.load_file("results/output.md")

    # Clear content
    viewer.clear()
    ```
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Markdown, Static


class ResultViewer(Vertical):
    """Markdown viewer for displaying results and documentation.

    Provides a rich markdown rendering interface with source tracking.
    """

    # CSS moved to widgets.tcss for centralized theme management

    def __init__(
        self,
        title: str = "Results",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize result viewer.

        Args:
            title: Title to display in the header
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self._title = title
        self._source = ""
        self._has_content = False

    def compose(self) -> ComposeResult:
        """Compose the result viewer layout.

        Yields:
            Header with title and source, plus content area
        """
        # Header container
        with Vertical(classes="viewer-header"):
            yield Label(self._title, classes="viewer-title", id="viewer-title")
            yield Label("", classes="viewer-source", id="viewer-source")

        # Content area (initially empty)
        yield Static(
            "No content loaded",
            classes="empty-message",
            id="viewer-content"
        )

    def load_content(self, content: str, source: str = "") -> None:
        """Load markdown content into the viewer.

        Args:
            content: Markdown content to display
            source: Optional source description (e.g., "Generated", "results.md")

        Example:
            ```python
            viewer.load_content(
                "# Analysis Results\\n\\n- Items: 42\\n- Errors: 0",
                source="Generated from pipeline"
            )
            ```
        """
        self._source = source
        self._has_content = True

        # Update source label
        source_label = self.query_one("#viewer-source", Label)
        source_label.update(f"Source: {source}" if source else "")

        # Remove old content widget
        old_content = self.query_one("#viewer-content")
        old_content.remove()

        # Create new Markdown widget
        markdown = Markdown(content, id="viewer-content")
        self.mount(markdown)

    def load_file(self, path: str | Path) -> None:
        """Load markdown content from a file.

        Args:
            path: Path to markdown file

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file can't be read

        Example:
            ```python
            viewer.load_file("output/results.md")
            viewer.load_file(Path("docs/README.md"))
            ```
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        content = file_path.read_text(encoding="utf-8")
        self.load_content(content, source=str(file_path))

    def clear(self) -> None:
        """Clear the viewer content and show empty message.

        Example:
            ```python
            viewer.clear()  # Reset to empty state
            ```
        """
        self._source = ""
        self._has_content = False

        # Update source label
        source_label = self.query_one("#viewer-source", Label)
        source_label.update("")

        # Remove old content widget
        old_content = self.query_one("#viewer-content")
        old_content.remove()

        # Restore empty message
        empty = Static(
            "No content loaded",
            classes="empty-message",
            id="viewer-content"
        )
        self.mount(empty)

    def set_title(self, title: str) -> None:
        """Update the viewer title.

        Args:
            title: New title to display

        Example:
            ```python
            viewer.set_title("Processing Results")
            ```
        """
        self._title = title
        title_label = self.query_one("#viewer-title", Label)
        title_label.update(title)

    @property
    def has_content(self) -> bool:
        """Check if viewer has content loaded.

        Returns:
            True if content is loaded, False if empty
        """
        return self._has_content

    @property
    def source(self) -> str:
        """Get the current content source.

        Returns:
            Source description string
        """
        return self._source

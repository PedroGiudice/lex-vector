"""File browser widget with directory tree and filtering capabilities.

Example:
    ```python
    from legal_extractor_tui.widgets.file_browser import FileBrowser, FileSelected

    browser = FileBrowser(
        path="/home/user/documents",
        filter_extensions=[".txt", ".md", ".pdf"]
    )

    @on(FileSelected)
    def handle_file_selected(self, event: FileSelected) -> None:
        print(f"Selected: {event.path}")
    ```
"""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import DirectoryTree, Label


class FileSelected(Message):
    """Message sent when a file is selected.

    Attributes:
        path: Path to the selected file
    """

    def __init__(self, path: Path) -> None:
        """Initialize the message.

        Args:
            path: Path to the selected file
        """
        super().__init__()
        self.path = path


class FilteredDirectoryTree(DirectoryTree):
    """DirectoryTree with file extension filtering.

    Only shows files with specified extensions.
    """

    def __init__(
        self,
        path: str | Path,
        filter_extensions: list[str] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize filtered directory tree.

        Args:
            path: Root path to browse
            filter_extensions: List of file extensions to show (e.g., [".py", ".txt"])
                              If None, shows all files
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(path, name=name, id=id, classes=classes)
        self.filter_extensions = filter_extensions or []

    def filter_paths(self, paths: list[Path]) -> list[Path]:
        """Filter paths based on extension filter.

        Args:
            paths: List of paths to filter

        Returns:
            Filtered list of paths
        """
        if not self.filter_extensions:
            # No filter - show all
            return paths

        filtered = []
        for path in paths:
            if path.is_dir():
                # Always show directories
                filtered.append(path)
            elif any(str(path).endswith(ext) for ext in self.filter_extensions):
                # Show files matching extensions
                filtered.append(path)

        return filtered


class FileBrowser(Vertical):
    """File browser widget with directory tree and filtering.

    Provides a file browsing interface with optional extension filtering.
    """

    # CSS moved to widgets.tcss for centralized theme management

    def __init__(
        self,
        path: str | Path = ".",
        filter_extensions: list[str] | None = None,
        title: str = "File Browser",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize file browser.

        Args:
            path: Root path to browse
            filter_extensions: List of file extensions to show (e.g., [".py", ".txt"])
            title: Title to display above the tree
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self._path = Path(path)
        self._filter_extensions = filter_extensions or []
        self._title = title

    def compose(self) -> ComposeResult:
        """Compose the file browser layout.

        Yields:
            Title label and directory tree
        """
        yield Label(self._title, classes="browser-title")
        yield FilteredDirectoryTree(
            self._path,
            filter_extensions=self._filter_extensions,
            id="file-tree"
        )

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection from directory tree.

        Args:
            event: The DirectoryTree.FileSelected event
        """
        # Prevent event from bubbling
        event.stop()

        # Post our custom FileSelected message
        self.post_message(FileSelected(event.path))

    def set_path(self, path: str | Path) -> None:
        """Change the root path of the browser.

        Args:
            path: New root path to browse

        Example:
            ```python
            browser.set_path("/home/user/projects")
            ```
        """
        self._path = Path(path)

        # Remove old tree and create new one
        tree = self.query_one("#file-tree", FilteredDirectoryTree)
        tree.remove()

        new_tree = FilteredDirectoryTree(
            self._path,
            filter_extensions=self._filter_extensions,
            id="file-tree"
        )
        self.mount(new_tree)

    def set_filter(self, extensions: list[str]) -> None:
        """Update the file extension filter.

        Args:
            extensions: New list of extensions to filter by

        Example:
            ```python
            browser.set_filter([".py", ".pyi"])
            browser.set_filter([])  # Clear filter (show all)
            ```
        """
        self._filter_extensions = extensions

        # Recreate tree with new filter
        tree = self.query_one("#file-tree", FilteredDirectoryTree)
        tree.remove()

        new_tree = FilteredDirectoryTree(
            self._path,
            filter_extensions=self._filter_extensions,
            id="file-tree"
        )
        self.mount(new_tree)

    def get_selected_path(self) -> Path | None:
        """Get the currently selected path in the tree.

        Returns:
            Path to selected file/directory, or None if nothing selected
        """
        tree = self.query_one("#file-tree", FilteredDirectoryTree)
        if tree.cursor_node:
            return tree.cursor_node.data.path
        return None

    def expand_all(self) -> None:
        """Expand all nodes in the directory tree."""
        tree = self.query_one("#file-tree", FilteredDirectoryTree)
        tree.root.expand_all()

    def collapse_all(self) -> None:
        """Collapse all nodes in the directory tree."""
        tree = self.query_one("#file-tree", FilteredDirectoryTree)
        tree.root.collapse_all()

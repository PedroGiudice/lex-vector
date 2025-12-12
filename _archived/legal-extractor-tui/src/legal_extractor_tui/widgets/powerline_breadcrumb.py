"""Powerline-style breadcrumb navigation widget.

This module provides a clickable breadcrumb navigation component with
Powerline-style separators for navigating hierarchical paths or menus.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static


# Powerline separator characters
PL_LEFT_SOLID = ""
PL_RIGHT_SOLID = ""
ASCII_SEPARATOR = ">"


class PowerlineBreadcrumb(Widget):
    """A clickable breadcrumb navigation with Powerline styling.

    Displays a navigable path with arrow separators. Each item is clickable
    and emits a CrumbClicked message when selected.

    Example:
        ```python
        # Create breadcrumb
        breadcrumb = PowerlineBreadcrumb(
            ["Home", "Projects", "TUI-App", "Widgets"],
            separator=""
        )

        # Handle clicks
        def on_powerline_breadcrumb_crumb_clicked(
            self, event: PowerlineBreadcrumb.CrumbClicked
        ) -> None:
            self.log(f"Clicked: {event.name} at index {event.index}")
            # Navigate to clicked level

        # Programmatic navigation
        breadcrumb.push("new_folder")  # Add item
        breadcrumb.pop()               # Remove last item
        breadcrumb.set_items(["Home", "Documents"])  # Replace all
        ```
    """

    # CSS moved to widgets.tcss for centralized theme management

    items: reactive[list[str]] = reactive([])
    """List of breadcrumb items to display."""

    class CrumbClicked(Message):
        """Message emitted when a breadcrumb item is clicked.

        Attributes:
            index: Index of the clicked item (0-based)
            name: Text of the clicked item
        """

        def __init__(self, index: int, name: str) -> None:
            super().__init__()
            self.index = index
            self.name = name

    def __init__(
        self,
        items: list[str] | None = None,
        separator: str = "",
        use_powerline_fonts: bool = True,
        fg_color: str = "$foreground",
        bg_color: str = "$primary",
        separator_color: str = "$primary-darken-1",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ):
        """Initialize breadcrumb widget.

        Args:
            items: Initial list of breadcrumb items
            separator: Custom separator character (defaults to Powerline arrow)
            use_powerline_fonts: Whether to use Powerline glyphs
            fg_color: Foreground (text) color for crumbs
            bg_color: Background color for crumbs
            separator_color: Color for separators
            name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=name, id=id, classes=classes)

        self.items = items or []
        self.use_powerline_fonts = use_powerline_fonts
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.separator_color = separator_color

        # Determine separator
        if separator:
            self._separator = separator
        elif use_powerline_fonts:
            self._separator = PL_LEFT_SOLID
        else:
            self._separator = ASCII_SEPARATOR

    def compose(self) -> ComposeResult:
        """Compose the breadcrumb widget."""
        with Horizontal(classes="breadcrumb-container"):
            yield from self._build_crumbs()

    def _build_crumbs(self) -> list[Static]:
        """Build the list of crumb and separator widgets.

        Returns:
            List of Static widgets representing crumbs and separators
        """
        widgets = []

        for i, item in enumerate(self.items):
            # Create clickable crumb
            crumb = Static(
                f"[{self.fg_color} on {self.bg_color}] {item} [/]",
                classes="crumb",
            )
            # Store index as metadata for click handling
            crumb.add_class(f"crumb-{i}")
            widgets.append(crumb)

            # Add separator (except after last item)
            if i < len(self.items) - 1:
                separator = Static(
                    f"[{self.bg_color} on {self.separator_color}]{self._separator}[/]",
                    classes="separator",
                )
                widgets.append(separator)

        return widgets

    def watch_items(self, items: list[str]) -> None:
        """React to changes in items list.

        Args:
            items: New list of breadcrumb items
        """
        # Rebuild the breadcrumb display
        if self.is_mounted:
            self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the breadcrumb display with current items."""
        # Remove existing children
        container = self.query_one(".breadcrumb-container", Horizontal)
        container.remove_children()

        # Add new crumbs
        for widget in self._build_crumbs():
            container.mount(widget)

    async def on_click(self, event) -> None:
        """Handle click events on breadcrumb items.

        Args:
            event: Click event
        """
        # Find which crumb was clicked
        target = event.widget
        if hasattr(target, "has_class") and "crumb" in target.classes:
            # Extract index from class name
            for cls in target.classes:
                if cls.startswith("crumb-"):
                    try:
                        index = int(cls.split("-")[1])
                        if 0 <= index < len(self.items):
                            # Emit message
                            self.post_message(
                                self.CrumbClicked(index, self.items[index])
                            )
                    except (ValueError, IndexError):
                        pass

    def set_items(self, items: list[str]) -> None:
        """Replace all breadcrumb items.

        Args:
            items: New list of items to display
        """
        self.items = items

    def push(self, item: str) -> None:
        """Add an item to the end of the breadcrumb.

        Args:
            item: Item to add
        """
        new_items = self.items.copy()
        new_items.append(item)
        self.items = new_items

    def pop(self) -> str | None:
        """Remove and return the last breadcrumb item.

        Returns:
            The removed item, or None if breadcrumb is empty
        """
        if not self.items:
            return None

        new_items = self.items.copy()
        removed = new_items.pop()
        self.items = new_items
        return removed

    def clear(self) -> None:
        """Remove all breadcrumb items."""
        self.items = []

    def navigate_to(self, index: int) -> None:
        """Navigate to a specific breadcrumb level by index.

        Truncates the breadcrumb to the specified index + 1 items.

        Args:
            index: Index to navigate to (0-based)
        """
        if 0 <= index < len(self.items):
            self.items = self.items[: index + 1]

    def get_current_path(self) -> str:
        """Get the current breadcrumb path as a string.

        Returns:
            Path string with items joined by '/'
        """
        return "/".join(self.items)

    def set_path(self, path: str, separator: str = "/") -> None:
        """Set breadcrumb items from a path string.

        Args:
            path: Path string to parse
            separator: Character used to split the path
        """
        if path:
            self.items = [item.strip() for item in path.split(separator) if item.strip()]
        else:
            self.items = []

"""Collapsible sidebar widget with navigation options.

Example:
    ```python
    from legal_extractor_tui.widgets.sidebar import Sidebar, OptionSelected

    sidebar = Sidebar()

    @on(OptionSelected)
    def handle_selection(self, event: OptionSelected) -> None:
        print(f"Selected: {event.option_id}")
    ```
"""

from textual import on
from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, OptionList
from textual.widgets.option_list import Option


class OptionSelected(Message):
    """Message sent when an option is selected.

    Attributes:
        option_id: ID of the selected option
        option_label: Label text of the selected option
    """

    def __init__(self, option_id: str, option_label: str) -> None:
        """Initialize the message.

        Args:
            option_id: ID of the selected option
            option_label: Label text of the selected option
        """
        super().__init__()
        self.option_id = option_id
        self.option_label = option_label


class Sidebar(Container):
    """Collapsible sidebar with navigation options.

    Attributes:
        collapsed: Whether the sidebar is collapsed
        DEFAULT_CSS: Inline CSS styling for the sidebar
    """

    # CSS moved to widgets.tcss for centralized theme management

    collapsed: reactive[bool] = reactive(False)

    def __init__(
        self,
        options: list[tuple[str, str]] | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the sidebar.

        Args:
            options: List of (id, label) tuples for navigation options.
                    Defaults to standard navigation items.
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self._options = options or [
            ("dashboard", "📊 Dashboard"),
            ("files", "📁 Files"),
            ("logs", "📜 Logs"),
            ("settings", "⚙️  Settings"),
        ]

    def compose(self) -> ComposeResult:
        """Compose the sidebar layout.

        Yields:
            Button for toggle and OptionList for navigation
        """
        yield Button("☰", id="sidebar-toggle", variant="default")
        yield OptionList(
            *[Option(label, id=opt_id) for opt_id, label in self._options],
            id="sidebar-options"
        )

    @on(Button.Pressed, "#sidebar-toggle")
    def handle_toggle(self) -> None:
        """Handle toggle button press."""
        self.toggle()

    @on(OptionList.OptionSelected)
    def handle_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle option selection from OptionList.

        Args:
            event: The OptionList.OptionSelected event
        """
        if event.option_id:
            # Find the label for this option
            label = next(
                (lbl for opt_id, lbl in self._options if opt_id == event.option_id),
                event.option_id
            )
            # Post our custom message
            self.post_message(OptionSelected(event.option_id, label))

    def toggle(self) -> None:
        """Toggle the sidebar between collapsed and expanded states."""
        self.collapsed = not self.collapsed
        if self.collapsed:
            self.add_class("collapsed")
        else:
            self.remove_class("collapsed")

    def expand(self) -> None:
        """Expand the sidebar."""
        if self.collapsed:
            self.toggle()

    def collapse(self) -> None:
        """Collapse the sidebar."""
        if not self.collapsed:
            self.toggle()

    def watch_collapsed(self, collapsed: bool) -> None:
        """React to collapsed state changes.

        Args:
            collapsed: New collapsed state
        """
        button = self.query_one("#sidebar-toggle", Button)
        button.label = "☰" if collapsed else "✕"

    def set_options(self, options: list[tuple[str, str]]) -> None:
        """Update the navigation options.

        Args:
            options: List of (id, label) tuples for navigation options

        Example:
            ```python
            sidebar.set_options([
                ("home", "🏠 Home"),
                ("search", "🔍 Search"),
                ("help", "❓ Help"),
            ])
            ```
        """
        self._options = options
        option_list = self.query_one("#sidebar-options", OptionList)
        option_list.clear_options()
        for opt_id, label in options:
            option_list.add_option(Option(label, id=opt_id))

"""Judicial system selector widget.

Example:
    ```python
    from legal_extractor_tui.widgets.system_selector import SystemSelector
    from legal_extractor_tui.messages.extractor_messages import SystemChanged

    selector = SystemSelector()

    @on(SystemChanged)
    def handle_system_changed(self, event: SystemChanged) -> None:
        print(f"System changed to: {event.system}")
    ```
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Label, Select, Static

from legal_extractor_tui.messages.extractor_messages import SystemChanged


# Judicial systems with descriptions
JUDICIAL_SYSTEMS = {
    "auto": "Automatic Detection - Let the system identify the judicial system",
    "pje": "PJE - Processo Judicial Eletrônico (National system)",
    "esaj": "E-SAJ - Electronic System of Justice Administration (TJSP)",
    "eproc": "EPROC - Electronic Process (TRF4)",
    "projudi": "PROJUDI - Process Management System",
    "stf": "STF - Supreme Federal Court",
    "stj": "STJ - Superior Court of Justice",
}

# Short names for display
SYSTEM_NAMES = {
    "auto": "AUTO",
    "pje": "PJE",
    "esaj": "E-SAJ",
    "eproc": "EPROC",
    "projudi": "PROJUDI",
    "stf": "STF",
    "stj": "STJ",
}


class SystemSelector(Vertical):
    """Widget for selecting the judicial system.

    Provides dropdown selection with system descriptions.
    """

    # CSS moved to widgets.tcss for centralized theme management

    selected_system: reactive[str] = reactive("auto")

    def __init__(
        self,
        initial_system: str = "auto",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize system selector.

        Args:
            initial_system: Initial system selection (default: "auto")
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self.selected_system = initial_system

    def compose(self) -> ComposeResult:
        """Compose the system selector layout.

        Yields:
            Title, dropdown select, and description display
        """
        yield Label("Judicial System", classes="selector-title")

        with Horizontal(classes="select-container"):
            # Create options for Select widget
            options = [
                (SYSTEM_NAMES[code], code)
                for code in JUDICIAL_SYSTEMS.keys()
            ]
            yield Select(
                options=options,
                value=self.selected_system,
                id="system-select",
                allow_blank=False,
            )

        with Vertical(classes="system-description", id="description-panel"):
            yield Label("System Description:", classes="description-label")
            yield Label(
                JUDICIAL_SYSTEMS[self.selected_system],
                id="description-text",
                classes="description-label"
            )

        yield Label(
            f"Current: {SYSTEM_NAMES[self.selected_system]}",
            classes="current-system",
            id="current-system-label"
        )

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle system selection change.

        Args:
            event: Select change event
        """
        if event.select.id == "system-select":
            new_system = str(event.value)
            self._update_system(new_system)

    def _update_system(self, system: str) -> None:
        """Update selected system and UI.

        Args:
            system: System code to select
        """
        if system not in JUDICIAL_SYSTEMS:
            self.log.warning(f"Invalid system code: {system}")
            return

        self.selected_system = system

        # Update description
        if self.is_mounted:
            description_text = self.query_one("#description-text", Label)
            description_text.update(JUDICIAL_SYSTEMS[system])

            current_label = self.query_one("#current-system-label", Label)
            current_label.update(f"Current: {SYSTEM_NAMES[system]}")

        # Emit SystemChanged message
        self.post_message(SystemChanged(system))

    def set_system(self, system: str) -> None:
        """Set system programmatically.

        Args:
            system: System code to select

        Example:
            ```python
            selector.set_system("pje")
            ```
        """
        if system not in JUDICIAL_SYSTEMS:
            raise ValueError(f"Invalid system code: {system}")

        self._update_system(system)

        # Update select widget
        if self.is_mounted:
            select = self.query_one("#system-select", Select)
            select.value = system

    def get_selected_system(self) -> str:
        """Get currently selected system code.

        Returns:
            System code (e.g., "auto", "pje", "esaj")
        """
        return self.selected_system

    def get_system_name(self) -> str:
        """Get display name of selected system.

        Returns:
            Human-readable system name
        """
        return SYSTEM_NAMES[self.selected_system]

    def get_system_description(self) -> str:
        """Get description of selected system.

        Returns:
            Full description text
        """
        return JUDICIAL_SYSTEMS[self.selected_system]

    def reset_to_auto(self) -> None:
        """Reset selection to automatic detection."""
        self.set_system("auto")

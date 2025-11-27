"""Configuration panel widget for extraction settings.

Example:
    ```python
    from legal_extractor_tui.widgets.config_panel import ConfigPanel
    from legal_extractor_tui.messages.extractor_messages import ConfigChanged

    config = ConfigPanel()

    @on(ConfigChanged)
    def handle_config_changed(self, event: ConfigChanged) -> None:
        print(f"Config updated: {event.config}")
    ```
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Checkbox, Input, Label, RadioButton, RadioSet, Static

from legal_extractor_tui.messages.extractor_messages import ConfigChanged


class ConfigPanel(Vertical):
    """Widget for configuring extraction options.

    Provides controls for:
    - Section analysis (requires API key)
    - Custom blacklist terms
    - Output format selection
    - Aggressive cleaning mode
    """

    # CSS moved to widgets.tcss for centralized theme management

    config: reactive[dict] = reactive({})

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize configuration panel."""
        super().__init__(name=name, id=id, classes=classes)
        self.config = {
            "enable_section_analysis": False,
            "custom_blacklist": "",
            "output_format": "text",
            "aggressive_cleaning": False,
        }

    def compose(self) -> ComposeResult:
        """Compose configuration panel layout."""
        yield Label("Extraction Configuration", classes="config-title")

        # Section Analysis
        with Vertical(classes="config-section"):
            yield Label("Section Analysis", classes="section-label")
            yield Label(
                "Detect and separate document sections using AI (requires API key)",
                classes="section-description"
            )
            yield Checkbox(
                "Enable section analysis",
                id="enable-section-analysis",
                value=self.config["enable_section_analysis"]
            )

        # Custom Blacklist
        with Vertical(classes="config-section"):
            yield Label("Custom Blacklist", classes="section-label")
            yield Label(
                "Additional terms to remove (comma-separated)",
                classes="section-description"
            )
            yield Input(
                placeholder="e.g., CONFIDENTIAL, DRAFT, INTERNAL",
                id="custom-blacklist",
                value=self.config["custom_blacklist"]
            )

        # Output Format
        with Vertical(classes="config-section"):
            yield Label("Output Format", classes="section-label")
            yield Label(
                "Choose preferred format for exported results",
                classes="section-description"
            )
            with RadioSet(id="output-format"):
                yield RadioButton(
                    "Plain Text (.txt)",
                    id="format-text",
                    value=self.config["output_format"] == "text"
                )
                yield RadioButton(
                    "Markdown (.md)",
                    id="format-markdown",
                    value=self.config["output_format"] == "markdown"
                )
                yield RadioButton(
                    "JSON (.json)",
                    id="format-json",
                    value=self.config["output_format"] == "json"
                )

        # Aggressive Cleaning
        with Vertical(classes="config-section"):
            yield Label("Cleaning Mode", classes="section-label")
            yield Label(
                "More aggressive pattern matching (may remove valid content)",
                classes="section-description"
            )
            yield Checkbox(
                "Enable aggressive cleaning",
                id="aggressive-cleaning",
                value=self.config["aggressive_cleaning"]
            )

        # Warning for section analysis
        if self.config["enable_section_analysis"]:
            yield Label(
                "Note: Section analysis requires API key to be configured in settings",
                classes="warning",
                id="api-warning"
            )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes.

        Args:
            event: Checkbox change event
        """
        checkbox_id = event.checkbox.id

        if checkbox_id == "enable-section-analysis":
            self.config["enable_section_analysis"] = event.value
            self._update_api_warning()

        elif checkbox_id == "aggressive-cleaning":
            self.config["aggressive_cleaning"] = event.value

        # Emit config changed message
        self.post_message(ConfigChanged(self.config.copy()))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input field changes.

        Args:
            event: Input change event
        """
        if event.input.id == "custom-blacklist":
            self.config["custom_blacklist"] = event.value
            # Emit config changed message
            self.post_message(ConfigChanged(self.config.copy()))

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio button selection.

        Args:
            event: RadioSet change event
        """
        if event.radio_set.id == "output-format":
            pressed_id = event.pressed.id

            if pressed_id == "format-text":
                self.config["output_format"] = "text"
            elif pressed_id == "format-markdown":
                self.config["output_format"] = "markdown"
            elif pressed_id == "format-json":
                self.config["output_format"] = "json"

            # Emit config changed message
            self.post_message(ConfigChanged(self.config.copy()))

    def _update_api_warning(self) -> None:
        """Show/hide API key warning based on section analysis setting."""
        if not self.is_mounted:
            return

        # Remove existing warning
        try:
            warning = self.query_one("#api-warning", Label)
            warning.remove()
        except Exception:
            pass

        # Add warning if section analysis enabled
        if self.config["enable_section_analysis"]:
            self.mount(
                Label(
                    "Note: Section analysis requires API key to be configured in settings",
                    classes="warning",
                    id="api-warning"
                )
            )

    def get_config(self) -> dict:
        """Get current configuration.

        Returns:
            Configuration dictionary
        """
        return self.config.copy()

    def set_config(self, config: dict) -> None:
        """Set configuration programmatically.

        Args:
            config: Configuration dictionary to apply
        """
        self.config.update(config)

        if not self.is_mounted:
            return

        # Update UI elements
        if "enable_section_analysis" in config:
            checkbox = self.query_one("#enable-section-analysis", Checkbox)
            checkbox.value = config["enable_section_analysis"]
            self._update_api_warning()

        if "custom_blacklist" in config:
            input_field = self.query_one("#custom-blacklist", Input)
            input_field.value = config["custom_blacklist"]

        if "output_format" in config:
            format_map = {
                "text": "format-text",
                "markdown": "format-markdown",
                "json": "format-json",
            }
            radio_id = format_map.get(config["output_format"])
            if radio_id:
                try:
                    radio_button = self.query_one(f"#{radio_id}", RadioButton)
                    radio_button.value = True
                except Exception:
                    pass

        if "aggressive_cleaning" in config:
            checkbox = self.query_one("#aggressive-cleaning", Checkbox)
            checkbox.value = config["aggressive_cleaning"]

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        default_config = {
            "enable_section_analysis": False,
            "custom_blacklist": "",
            "output_format": "text",
            "aggressive_cleaning": False,
        }
        self.set_config(default_config)
        self.post_message(ConfigChanged(default_config.copy()))

    def get_blacklist_terms(self) -> list[str]:
        """Get custom blacklist terms as list.

        Returns:
            List of blacklist terms (empty list if none)
        """
        blacklist_str = self.config["custom_blacklist"].strip()
        if not blacklist_str:
            return []

        # Split by comma and clean up
        terms = [term.strip() for term in blacklist_str.split(",")]
        return [term for term in terms if term]

    def check_config_validity(self) -> tuple[bool, str]:
        """Check if current configuration is valid.

        Note: This method was renamed from validate_config() to avoid
        conflict with Textual's reactive validator pattern (validate_<varname>).

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if section analysis enabled without API key
        # (In real implementation, would check actual API key presence)
        if self.config["enable_section_analysis"]:
            # This would need to check actual API key configuration
            pass

        # Validate blacklist terms format
        blacklist_terms = self.get_blacklist_terms()
        for term in blacklist_terms:
            if len(term) < 2:
                return False, f"Blacklist term too short: '{term}'"

        return True, ""

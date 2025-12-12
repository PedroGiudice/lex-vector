"""Results panel widget for displaying extraction results.

Example:
    ```python
    from legal_extractor_tui.widgets.results_panel import ResultsPanel
    from legal_extractor_tui.messages.extractor_messages import ExtractionCompleted

    results = ResultsPanel()

    @on(ExtractionCompleted)
    def handle_completed(self, event: ExtractionCompleted) -> None:
        results.set_result(event.result)
    ```
"""

import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Button, Label, Static, TabbedContent, TabPane

from legal_extractor_tui.messages.extractor_messages import (
    ExportRequested,
    ExtractionCompleted,
)


class ResultsPanel(Vertical):
    """Widget for displaying extraction results.

    Shows tabbed view with:
    - Metadata: System detection, stats, confidence
    - Sections: List of detected sections (if analyzed)

    Also provides preview button (opens modal) and export buttons for TXT, MD, JSON formats.
    """

    # CSS moved to widgets.tcss for centralized theme management

    has_result: reactive[bool] = reactive(False)
    result_data: reactive[dict] = reactive({})

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize results panel."""
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        """Compose results panel layout."""
        with Horizontal(classes="results-header"):
            yield Label("Extraction Results", classes="results-title")
            with Horizontal(classes="export-buttons"):
                yield Button("👁 Preview", id="preview-btn", variant="default")
                yield Button("Export TXT", id="export-txt", variant="primary")
                yield Button("Export MD", id="export-md", variant="default")
                yield Button("Export JSON", id="export-json", variant="default")

        with TabbedContent(id="results-tabs"):
            with TabPane("Metadata", id="tab-metadata"):
                yield self._create_metadata_pane()

            with TabPane("Sections", id="tab-sections"):
                yield self._create_sections_pane()

    def _create_metadata_pane(self) -> VerticalScroll:
        """Create metadata tab content."""
        container = VerticalScroll(classes="metadata-container", id="metadata-container")

        if self.has_result:
            # Worker returns flat structure, not nested metadata
            # Add metadata rows
            rows_data = [
                ("System Detected", self.result_data.get("system_name", "N/A")),
                ("System Code", self.result_data.get("system", "N/A")),
                ("Confidence", f"{self.result_data.get('confidence', 0):.1%}"),
                ("Original Length", f"{self.result_data.get('original_length', 0):,} chars"),
                ("Final Length", f"{self.result_data.get('final_length', 0):,} chars"),
                ("Reduction", f"{self.result_data.get('reduction_pct', 0):.1%}"),
                ("Patterns Removed", f"{self.result_data.get('patterns_removed', 0):,}"),
            ]

            for label_text, value_text in rows_data:
                row = Horizontal(classes="metadata-row")
                row.compose_add_child(Label(label_text + ":", classes="metadata-label"))
                row.compose_add_child(Label(str(value_text), classes="metadata-value"))
                container.compose_add_child(row)
        else:
            container.compose_add_child(
                Static(
                    "No metadata available. Process a PDF file first.",
                    classes="empty-message"
                )
            )

        return container

    def _create_sections_pane(self) -> VerticalScroll:
        """Create sections tab content."""
        container = VerticalScroll(classes="sections-container", id="sections-container")

        if self.has_result and "sections" in self.result_data:
            sections = self.result_data["sections"]

            if sections:
                for idx, section in enumerate(sections, 1):
                    section_widget = Vertical(classes="section-item")
                    section_widget.compose_add_child(
                        Label(f"Section {idx}: {section.get('title', 'Untitled')}", classes="section-title")
                    )

                    preview = section.get("content", "")[:200]
                    if len(section.get("content", "")) > 200:
                        preview += "..."

                    section_widget.compose_add_child(
                        Label(preview, classes="section-preview")
                    )

                    container.compose_add_child(section_widget)
            else:
                container.compose_add_child(
                    Static(
                        "No sections detected. Enable section analysis to extract sections.",
                        classes="empty-message"
                    )
                )
        else:
            container.compose_add_child(
                Static(
                    "No sections available. Process a PDF with section analysis enabled.",
                    classes="empty-message"
                )
            )

        return container

    def on_extraction_completed(self, event: ExtractionCompleted) -> None:
        """Handle extraction completion and update results.

        Args:
            event: ExtractionCompleted message
        """
        self.set_result(event.result)

    def set_result(self, result: dict) -> None:
        """Set extraction result and update display.

        Args:
            result: Result dictionary with text, metadata, sections
        """
        self.result_data = result
        self.has_result = True

        # Update metadata pane
        self._update_metadata_pane()

        # Update sections pane
        self._update_sections_pane()

    def _update_metadata_pane(self) -> None:
        """Update metadata tab with new data."""
        if not self.is_mounted:
            return

        try:
            metadata_widget = self.query_one("#metadata-container", VerticalScroll)

            # Clear existing children and rebuild
            metadata_widget.remove_children()

            if self.has_result:
                # Worker returns flat structure, not nested metadata
                # Add metadata rows
                rows_data = [
                    ("System Detected", self.result_data.get("system_name", "N/A")),
                    ("System Code", self.result_data.get("system", "N/A")),
                    ("Confidence", f"{self.result_data.get('confidence', 0):.1%}"),
                    ("Original Length", f"{self.result_data.get('original_length', 0):,} chars"),
                    ("Final Length", f"{self.result_data.get('final_length', 0):,} chars"),
                    ("Reduction", f"{self.result_data.get('reduction_pct', 0):.1%}"),
                    ("Patterns Removed", f"{self.result_data.get('patterns_removed', 0):,}"),
                ]

                for label_text, value_text in rows_data:
                    row = Horizontal(classes="metadata-row")
                    row.compose_add_child(Label(label_text + ":", classes="metadata-label"))
                    row.compose_add_child(Label(str(value_text), classes="metadata-value"))
                    metadata_widget.mount(row)
            else:
                metadata_widget.mount(
                    Static(
                        "No metadata available. Process a PDF file first.",
                        classes="empty-message"
                    )
                )
        except Exception:
            # Widget doesn't exist yet, ignore
            pass

    def _update_sections_pane(self) -> None:
        """Update sections tab with new data."""
        if not self.is_mounted:
            return

        try:
            sections_widget = self.query_one("#sections-container", VerticalScroll)

            # Clear existing children and rebuild
            sections_widget.remove_children()

            if self.has_result and "sections" in self.result_data:
                sections = self.result_data["sections"]

                if sections:
                    for idx, section in enumerate(sections, 1):
                        section_widget = Vertical(classes="section-item")
                        section_widget.compose_add_child(
                            Label(f"Section {idx}: {section.get('title', 'Untitled')}", classes="section-title")
                        )

                        preview = section.get("content", "")[:200]
                        if len(section.get("content", "")) > 200:
                            preview += "..."

                        section_widget.compose_add_child(
                            Label(preview, classes="section-preview")
                        )

                        sections_widget.mount(section_widget)
                else:
                    sections_widget.mount(
                        Static(
                            "No sections detected. Enable section analysis to extract sections.",
                            classes="empty-message"
                        )
                    )
            else:
                sections_widget.mount(
                    Static(
                        "No sections available. Process a PDF with section analysis enabled.",
                        classes="empty-message"
                    )
                )
        except Exception:
            # Widget doesn't exist yet, ignore
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle export button clicks.

        Args:
            event: Button press event
        """
        if not self.has_result:
            self.log.warning("No result to export")
            return

        button_id = event.button.id

        if button_id == "export-txt":
            self.post_message(ExportRequested("txt"))
        elif button_id == "export-md":
            self.post_message(ExportRequested("md"))
        elif button_id == "export-json":
            self.post_message(ExportRequested("json"))

    def get_export_data(self, format: str) -> str:
        """Get result data in specified format.

        Args:
            format: Export format (txt, md, json)

        Returns:
            Formatted string data
        """
        if not self.has_result:
            return ""

        if format == "txt":
            return self.result_data.get("text", "")

        elif format == "md":
            md_content = "# Legal Text Extraction Result\n\n"

            # Metadata section (flat structure from worker)
            md_content += "## Metadata\n\n"
            md_content += f"- **System**: {self.result_data.get('system_name', 'N/A')}\n"
            md_content += f"- **System Code**: {self.result_data.get('system', 'N/A')}\n"
            md_content += f"- **Confidence**: {self.result_data.get('confidence', 0):.1%}\n"
            md_content += f"- **Original Length**: {self.result_data.get('original_length', 0):,} chars\n"
            md_content += f"- **Final Length**: {self.result_data.get('final_length', 0):,} chars\n"
            md_content += f"- **Reduction**: {self.result_data.get('reduction_pct', 0):.1%}\n\n"

            # Text section
            md_content += "## Extracted Text\n\n"
            md_content += self.result_data.get("text", "")

            # Sections
            if "sections" in self.result_data and self.result_data["sections"]:
                md_content += "\n\n## Detected Sections\n\n"
                for idx, section in enumerate(self.result_data["sections"], 1):
                    md_content += f"### {idx}. {section.get('title', 'Untitled')}\n\n"
                    md_content += section.get("content", "") + "\n\n"

            return md_content

        elif format == "json":
            return json.dumps(self.result_data, indent=2, ensure_ascii=False)

        return ""

    def clear_results(self) -> None:
        """Clear all results and reset to empty state."""
        self.result_data = {}
        self.has_result = False

        self._update_metadata_pane()
        self._update_sections_pane()

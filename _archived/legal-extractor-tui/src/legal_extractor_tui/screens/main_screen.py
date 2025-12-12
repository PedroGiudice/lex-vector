"""Main application screen for Legal Extractor TUI.

This module provides the primary screen containing all widgets for PDF
extraction operations, progress tracking, and result visualization.
"""

from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, Container
from textual.screen import Screen
from textual.widgets import Button, Footer

from legal_extractor_tui.config import OUTPUT_FORMATS
from legal_extractor_tui.messages import (
    ConfigChanged,
    ExportRequested,
    ExtractionCancelled,
    ExtractionCompleted,
    ExtractionError,
    ExtractionProgress,
    ExtractionStarted,
    FileSelected,
    LogLevel,
    LogMessage,
    StatusUpdate,
    SystemChanged,
)
from legal_extractor_tui.screens.file_browser_screen import FileBrowserScreen
from legal_extractor_tui.widgets import (
    ConfigPanel,
    ExtractionProgress as ExtractionProgressWidget,
    FileSelector,
    Header,
    LogPanel,
    ResultsPanel,
    StatusBar,
    SystemSelector,
)
from legal_extractor_tui.workers import ExtractionWorker


class MainScreen(Screen):
    """Main application screen with full Legal Extractor UI.

    Layout:
        ┌─────────────────────────────────────────────────────────┐
        │ HEADER: Logo + Title + Status                           │
        ├─────────────┬───────────────────────────────────────────┤
        │ LEFT PANEL  │  CENTER AREA                              │
        │             │                                           │
        │ FileSelector│  ┌─────────────────────────────────────┐  │
        │             │  │ ExtractionProgress                  │  │
        │ SystemSelect│  │ (shows when processing)             │  │
        │             │  └─────────────────────────────────────┘  │
        │ ConfigPanel │                                           │
        │             │  ┌─────────────────────────────────────┐  │
        │             │  │ ResultsPanel                        │  │
        │             │  │ (tabs: Metadata|Sections)           │  │
        │             │  │                                     │  │
        │             │  │                                     │  │
        │             │  └─────────────────────────────────────┘  │
        ├─────────────┴───────────────────────────────────────────┤
        │ FOOTER: Status Bar + Keybindings                        │
        └─────────────────────────────────────────────────────────┘

    Keybindings:
        - ctrl+r: Run extraction on selected file
        - escape: Cancel running extraction
        - ctrl+o: Focus file selector
        - ctrl+s: Save/export results
        - ctrl+p: Show full text preview in modal
        - ?: Show help screen

    Attributes:
        extraction_worker: Background worker for PDF processing
        selected_file: Currently selected PDF file path
        current_system: Selected judicial system code
        current_config: Extraction configuration settings
        extraction_result: Most recent extraction result
    """

    BINDINGS = [
        Binding("ctrl+r", "run_extraction", "Extrair", show=True),
        Binding("escape", "cancel_extraction", "Cancelar", show=True),
        Binding("ctrl+o", "open_file", "Abrir", show=True),
        Binding("ctrl+s", "save_result", "Salvar", show=True),
        Binding("ctrl+p", "show_preview", "Preview", show=True),
        Binding("?", "show_help", "Ajuda", show=True),
    ]

    def __init__(self, initial_file: Path | None = None) -> None:
        """Initialize main screen.

        Args:
            initial_file: Optional PDF file to load on startup
        """
        super().__init__()
        self.extraction_worker: ExtractionWorker | None = None
        self.selected_file: Path | None = initial_file
        self.current_system: str = "auto"
        self.current_config: dict[str, Any] = {
            "separate_sections": False,
            "output_format": "text",
        }
        self.extraction_result: dict | None = None

    def compose(self) -> ComposeResult:
        """Compose the screen layout.

        Yields:
            Textual widgets in layout order
        """
        # Header with logo and title
        yield Header(title="Legal Extractor TUI")

        # Main container with sidebar and content area
        with Horizontal(id="main-container"):
            # Left sidebar panel (30% width)
            with Vertical(id="sidebar-panel"):
                yield FileSelector(
                    id="file-selector",
                    initial_path=str(self.selected_file) if self.selected_file else ""
                )
                yield SystemSelector(id="system-selector")
                yield ConfigPanel(id="config-panel")

                # Action buttons - minimal modern style
                with Horizontal(id="action-buttons"):
                    yield Button("● RUN", id="extract-btn", variant="success")
                    yield Button("↓ SAVE", id="save-btn", variant="primary")
                    yield Button("× CLEAR", id="clear-btn", variant="error")

            # Right content area (70% width)
            with Vertical(id="content-area"):
                # Progress panel (collapsible, hidden initially)
                yield ExtractionProgressWidget(id="extraction-progress")

                # Results panel (main area)
                yield ResultsPanel(id="results-panel")

                # Log panel (bottom, collapsible)
                yield LogPanel(id="log-panel")

        # Status bar and footer
        yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen after mounting."""
        # Hide progress panel initially
        progress = self.query_one("#extraction-progress", ExtractionProgressWidget)
        progress.add_class("hidden")

        # Log startup
        self.add_log("Application started", LogLevel.INFO)
        self.update_status("Ready - Select a PDF file to extract")

        # If initial file was provided, trigger file selection
        if self.selected_file:
            self.add_log(f"Loaded initial file: {self.selected_file.name}", LogLevel.INFO)
            self.update_status(f"File selected: {self.selected_file.name}")

    # Actions

    def action_run_extraction(self) -> None:
        """Start PDF extraction with current settings.

        Validates that a file is selected, then creates and runs an
        ExtractionWorker in the background.
        """
        # Validate file selection
        if not self.selected_file:
            self.add_log("No file selected", LogLevel.WARNING)
            self.update_status("Error: No file selected")
            return

        if not self.selected_file.exists():
            self.add_log(f"File not found: {self.selected_file}", LogLevel.ERROR)
            self.update_status("Error: File not found")
            return

        # Check if already running
        if self.extraction_worker and not self.extraction_worker.is_cancelled:
            self.add_log("Extraction already running", LogLevel.WARNING)
            return

        # Create and run worker
        self.add_log(f"Starting extraction: {self.selected_file.name}", LogLevel.INFO)
        self.update_status("Starting extraction...")

        self.extraction_worker = ExtractionWorker(self.app)

        # Start extraction in background using Textual worker pattern
        self.run_worker(
            self.extraction_worker.run(
                pdf_path=self.selected_file,
                system=self.current_system,
                separate_sections=self.current_config.get("separate_sections", False),
                output_format=self.current_config.get("output_format", "text"),
            ),
            exclusive=True,
            name="extraction",
        )

    def action_cancel_extraction(self) -> None:
        """Cancel running extraction operation."""
        if self.extraction_worker and not self.extraction_worker.is_cancelled:
            self.extraction_worker.cancel()
            self.add_log("Cancelling extraction...", LogLevel.WARNING)
            self.update_status("Cancelling...")
        else:
            self.add_log("No extraction to cancel", LogLevel.DEBUG)

    def action_open_file(self) -> None:
        """Focus the file selector for file browsing."""
        file_selector = self.query_one("#file-selector", FileSelector)
        file_selector.focus()
        self.update_status("Browse and select a PDF file")

    def action_save_result(self) -> None:
        """Export current extraction results.

        Prompts for export format and destination, then saves results
        to the specified file.
        """
        if not self.extraction_result:
            self.add_log("No results to export", LogLevel.WARNING)
            self.update_status("Error: No results to export")
            return

        # Get export format from config
        export_format = self.current_config.get("output_format", "text")

        # Build default filename
        if self.selected_file:
            base_name = self.selected_file.stem
            extension = OUTPUT_FORMATS[export_format][1]
            default_dest = self.selected_file.parent / f"{base_name}_extracted{extension}"
        else:
            default_dest = Path.cwd() / f"extracted{OUTPUT_FORMATS[export_format][1]}"

        # Post export request (will be handled by save dialog or direct export)
        self.post_message(
            ExportRequested(
                format=export_format,
                destination=default_dest,
            )
        )

    def action_show_help(self) -> None:
        """Show help screen."""
        from legal_extractor_tui.screens.help_screen import HelpScreen

        self.app.push_screen(HelpScreen())

    def action_show_preview(self) -> None:
        """Show full text preview in modal."""
        # Verificar se tem resultado
        results_panel = self.query_one("#results-panel", ResultsPanel)
        if not results_panel.has_result:
            self.add_log("No results to preview", LogLevel.WARNING)
            return

        # Obter texto do resultado
        text = results_panel.result_data.get("text", "") if results_panel.result_data else ""

        from legal_extractor_tui.screens.preview_modal_screen import PreviewModalScreen
        self.app.push_screen(PreviewModalScreen(text=text))

    def action_clear_selection(self) -> None:
        """Clear file selection and results."""
        # Clear file selector
        file_selector = self.query_one("#file-selector", FileSelector)
        file_selector.clear_selection()
        self.selected_file = None

        # Clear results
        self.extraction_result = None
        results_panel = self.query_one("#results-panel", ResultsPanel)
        results_panel.clear_results()

        self.add_log("Selection cleared", LogLevel.INFO)
        self.update_status("Ready - Select a PDF file")

    # Message Handlers - Action Buttons

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle action button clicks.

        Args:
            event: Button.Pressed event with button reference
        """
        if event.button.id == "extract-btn":
            self.action_run_extraction()
        elif event.button.id == "save-btn":
            self.action_save_result()
        elif event.button.id == "clear-btn":
            self.action_clear_selection()
        elif event.button.id == "preview-btn":
            self.action_show_preview()

    # Message Handlers - File Selection

    @on(FileSelector.BrowseRequested)
    def on_browse_requested(self, event: FileSelector.BrowseRequested) -> None:
        """Handle browse button click from FileSelector.

        Opens a modal file browser for selecting PDF files.

        Args:
            event: BrowseRequested message
        """
        # Stop event propagation
        event.stop()

        # Determine initial path for browser
        if self.selected_file and self.selected_file.parent.exists():
            initial_path = self.selected_file.parent
        else:
            initial_path = Path.cwd()

        # Show file browser modal
        self.app.push_screen(
            FileBrowserScreen(initial_path=initial_path),
            callback=self._handle_file_browser_result
        )

    def _handle_file_browser_result(self, selected_path: Path | None) -> None:
        """Handle result from file browser modal.

        Args:
            selected_path: Path to selected PDF file, or None if cancelled
        """
        if selected_path:
            # Update FileSelector with selected path
            file_selector = self.query_one("#file-selector", FileSelector)
            file_selector.set_path(selected_path)

            # Log the selection
            self.add_log(f"File browsed and selected: {selected_path.name}", LogLevel.INFO)

    @on(FileSelected)
    def on_file_selected(self, event: FileSelected) -> None:
        """Handle file selection from FileSelector.

        Args:
            event: FileSelected message with path
        """
        self.selected_file = event.path
        self.add_log(f"File selected: {event.path.name}", LogLevel.INFO)
        self.update_status(f"Selected: {event.path.name}")

        # Clear previous results
        self.extraction_result = None
        results_panel = self.query_one("#results-panel", ResultsPanel)
        results_panel.clear_results()

    @on(SystemChanged)
    def on_system_changed(self, event: SystemChanged) -> None:
        """Handle judicial system selection change.

        Args:
            event: SystemChanged message with system code
        """
        self.current_system = event.system
        self.add_log(f"System changed: {event.system}", LogLevel.DEBUG)

    @on(ConfigChanged)
    def on_config_changed(self, event: ConfigChanged) -> None:
        """Handle configuration changes.

        Args:
            event: ConfigChanged message with config dict
        """
        self.current_config.update(event.config)
        self.add_log(f"Config updated: {event.config}", LogLevel.DEBUG)

    # Message Handlers - Extraction Lifecycle

    @on(ExtractionStarted)
    def on_extraction_started(self, event: ExtractionStarted) -> None:
        """Handle extraction started event.

        Args:
            event: ExtractionStarted message
        """
        # Show progress panel
        progress = self.query_one("#extraction-progress", ExtractionProgressWidget)
        progress.remove_class("hidden")
        progress.reset()

        self.add_log(
            f"Extraction started: {event.file_path.name} (system: {event.system})",
            LogLevel.INFO,
        )
        self.update_status(f"Extracting: {event.file_path.name}")

    @on(ExtractionProgress)
    def on_extraction_progress(self, event: ExtractionProgress) -> None:
        """Handle extraction progress updates.

        Args:
            event: ExtractionProgress message
        """
        # Update progress widget
        progress = self.query_one("#extraction-progress", ExtractionProgressWidget)
        progress.update_progress(
            stage=event.stage,
            progress=event.progress,
            message=event.message,
        )

        # Log progress with details if available
        if event.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in event.details.items())
            self.add_log(f"{event.message} ({detail_str})", LogLevel.DEBUG)
        else:
            self.add_log(event.message, LogLevel.DEBUG)

        self.update_status(event.message)

    @on(ExtractionCompleted)
    def on_extraction_completed(self, event: ExtractionCompleted) -> None:
        """Handle extraction completion.

        Args:
            event: ExtractionCompleted message with results
        """
        # Hide progress panel
        progress = self.query_one("#extraction-progress", ExtractionProgressWidget)
        progress.add_class("hidden")

        # Store results
        self.extraction_result = event.result

        # Update results panel
        results_panel = self.query_one("#results-panel", ResultsPanel)
        results_panel.set_result(event.result)

        # Log completion
        char_count = event.result.get("final_length", 0)
        self.add_log(
            f"Extraction completed in {event.elapsed_time:.2f}s ({char_count:,} chars)",
            LogLevel.SUCCESS,
        )
        self.update_status(
            f"Completed: {char_count:,} chars ({event.elapsed_time:.1f}s)"
        )

    @on(ExtractionError)
    def on_extraction_error(self, event: ExtractionError) -> None:
        """Handle extraction error.

        Args:
            event: ExtractionError message
        """
        # Hide progress panel
        progress = self.query_one("#extraction-progress", ExtractionProgressWidget)
        progress.add_class("hidden")

        # Log error
        self.add_log(
            f"Extraction failed at {event.stage}: {event.message}",
            LogLevel.ERROR,
        )
        self.update_status(f"Error: {event.message}")

    @on(ExtractionCancelled)
    def on_extraction_cancelled(self, event: ExtractionCancelled) -> None:
        """Handle extraction cancellation.

        Args:
            event: ExtractionCancelled message
        """
        # Hide progress panel
        progress = self.query_one("#extraction-progress", ExtractionProgressWidget)
        progress.add_class("hidden")

        self.add_log(
            f"Extraction cancelled at {event.stage}",
            LogLevel.WARNING,
        )
        self.update_status("Extraction cancelled")

    @on(ExportRequested)
    def on_export_requested(self, event: ExportRequested) -> None:
        """Handle export request.

        Args:
            event: ExportRequested message
        """
        if not self.extraction_result:
            self.add_log("No results to export", LogLevel.WARNING)
            return

        try:
            # Get result text
            text = self.extraction_result.get("text", "")

            # Format based on export format
            if event.format == "markdown":
                content = self._format_as_markdown(self.extraction_result)
            elif event.format == "json":
                import json
                content = json.dumps(self.extraction_result, indent=2, ensure_ascii=False)
            else:  # text
                content = text

            # Write to file
            if event.destination:
                event.destination.write_text(content, encoding="utf-8")
                self.add_log(
                    f"Exported to {event.destination.name} ({event.format})",
                    LogLevel.SUCCESS,
                )
                self.update_status(f"Saved: {event.destination.name}")
            else:
                self.add_log("Export cancelled - no destination", LogLevel.WARNING)

        except Exception as e:
            self.add_log(f"Export failed: {e}", LogLevel.ERROR)
            self.update_status(f"Export error: {e}")

    # Helper Methods

    def add_log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Post log message to log panel.

        Args:
            message: Log message text
            level: Log severity level
        """
        self.post_message(LogMessage(message=message, level=level))

    def update_status(self, text: str) -> None:
        """Update status bar text.

        Args:
            text: Status text to display
        """
        self.post_message(StatusUpdate(status=text))

    def _format_as_markdown(self, result: dict) -> str:
        """Format extraction result as Markdown.

        Args:
            result: Extraction result dictionary

        Returns:
            Markdown-formatted string
        """
        lines = []

        # Header
        lines.append("# Documento Jurídico Extraído")
        lines.append("")

        # Metadata
        lines.append("## Metadados")
        lines.append("")
        lines.append(f"- **Sistema:** {result.get('system_name', 'Desconhecido')}")
        lines.append(f"- **Confiança:** {result.get('confidence', 0)}%")
        lines.append(f"- **Tamanho original:** {result.get('original_length', 0):,} caracteres")
        lines.append(f"- **Tamanho final:** {result.get('final_length', 0):,} caracteres")
        lines.append(f"- **Redução:** {result.get('reduction_pct', 0):.1f}%")
        lines.append("")

        # Text content
        lines.append("## Conteúdo")
        lines.append("")
        lines.append(result.get("text", ""))
        lines.append("")

        # Sections (if available)
        sections = result.get("sections", [])
        if len(sections) > 1:  # More than just the single full document section
            lines.append("## Seções Identificadas")
            lines.append("")
            for i, section in enumerate(sections, 1):
                section_type = section.get("type", "unknown")
                confidence = section.get("confidence", 0)
                lines.append(f"### {i}. {section_type} (confiança: {confidence:.0%})")
                lines.append("")
                lines.append(section.get("content", ""))
                lines.append("")

        return "\n".join(lines)

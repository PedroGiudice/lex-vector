"""Extraction progress widget for tracking PDF processing stages.

Example:
    ```python
    from legal_extractor_tui.widgets.extraction_progress import ExtractionProgress
    from legal_extractor_tui.messages.extractor_messages import ExtractionProgress as ProgressMsg

    progress = ExtractionProgress()

    # Listen to progress updates
    @on(ProgressMsg)
    def handle_progress(self, event: ProgressMsg) -> None:
        # Progress widget will handle this automatically
        pass
    ```
"""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Label, ProgressBar, Static

from legal_extractor_tui.messages.extractor_messages import (
    ExtractionCompleted,
    ExtractionError,
    ExtractionProgress as ExtractionProgressMsg,
    ExtractionStarted,
)
from legal_extractor_tui.widgets.spinner_widget import SpinnerWidget


class StageIndicator(Static):
    """Individual stage indicator with progress bar and status."""

    # CSS moved to widgets.tcss for centralized theme management

    stage_name: reactive[str] = reactive("")
    stage_status: reactive[str] = reactive("Pending")
    stage_progress: reactive[float] = reactive(0.0)
    stage_message: reactive[str] = reactive("")

    def __init__(
        self,
        name: str,
        *,
        widget_name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize stage indicator.

        Args:
            name: Display name of the stage
            widget_name: Widget name
            id: Widget ID
            classes: CSS classes
        """
        super().__init__(name=widget_name, id=id, classes=classes)
        self.stage_name = name
        self.add_class("pending")

    def compose(self) -> ComposeResult:
        """Compose stage indicator layout."""
        with Horizontal(classes="stage-header"):
            yield SpinnerWidget(
                spinner_name="pulse_bar",
                source="custom",
                style="cyan",
                id="stage-spinner"
            )
            yield Label(self.stage_name, classes="stage-name", id="stage-name")
            yield Label(self.stage_status, classes="stage-status", id="stage-status")

        yield ProgressBar(
            total=100,
            show_eta=False,
            id="stage-progress"
        )

        yield Label(self.stage_message, classes="stage-message", id="stage-message")

    def on_mount(self) -> None:
        """Initialize spinner state when mounted."""
        # Pause spinner initially (pending state)
        try:
            spinner = self.query_one("#stage-spinner", SpinnerWidget)
            spinner.pause()
            spinner.set_style("dim")
        except Exception:
            pass

    def set_active(self) -> None:
        """Mark stage as active/in-progress."""
        self.remove_class("pending", "completed", "error")
        self.add_class("active")
        self.stage_status = "In Progress"
        if self.is_mounted:
            # Resume spinner
            try:
                spinner = self.query_one("#stage-spinner", SpinnerWidget)
                spinner.resume()
                spinner.set_style("cyan")
            except Exception:
                pass

            status_label = self.query_one("#stage-status", Label)
            status_label.update(self.stage_status)

    def set_completed(self) -> None:
        """Mark stage as completed."""
        self.remove_class("pending", "active", "error")
        self.add_class("completed")
        self.stage_status = "Completed"
        self.stage_progress = 1.0
        if self.is_mounted:
            # Pause spinner and change to green
            try:
                spinner = self.query_one("#stage-spinner", SpinnerWidget)
                spinner.pause()
                spinner.set_style("green")
            except Exception:
                pass

            status_label = self.query_one("#stage-status", Label)
            status_label.update(self.stage_status)
            progress_bar = self.query_one("#stage-progress", ProgressBar)
            progress_bar.update(progress=100)

    def set_error(self, message: str = "") -> None:
        """Mark stage as error.

        Args:
            message: Error message to display
        """
        self.remove_class("pending", "active", "completed")
        self.add_class("error")
        self.stage_status = "Error"
        if message:
            self.stage_message = message
        if self.is_mounted:
            # Pause spinner and change to red
            try:
                spinner = self.query_one("#stage-spinner", SpinnerWidget)
                spinner.pause()
                spinner.set_style("red")
            except Exception:
                pass

            status_label = self.query_one("#stage-status", Label)
            status_label.update(self.stage_status)
            message_label = self.query_one("#stage-message", Label)
            message_label.update(self.stage_message)

    def update_progress(self, progress: float, message: str = "") -> None:
        """Update stage progress.

        Args:
            progress: Progress value 0.0-1.0
            message: Status message
        """
        self.stage_progress = max(0.0, min(1.0, progress))
        if message:
            self.stage_message = message

        if self.is_mounted:
            progress_bar = self.query_one("#stage-progress", ProgressBar)
            progress_bar.update(progress=int(self.stage_progress * 100))

            if message:
                message_label = self.query_one("#stage-message", Label)
                message_label.update(message)


class ExtractionProgress(Vertical):
    """Widget for tracking extraction pipeline progress.

    Shows 3 stages: Extracting -> Cleaning -> Analyzing
    Each stage has progress bar, spinner, and status.
    """

    # CSS moved to widgets.tcss for centralized theme management

    current_stage: reactive[str] = reactive("")
    overall_status: reactive[str] = reactive("Idle")
    stats: reactive[dict] = reactive({})

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize extraction progress widget."""
        super().__init__(name=name, id=id, classes=classes)
        self.stats = {
            "chars_removed": 0,
            "patterns_matched": 0,
            "sections_found": 0,
        }

    def compose(self) -> ComposeResult:
        """Compose extraction progress layout."""
        yield Label("Extraction Progress", classes="progress-title")

        with Vertical(classes="stages-container", id="stages-container"):
            yield StageIndicator("1. Extracting Text", id="stage-extracting")
            yield StageIndicator("2. Cleaning Text", id="stage-cleaning")
            yield StageIndicator("3. Analyzing Sections", id="stage-analyzing")

        with Vertical(classes="stats-panel", id="stats-panel"):
            with Horizontal(classes="stats-row"):
                yield Label("Characters Removed:", classes="stats-label")
                yield Label("0", classes="stats-value", id="stats-chars-removed")

            with Horizontal(classes="stats-row"):
                yield Label("Patterns Matched:", classes="stats-label")
                yield Label("0", classes="stats-value", id="stats-patterns-matched")

            with Horizontal(classes="stats-row"):
                yield Label("Sections Found:", classes="stats-label")
                yield Label("0", classes="stats-value", id="stats-sections-found")

        yield Label(
            "Ready to process",
            classes="overall-status idle",
            id="overall-status"
        )

    def on_extraction_started(self, event: ExtractionStarted) -> None:
        """Handle extraction start.

        Args:
            event: ExtractionStarted message
        """
        self.overall_status = "Processing"
        self.current_stage = "extracting"

        # Update overall status
        status_label = self.query_one("#overall-status", Label)
        status_label.remove_class("idle", "completed", "error")
        status_label.add_class("processing")
        status_label.update(f"Processing: {event.file_path.name}")

        # Activate first stage
        extracting_stage = self.query_one("#stage-extracting", StageIndicator)
        extracting_stage.set_active()

    def on_extraction_progress(self, event: ExtractionProgressMsg) -> None:
        """Handle extraction progress updates.

        Args:
            event: ExtractionProgress message
        """
        stage_id = f"stage-{event.stage}"

        try:
            stage = self.query_one(f"#{stage_id}", StageIndicator)
            stage.update_progress(event.progress, event.message)

            # Update stats if provided in details
            if event.details:
                self._update_stats(event.details)

        except Exception as e:
            self.log.warning(f"Stage {stage_id} not found: {e}")

    def on_extraction_completed(self, event: ExtractionCompleted) -> None:
        """Handle extraction completion.

        Args:
            event: ExtractionCompleted message
        """
        self.overall_status = "Completed"

        # Mark all stages as completed
        for stage_id in ["stage-extracting", "stage-cleaning", "stage-analyzing"]:
            try:
                stage = self.query_one(f"#{stage_id}", StageIndicator)
                stage.set_completed()
            except Exception:
                pass

        # Update overall status
        status_label = self.query_one("#overall-status", Label)
        status_label.remove_class("idle", "processing", "error")
        status_label.add_class("completed")
        status_label.update(f"Completed in {event.elapsed_time:.1f}s")

        # Update final stats from result
        if "metadata" in event.result:
            metadata = event.result["metadata"]
            self._update_stats({
                "chars_removed": metadata.get("chars_removed", 0),
                "patterns_matched": metadata.get("patterns_matched", 0),
                "sections_found": len(event.result.get("sections", [])),
            })

    def on_extraction_error(self, event: ExtractionError) -> None:
        """Handle extraction error.

        Args:
            event: ExtractionError message
        """
        self.overall_status = "Error"

        # Mark current stage as error
        if event.stage:
            stage_id = f"stage-{event.stage}"
            try:
                stage = self.query_one(f"#{stage_id}", StageIndicator)
                stage.set_error(event.message)
            except Exception:
                pass

        # Update overall status
        status_label = self.query_one("#overall-status", Label)
        status_label.remove_class("idle", "processing", "completed")
        status_label.add_class("error")
        status_label.update(f"Error: {event.message}")

    def _update_stats(self, stats_dict: dict) -> None:
        """Update statistics display.

        Args:
            stats_dict: Dictionary with stats to update
        """
        if "chars_removed" in stats_dict:
            self.stats["chars_removed"] = stats_dict["chars_removed"]
            label = self.query_one("#stats-chars-removed", Label)
            label.update(f"{stats_dict['chars_removed']:,}")

        if "patterns_matched" in stats_dict:
            self.stats["patterns_matched"] = stats_dict["patterns_matched"]
            label = self.query_one("#stats-patterns-matched", Label)
            label.update(f"{stats_dict['patterns_matched']:,}")

        if "sections_found" in stats_dict:
            self.stats["sections_found"] = stats_dict["sections_found"]
            label = self.query_one("#stats-sections-found", Label)
            label.update(str(stats_dict["sections_found"]))

    def reset(self) -> None:
        """Reset progress to initial state."""
        self.overall_status = "Idle"
        self.current_stage = ""
        self.stats = {
            "chars_removed": 0,
            "patterns_matched": 0,
            "sections_found": 0,
        }

        # Reset all stages
        for stage_id in ["stage-extracting", "stage-cleaning", "stage-analyzing"]:
            stage = self.query_one(f"#{stage_id}", StageIndicator)
            stage.remove_class("active", "completed", "error")
            stage.add_class("pending")
            stage.stage_status = "Pending"
            stage.stage_progress = 0.0
            stage.stage_message = ""

            # Reset spinner to paused/dim state
            try:
                spinner = stage.query_one("#stage-spinner", SpinnerWidget)
                spinner.pause()
                spinner.set_style("dim")
            except Exception:
                pass

        # Reset UI
        status_label = self.query_one("#overall-status", Label)
        status_label.remove_class("processing", "completed", "error")
        status_label.add_class("idle")
        status_label.update("Ready to process")

        self._update_stats(self.stats)

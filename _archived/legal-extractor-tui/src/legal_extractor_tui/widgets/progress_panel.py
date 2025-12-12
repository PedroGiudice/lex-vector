"""Multi-stage progress panel for pipeline execution tracking.

Example:
    ```python
    from legal_extractor_tui.widgets.progress_panel import PipelineProgress

    pipeline = PipelineProgress([
        "Download",
        "Extract",
        "Process",
        "Upload"
    ])

    pipeline.start_stage("Download")
    pipeline.update_stage("Download", 50)
    pipeline.complete_stage("Download")

    pipeline.start_stage("Extract")
    pipeline.error_stage("Extract", "Failed to parse file")
    ```
"""

from typing import Literal

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.widgets import Label, ProgressBar, Static

StageStatus = Literal["pending", "running", "completed", "error"]


class StageProgress(Container):
    """Single stage progress widget with label, progress bar and status icon.

    Attributes:
        status: Current status of the stage
        progress: Current progress percentage (0-100)
    """

    # CSS moved to widgets.tcss for centralized theme management

    status: reactive[StageStatus] = reactive("pending")
    progress: reactive[float] = reactive(0.0)

    def __init__(
        self,
        stage_name: str,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize stage progress widget.

        Args:
            stage_name: Name of the pipeline stage
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self.stage_name = stage_name
        self.add_class("pending")

    def compose(self) -> ComposeResult:
        """Compose the stage progress layout.

        Yields:
            Label, ProgressBar and status icon
        """
        yield Label(self.stage_name, classes="stage-label")
        yield ProgressBar(total=100, show_eta=False, id=f"progress-{self.stage_name}")
        yield Static(self._get_status_icon(), classes="stage-status", id=f"status-{self.stage_name}")

    def _get_status_icon(self) -> str:
        """Get status icon for current status.

        Returns:
            Icon string for current status
        """
        icons = {
            "pending": "⏸️",
            "running": "▶️",
            "completed": "✅",
            "error": "❌",
        }
        return icons.get(self.status, "⏸️")

    def watch_status(self, status: StageStatus) -> None:
        """React to status changes.

        Args:
            status: New status value
        """
        # Update CSS class
        for s in ["pending", "running", "completed", "error"]:
            self.remove_class(s)
        self.add_class(status)

        # Update status icon
        status_widget = self.query_one(f"#status-{self.stage_name}", Static)
        status_widget.update(self._get_status_icon())

    def watch_progress(self, progress: float) -> None:
        """React to progress changes.

        Args:
            progress: New progress value (0-100)
        """
        progress_bar = self.query_one(f"#progress-{self.stage_name}", ProgressBar)
        progress_bar.update(progress=progress)

    def set_status(self, status: StageStatus, progress: float | None = None) -> None:
        """Update stage status and optionally progress.

        Args:
            status: New status
            progress: Optional progress percentage
        """
        self.status = status
        if progress is not None:
            self.progress = progress


class PipelineProgress(Vertical):
    """Container for multiple stage progress widgets.

    Manages a multi-stage pipeline with progress tracking.
    """

    # CSS moved to widgets.tcss for centralized theme management

    def __init__(
        self,
        stages: list[str],
        title: str = "Pipeline Progress",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize pipeline progress widget.

        Args:
            stages: List of stage names
            title: Title to display above stages
            name: Name of the widget
            id: ID of the widget
            classes: CSS classes to apply
        """
        super().__init__(name=name, id=id, classes=classes)
        self.stages = stages
        self.title = title
        self._stage_widgets: dict[str, StageProgress] = {}

    def compose(self) -> ComposeResult:
        """Compose the pipeline layout.

        Yields:
            Title label and StageProgress widgets
        """
        yield Label(self.title, classes="pipeline-title")

        for stage_name in self.stages:
            stage_widget = StageProgress(stage_name, id=f"stage-{stage_name}")
            self._stage_widgets[stage_name] = stage_widget
            yield stage_widget

    def start_stage(self, stage_name: str) -> None:
        """Start a pipeline stage.

        Args:
            stage_name: Name of the stage to start

        Raises:
            KeyError: If stage_name is not in the pipeline
        """
        if stage_name not in self._stage_widgets:
            raise KeyError(f"Stage '{stage_name}' not found in pipeline")

        self._stage_widgets[stage_name].set_status("running", 0)

    def update_stage(self, stage_name: str, progress: float) -> None:
        """Update stage progress.

        Args:
            stage_name: Name of the stage to update
            progress: Progress percentage (0-100)

        Raises:
            KeyError: If stage_name is not in the pipeline
        """
        if stage_name not in self._stage_widgets:
            raise KeyError(f"Stage '{stage_name}' not found in pipeline")

        widget = self._stage_widgets[stage_name]
        widget.progress = min(100, max(0, progress))

    def complete_stage(self, stage_name: str) -> None:
        """Mark a stage as completed.

        Args:
            stage_name: Name of the stage to complete

        Raises:
            KeyError: If stage_name is not in the pipeline
        """
        if stage_name not in self._stage_widgets:
            raise KeyError(f"Stage '{stage_name}' not found in pipeline")

        self._stage_widgets[stage_name].set_status("completed", 100)

    def error_stage(self, stage_name: str, error_message: str = "") -> None:
        """Mark a stage as errored.

        Args:
            stage_name: Name of the stage that errored
            error_message: Optional error message (currently unused, reserved for future)

        Raises:
            KeyError: If stage_name is not in the pipeline
        """
        if stage_name not in self._stage_widgets:
            raise KeyError(f"Stage '{stage_name}' not found in pipeline")

        self._stage_widgets[stage_name].set_status("error")

    def reset(self) -> None:
        """Reset all stages to pending state with 0 progress."""
        for widget in self._stage_widgets.values():
            widget.set_status("pending", 0)

    def get_stage_status(self, stage_name: str) -> StageStatus:
        """Get current status of a stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Current stage status

        Raises:
            KeyError: If stage_name is not in the pipeline
        """
        if stage_name not in self._stage_widgets:
            raise KeyError(f"Stage '{stage_name}' not found in pipeline")

        return self._stage_widgets[stage_name].status

    def get_stage_progress(self, stage_name: str) -> float:
        """Get current progress of a stage.

        Args:
            stage_name: Name of the stage

        Returns:
            Current progress percentage (0-100)

        Raises:
            KeyError: If stage_name is not in the pipeline
        """
        if stage_name not in self._stage_widgets:
            raise KeyError(f"Stage '{stage_name}' not found in pipeline")

        return self._stage_widgets[stage_name].progress

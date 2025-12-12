"""Pipeline-related messages for TUI Template.

Messages emitted during pipeline execution lifecycle.
"""

from dataclasses import dataclass
from textual.message import Message


@dataclass
class PipelineStarted(Message):
    """Emitted when pipeline execution starts.

    Attributes:
        total_steps: Total number of steps in the pipeline
    """
    total_steps: int


@dataclass
class StepStarted(Message):
    """Emitted when a pipeline step begins execution.

    Attributes:
        step: Step index (0-based)
        name: Human-readable step name
    """
    step: int
    name: str


@dataclass
class StepProgress(Message):
    """Emitted to report progress within a step.

    Attributes:
        step: Step index (0-based)
        progress: Progress value (0.0 to 1.0)
        message: Optional progress message
    """
    step: int
    progress: float
    message: str | None = None


@dataclass
class StepCompleted(Message):
    """Emitted when a step completes successfully.

    Attributes:
        step: Step index (0-based)
        result: Optional result data from the step
    """
    step: int
    result: dict | None = None


@dataclass
class StepError(Message):
    """Emitted when a step encounters an error.

    Attributes:
        step: Step index (0-based)
        error: Error message or description
    """
    step: int
    error: str


@dataclass
class PipelineCompleted(Message):
    """Emitted when entire pipeline completes successfully.

    Attributes:
        results: Aggregated results from all steps
    """
    results: dict


@dataclass
class PipelineAborted(Message):
    """Emitted when pipeline is aborted (error or user action).

    Attributes:
        reason: Reason for abortion
        step: Step index where abortion occurred (if applicable)
    """
    reason: str
    step: int | None = None

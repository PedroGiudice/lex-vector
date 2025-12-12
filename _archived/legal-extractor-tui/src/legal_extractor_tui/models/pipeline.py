"""Pipeline configuration and result models.

Pydantic models for pipeline execution configuration and results.
"""

from pydantic import BaseModel, Field


class StepConfig(BaseModel):
    """Configuration for a single pipeline step.

    Attributes:
        name: Human-readable step name
        enabled: Whether this step should execute
        timeout_s: Maximum execution time in seconds
        params: Step-specific parameters
    """
    name: str
    enabled: bool = Field(default=True)
    timeout_s: int = Field(default=60, ge=1)
    params: dict = Field(default_factory=dict)


class PipelineConfig(BaseModel):
    """Configuration for an entire pipeline.

    Attributes:
        name: Pipeline name/identifier
        steps: List of step configurations
        stop_on_error: Whether to halt pipeline on first error
    """
    name: str
    steps: list[StepConfig]
    stop_on_error: bool = Field(default=True)

    def get_enabled_steps(self) -> list[StepConfig]:
        """Get only enabled steps from pipeline.

        Returns:
            List of enabled StepConfig objects
        """
        return [step for step in self.steps if step.enabled]


class StepResult(BaseModel):
    """Result from a single pipeline step execution.

    Attributes:
        step: Step index (0-based)
        name: Step name
        success: Whether step completed successfully
        duration_ms: Execution duration in milliseconds
        output: Step output data
        error: Error message if step failed
    """
    step: int = Field(ge=0)
    name: str
    success: bool
    duration_ms: float = Field(ge=0)
    output: dict | None = Field(default=None)
    error: str | None = Field(default=None)

    @property
    def duration_s(self) -> float:
        """Get duration in seconds."""
        return self.duration_ms / 1000.0

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        duration = f"{self.duration_ms:.0f}ms"
        result = f"Step {self.step}: {self.name} - {status} ({duration})"
        if self.error:
            result += f"\n  Error: {self.error}"
        return result

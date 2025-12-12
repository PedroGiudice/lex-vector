"""Pipeline worker for executing multi-step workflows.

This module provides a worker that executes pipelines with multiple steps,
emitting progress messages at each stage.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from legal_extractor_tui.messages import (
    PipelineAborted,
    PipelineCompleted,
    PipelineStarted,
    StepCompleted,
    StepError,
    StepProgress,
    StepStarted,
)
from legal_extractor_tui.workers.base_worker import BaseWorker


class PipelineStep:
    """Represents a single step in a pipeline.

    Attributes:
        name: Human-readable step name
        function: Callable to execute (can be sync or async)
        args: Positional arguments for function
        kwargs: Keyword arguments for function
    """

    def __init__(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.function = function
        self.args = args
        self.kwargs = kwargs or {}


class PipelineWorker(BaseWorker):
    """Worker for executing multi-step pipelines.

    Executes a series of steps sequentially, emitting progress messages
    for each stage. Supports cancellation and error handling.

    Example:
        ```python
        steps = [
            PipelineStep("Download", download_data, ("url",)),
            PipelineStep("Process", process_data),
            PipelineStep("Upload", upload_results),
        ]

        worker = PipelineWorker(app)
        await worker.run_pipeline(steps)
        ```
    """

    async def run_pipeline(
        self,
        steps: List[PipelineStep],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute pipeline with multiple steps.

        Args:
            steps: List of PipelineStep instances to execute
            context: Shared context dict passed to all steps

        Returns:
            Final context dict with results, or None if cancelled/failed
        """
        if context is None:
            context = {}

        total_steps = len(steps)

        # Emit pipeline started
        self.post_message(PipelineStarted(total_steps=total_steps))

        for step_index, step in enumerate(steps, start=1):
            # Check cancellation before starting step
            if self.is_cancelled:
                self.post_message(
                    PipelineAborted(
                        reason="User cancelled operation",
                        step=step_index,
                    )
                )
                return None

            # Emit step started
            self.post_message(
                StepStarted(
                    step=step_index,
                    name=step.name,
                )
            )

            try:
                # Execute step function
                result = await self._execute_step(step, context, step_index, total_steps)

                # Store result in context
                context[f"step_{step_index}_result"] = result
                context[f"{step.name.lower()}_result"] = result

                # Emit step completed
                self.post_message(
                    StepCompleted(
                        step=step_index,
                        result=result,
                    )
                )

            except Exception as error:
                # Emit step error
                self.post_message(
                    StepError(
                        step=step_index,
                        error=str(error),
                    )
                )
                return None

        # All steps completed successfully
        self.post_message(PipelineCompleted(results=context))

        return context

    async def _execute_step(
        self,
        step: PipelineStep,
        context: Dict[str, Any],
        step_index: int,
        total_steps: int,
    ) -> Any:
        """Execute a single pipeline step with progress updates.

        Args:
            step: PipelineStep to execute
            context: Shared context dict
            step_index: Current step number (1-indexed)
            total_steps: Total number of steps

        Returns:
            Step execution result
        """
        # Simulate work with progress updates
        # In a real implementation, the step function would emit progress
        progress_updates = 10
        for i in range(progress_updates):
            if self.is_cancelled:
                raise RuntimeError("Operation cancelled by user")

            # Emit progress update
            progress = (i + 1) / progress_updates
            self.post_message(
                StepProgress(
                    step=step_index,
                    progress=progress,
                    message=f"Processing... {progress*100:.0f}%",
                )
            )

            # Simulate work
            await asyncio.sleep(0.1)

        # Execute actual step function
        if asyncio.iscoroutinefunction(step.function):
            result = await step.function(*step.args, context=context, **step.kwargs)
        else:
            result = step.function(*step.args, context=context, **step.kwargs)

        return result

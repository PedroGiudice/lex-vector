"""Base worker abstraction for background tasks.

This module provides the base class for implementing workers that handle
long-running operations in the background without blocking the UI.

Workers support cancellation, status tracking, and message posting to the
main application.
"""

from abc import ABC, abstractmethod
from typing import Any

from textual.app import App


class BaseWorker(ABC):
    """Abstract base class for background workers.

    Workers handle asynchronous operations like API calls, file processing,
    or long computations. They can be cancelled, reset, and post messages
    to the main application.

    Attributes:
        app: Reference to the Textual application
        _cancelled: Flag indicating if worker was cancelled

    Example:
        ```python
        class DataFetcher(BaseWorker):
            async def run(self, url: str):
                if self.is_cancelled:
                    return

                data = await fetch_data(url)
                self.post_message(DataReceived(data))
        ```
    """

    def __init__(self, app: App) -> None:
        """Initialize worker with app reference.

        Args:
            app: The Textual application instance
        """
        self.app = app
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the worker operation.

        Sets the cancellation flag. Workers should check `is_cancelled`
        periodically and stop gracefully.
        """
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check if worker was cancelled.

        Returns:
            True if cancel() was called, False otherwise
        """
        return self._cancelled

    def reset(self) -> None:
        """Reset worker state for reuse.

        Clears the cancellation flag so the worker can be run again.
        """
        self._cancelled = False

    def post_message(self, message: Any) -> None:
        """Post a message to the application event queue.

        Args:
            message: Any Textual message instance to post
        """
        self.app.post_message(message)

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the worker's main task.

        This method must be implemented by subclasses. It should:
        - Check `is_cancelled` periodically
        - Post progress messages via `post_message()`
        - Handle errors gracefully
        - Return results or None

        Args:
            *args: Positional arguments for the task
            **kwargs: Keyword arguments for the task

        Returns:
            Task result or None
        """
        ...

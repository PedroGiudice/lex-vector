"""
Middleware for theme injection and request processing.

The theme middleware adds HX-Trigger headers to module load responses,
enabling client-side theme switching without full page reloads.
"""

import json
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def create_theme_trigger(theme_id: str) -> str:
    """
    Create an HX-Trigger header value for theme switching.

    Args:
        theme_id: The theme identifier to switch to

    Returns:
        JSON string for HX-Trigger header
    """
    return json.dumps({
        "themeSwitch": {"theme": theme_id}
    })


class ThemeContext:
    """
    Context manager for tracking active theme in request scope.

    Usage in routes:
        @rt("/m/{module}/")
        def module_index(module: str):
            ThemeContext.set_active(module)
            return ModuleContent()
    """

    _active_theme: Optional[str] = None

    @classmethod
    def set_active(cls, theme_id: str) -> None:
        """Set the active theme for current request."""
        cls._active_theme = theme_id

    @classmethod
    def get_active(cls) -> Optional[str]:
        """Get the active theme for current request."""
        return cls._active_theme

    @classmethod
    def clear(cls) -> None:
        """Clear the active theme."""
        cls._active_theme = None

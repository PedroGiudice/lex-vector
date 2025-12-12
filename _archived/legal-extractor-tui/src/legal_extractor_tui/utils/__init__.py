"""Utility functions for TUI Template.

This package contains helper functions for formatting, ASCII art,
and other common operations.
"""

from .ascii_art import (
    LOGO_SMALL,
    LOGO_VIBE,
    LOGO_BOX,
    SEPARATOR_THIN,
    SEPARATOR_THICK,
    SEPARATOR_DOUBLE,
    BOX_CHARS,
    get_logo,
    colorize_logo,
    render_logo,
    make_box,
)
from .formatting import (
    format_bytes,
    format_duration,
    format_percentage,
    truncate_path,
    format_number,
    pluralize,
)

__all__ = [
    # ASCII art
    "LOGO_SMALL",
    "LOGO_VIBE",
    "LOGO_BOX",
    "SEPARATOR_THIN",
    "SEPARATOR_THICK",
    "SEPARATOR_DOUBLE",
    "BOX_CHARS",
    "get_logo",
    "colorize_logo",
    "render_logo",
    "make_box",
    # Formatting
    "format_bytes",
    "format_duration",
    "format_percentage",
    "truncate_path",
    "format_number",
    "pluralize",
]

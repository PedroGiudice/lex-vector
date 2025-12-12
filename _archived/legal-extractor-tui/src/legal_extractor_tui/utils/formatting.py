"""Formatting utilities for TUI Template.

Helpers for formatting numbers, durations, file sizes, and paths.
"""

import math
from pathlib import Path


def format_bytes(size: int, decimal_places: int = 1) -> str:
    """Format byte count as human-readable string.

    Args:
        size: Size in bytes
        decimal_places: Number of decimal places to show

    Returns:
        Formatted string (e.g., "1.5 MB", "340 KB")

    Example:
        >>> format_bytes(1536)
        '1.5 KB'
        >>> format_bytes(1048576)
        '1.0 MB'
        >>> format_bytes(0)
        '0 B'
    """
    if size == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    index = min(int(math.floor(math.log(size, 1024))), len(units) - 1)
    size_in_unit = size / (1024 ** index)

    if index == 0:  # Bytes - no decimals needed
        return f"{size_in_unit:.0f} {units[index]}"

    return f"{size_in_unit:.{decimal_places}f} {units[index]}"


def format_duration(ms: float, precision: str = "auto") -> str:
    """Format duration in milliseconds as human-readable string.

    Args:
        ms: Duration in milliseconds
        precision: Output precision ('auto', 'ms', 's', 'm', 'h')

    Returns:
        Formatted duration string

    Example:
        >>> format_duration(1500)
        '1.5s'
        >>> format_duration(150)
        '150ms'
        >>> format_duration(90000)
        '1.5m'
        >>> format_duration(3600000)
        '1.0h'
    """
    if ms < 0:
        return "0ms"

    # Auto-select best unit
    if precision == "auto":
        if ms < 1000:  # Less than 1 second
            return f"{ms:.0f}ms"
        elif ms < 60000:  # Less than 1 minute
            return f"{ms / 1000:.1f}s"
        elif ms < 3600000:  # Less than 1 hour
            return f"{ms / 60000:.1f}m"
        else:
            return f"{ms / 3600000:.1f}h"

    # Explicit precision
    if precision == "ms":
        return f"{ms:.0f}ms"
    elif precision == "s":
        return f"{ms / 1000:.1f}s"
    elif precision == "m":
        return f"{ms / 60000:.1f}m"
    elif precision == "h":
        return f"{ms / 3600000:.1f}h"
    else:
        raise ValueError(f"Invalid precision: {precision}")


def format_percentage(value: float, decimals: int = 1, include_symbol: bool = True) -> str:
    """Format float as percentage string.

    Args:
        value: Value between 0.0 and 1.0
        decimals: Number of decimal places
        include_symbol: Whether to include '%' symbol

    Returns:
        Formatted percentage string

    Example:
        >>> format_percentage(0.856)
        '85.6%'
        >>> format_percentage(0.5, decimals=0)
        '50%'
        >>> format_percentage(1.0, include_symbol=False)
        '100.0'
    """
    percentage = value * 100
    formatted = f"{percentage:.{decimals}f}"

    if include_symbol:
        return f"{formatted}%"
    return formatted


def truncate_path(path: str, max_length: int = 40, placeholder: str = "...") -> str:
    """Truncate file path for display, keeping start and end.

    Args:
        path: File path to truncate
        max_length: Maximum display length
        placeholder: String to use for truncated middle section

    Returns:
        Truncated path string

    Example:
        >>> truncate_path("/very/long/path/to/some/file.txt", max_length=30)
        '/very/long/.../file.txt'
        >>> truncate_path("short.txt", max_length=30)
        'short.txt'
    """
    if len(path) <= max_length:
        return path

    path_obj = Path(path)

    # Try to keep filename intact
    filename = path_obj.name
    if len(filename) >= max_length - len(placeholder) - 3:
        # Even filename is too long
        return f"{path[:max_length - len(placeholder)]}{placeholder}"

    # Calculate space for directory portion
    remaining = max_length - len(filename) - len(placeholder)
    if remaining < 3:
        # Not enough space for meaningful directory info
        return f"{placeholder}/{filename}"

    # Show start of path + placeholder + filename
    dir_start = str(path_obj.parent)[:remaining]
    return f"{dir_start}{placeholder}/{filename}"


def format_number(
    value: int | float,
    decimals: int = 0,
    thousands_sep: str = ",",
) -> str:
    """Format number with thousands separator.

    Args:
        value: Number to format
        decimals: Number of decimal places (0 for integers)
        thousands_sep: Separator character (default: comma)

    Returns:
        Formatted number string

    Example:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.5678, decimals=2)
        '1,234.57'
    """
    if decimals == 0:
        return f"{int(value):,}".replace(",", thousands_sep)

    formatted = f"{value:,.{decimals}f}"
    return formatted.replace(",", thousands_sep)


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return singular or plural form based on count.

    Args:
        count: Number of items
        singular: Singular form (e.g., "file")
        plural: Plural form (e.g., "files"). If None, adds 's' to singular

    Returns:
        Appropriate form with count

    Example:
        >>> pluralize(1, "file")
        '1 file'
        >>> pluralize(5, "file")
        '5 files'
        >>> pluralize(1, "query", "queries")
        '1 query'
    """
    if plural is None:
        plural = f"{singular}s"

    word = singular if count == 1 else plural
    return f"{count} {word}"

"""
Theme System for FastHTML Workbench.

Usage:
    from themes import get_theme, THEMES, generate_css

    theme = get_theme("stj")
    css = generate_css(theme)
"""

from .base import BaseTheme, SHARED_THEME
from .modules import (
    STJ_THEME,
    TEXT_EXTRACTOR_THEME,
    DOC_ASSEMBLER_THEME,
    TRELLO_THEME,
    THEMES,
    get_theme,
)
from .css_generator import generate_css, generate_css_variables

__all__ = [
    "BaseTheme",
    "SHARED_THEME",
    "STJ_THEME",
    "TEXT_EXTRACTOR_THEME",
    "DOC_ASSEMBLER_THEME",
    "TRELLO_THEME",
    "THEMES",
    "get_theme",
    "generate_css",
    "generate_css_variables",
]

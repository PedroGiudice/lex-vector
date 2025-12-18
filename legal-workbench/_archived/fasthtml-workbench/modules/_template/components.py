"""
Module Components Template

Define your module's UI components here.
"""

from fasthtml.common import *
from shared.components import module_header, card


def module_index() -> FT:
    """Main module index component."""
    return Div(
        module_header(
            icon="📦",
            name="My Module",
            tagline="Module description here",
        ),
        card(
            "Getting Started",
            P("Edit components.py to customize this module."),
            P("Edit routes.py to add functionality."),
        ),
    )

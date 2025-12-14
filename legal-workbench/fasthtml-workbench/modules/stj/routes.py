"""
STJ Module Routes

All routes are relative to the module mount point (/m/stj/).
Returns Components (not full pages) for HTMX integration.
"""

from fasthtml.common import *
from .components import (
    stj_index,
    search_form,
    search_results,
    quick_stats,
)

# Create module-specific FastHTML app
app = FastHTML()
rt = app.route


@rt("/")
def index():
    """
    Module index page.

    Returns a Component (not full HTML) because this
    will be loaded into the shell's workspace via HTMX.
    """
    # Add HX-Trigger header for theme switch
    return stj_index(), {"HX-Trigger": '{"themeSwitch": {"theme": "stj"}}'}


@rt("/search")
def search(
    termo: str = "",
    orgao: str = "",
    dias: int = 365,
):
    """
    Execute search and return results.
    """
    # In real implementation, this would query the STJ API
    return search_results(termo, orgao, dias)


@rt("/stats")
def stats():
    """
    Return quick stats card.
    """
    return quick_stats()

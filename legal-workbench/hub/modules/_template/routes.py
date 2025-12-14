"""
Module Routes Template

Define your module's routes here.
All routes are relative to the module mount point.
"""

from fasthtml.common import *
from .components import module_index

app = FastHTML()
rt = app.route


@rt("/")
def index():
    """Module index - returns Component for HTMX."""
    return module_index()


# Add more routes as needed:
# @rt("/action")
# def action():
#     return ActionResult()

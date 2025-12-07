"""
Prompt Library Core - Backend para gerenciamento de prompts.

Uso:
    from core import load_library, search, render

    library = load_library(Path("prompts"))
    results = search(library, "contrato")
    output = render(results[0], {"parte": "João"})
"""

from .models import PromptVariable, PromptTemplate, PromptLibrary
from .loader import load_library, load_prompt, reload_library
from .search import search, filter_by_tags
from .renderer import render, preview, RenderError, MissingVariableError

__all__ = [
    # Models
    "PromptVariable",
    "PromptTemplate",
    "PromptLibrary",
    # Loader
    "load_library",
    "load_prompt",
    "reload_library",
    # Search
    "search",
    "filter_by_tags",
    # Renderer
    "render",
    "preview",
    "RenderError",
    "MissingVariableError",
]

"""
STJ Dados Abertos Module

A jurisprudence research tool for querying Brazilian Supreme Court decisions.
Uses observatory purple theme to evoke discovery and exploration.
"""

from .routes import app

# Plugin metadata (required for auto-discovery)
meta = {
    "name": "STJ Dados Abertos",
    "icon": "🔭",
    "description": "Explore a jurisprudência do Superior Tribunal de Justiça",
    "theme_id": "stj",
}

__all__ = ["app", "meta"]

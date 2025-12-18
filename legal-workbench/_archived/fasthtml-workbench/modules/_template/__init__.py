"""
Module Template

Copy this directory to create a new module.

Required exports:
- app: FastHTML application instance
- meta: dict with module metadata

Steps to create a new module:
1. Copy this directory: cp -r _template my_module
2. Update meta dict with your module info
3. Implement routes in routes.py
4. Add components in components.py
5. Restart the server

The module will be auto-discovered and mounted at /m/my_module/
"""

from .routes import app

# UPDATE THIS with your module info
meta = {
    "name": "My Module",                    # Display name
    "icon": "📦",                           # Emoji icon
    "description": "Description here",      # Short description
    "theme_id": "shared",                   # Theme ID (or your custom theme)
}

__all__ = ["app", "meta"]

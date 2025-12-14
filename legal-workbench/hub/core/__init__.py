"""
Core framework for FastHTML Workbench.

Exports:
- PluginRegistry: Dynamic module loader
- Config: Application configuration
"""

from .loader import PluginRegistry, PluginInfo
from .config import Config

__all__ = ["PluginRegistry", "PluginInfo", "Config"]

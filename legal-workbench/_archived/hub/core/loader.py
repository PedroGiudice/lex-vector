"""
Dynamic Plugin Loader for FastHTML Workbench.

Scans the modules/ directory and loads valid plugins at runtime.
Each plugin must export:
- app: FastHTML application instance
- meta: dict with name, icon, description, theme_id (optional)

Usage:
    registry = PluginRegistry()
    registry.discover()

    for plugin in registry.plugins:
        main_app.mount(f"/m/{plugin.id}", plugin.app)
"""

import importlib
import importlib.util
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import config

logger = logging.getLogger(__name__)


@dataclass
class PluginInfo:
    """
    Information about a loaded plugin.

    Attributes:
        id: Unique identifier (directory name)
        name: Display name
        icon: Emoji or icon character
        description: Short description
        theme_id: Theme to use (defaults to plugin id)
        app: FastHTML application instance
        mount_path: URL path where plugin is mounted
    """
    id: str
    name: str
    icon: str
    description: str
    theme_id: str
    app: Any  # FastHTML app
    mount_path: str = field(init=False)

    def __post_init__(self):
        self.mount_path = f"/m/{self.id}"


class PluginRegistry:
    """
    Registry for dynamically loaded plugins.

    Scans the modules/ directory for valid plugin packages and
    loads them into memory. Invalid plugins are logged but don't
    crash the application.
    """

    def __init__(self, modules_dir: Optional[Path] = None):
        self.modules_dir = modules_dir or config.MODULES_DIR
        self._plugins: Dict[str, PluginInfo] = {}
        self._errors: List[str] = []

    @property
    def plugins(self) -> List[PluginInfo]:
        """Get list of all loaded plugins."""
        return list(self._plugins.values())

    @property
    def errors(self) -> List[str]:
        """Get list of loading errors."""
        return self._errors.copy()

    def get(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get a plugin by ID."""
        return self._plugins.get(plugin_id)

    def discover(self) -> "PluginRegistry":
        """
        Discover and load all plugins from modules directory.

        Returns self for chaining.
        """
        logger.info(f"Discovering plugins in {self.modules_dir}")

        if not self.modules_dir.exists():
            logger.warning(f"Modules directory does not exist: {self.modules_dir}")
            return self

        for path in self.modules_dir.iterdir():
            # Skip non-directories and hidden/special directories
            if not path.is_dir():
                continue
            if path.name.startswith("_") or path.name.startswith("."):
                continue

            # Try to load as plugin
            self._load_plugin(path)

        logger.info(f"Loaded {len(self._plugins)} plugins, {len(self._errors)} errors")
        return self

    def _load_plugin(self, path: Path) -> None:
        """
        Load a single plugin from a directory.

        Args:
            path: Path to plugin directory
        """
        plugin_id = path.name
        init_file = path / "__init__.py"

        if not init_file.exists():
            logger.debug(f"Skipping {plugin_id}: no __init__.py")
            return

        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                f"modules.{plugin_id}",
                init_file
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {plugin_id}")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Validate required exports
            if not hasattr(module, "app"):
                raise AttributeError(f"Plugin {plugin_id} missing 'app' export")
            if not hasattr(module, "meta"):
                raise AttributeError(f"Plugin {plugin_id} missing 'meta' export")

            meta = module.meta

            # Validate meta structure
            required_keys = {"name", "icon"}
            if not required_keys.issubset(meta.keys()):
                missing = required_keys - set(meta.keys())
                raise ValueError(f"Plugin {plugin_id} meta missing keys: {missing}")

            # Create plugin info
            plugin = PluginInfo(
                id=plugin_id,
                name=meta["name"],
                icon=meta["icon"],
                description=meta.get("description", ""),
                theme_id=meta.get("theme_id", plugin_id),
                app=module.app,
            )

            self._plugins[plugin_id] = plugin
            logger.info(f"Loaded plugin: {plugin.icon} {plugin.name} ({plugin_id})")

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_id}: {e}"
            logger.error(error_msg)
            self._errors.append(error_msg)

    def mount_all(self, main_app: Any) -> None:
        """
        Mount all plugins to a FastHTML app.

        Args:
            main_app: The main FastHTML application
        """
        for plugin in self.plugins:
            main_app.mount(plugin.mount_path, plugin.app)
            logger.info(f"Mounted {plugin.name} at {plugin.mount_path}")

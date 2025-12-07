"""
Configuração persistente do backend.

Armazena preferências em ~/.claude-ui/config.json
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field
from .exceptions import ConfigError

logger = logging.getLogger(__name__)


@dataclass
class StatusLineConfig:
    """Configuração visual da statusline."""
    show_model: bool = True
    show_path: bool = True
    show_git: bool = True
    show_context: bool = True
    show_cost: bool = True
    show_time: bool = True

    color_model: str = "#c084fc"
    color_path: str = "#4ade80"
    color_git: str = "#facc15"
    color_context: str = "#60a5fa"
    color_cost: str = "#f87171"
    color_time: str = "#888888"


@dataclass
class AppConfig:
    """Configuração geral da aplicação."""
    default_project: str = ""
    skip_permissions: bool = True
    auto_reconnect: bool = True
    theme: str = "dark"
    font_family: str = "OpenDyslexic"
    font_size: int = 14
    statusline: StatusLineConfig = field(default_factory=StatusLineConfig)

    # Advanced settings
    cli_timeout: float = 120.0
    reconnect_delay: float = 1.0
    max_reconnect_attempts: int = 3
    output_buffer_size: int = 10000

    def __post_init__(self):
        """Ensure statusline is properly initialized."""
        if self.statusline is None:
            self.statusline = StatusLineConfig()
        elif isinstance(self.statusline, dict):
            self.statusline = StatusLineConfig(**self.statusline)


class ConfigManager:
    """
    Gerencia configuração persistente.

    Arquivo: ~/.claude-ui/config.json

    Usage:
        config_mgr = ConfigManager()
        config = config_mgr.get()
        config.theme = "light"
        config_mgr.save(config)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: Caminho para arquivo de config.
                        Default: ~/.claude-ui/config.json
        """
        self.config_path = config_path or Path.home() / ".claude-ui" / "config.json"
        self._config: Optional[AppConfig] = None

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        """
        Carrega configuração do disco ou retorna defaults.

        Returns:
            AppConfig carregado ou default
        """
        if not self.config_path.exists():
            logger.info("Config file not found, using defaults")
            self._config = AppConfig()
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle nested statusline config
            if 'statusline' in data and isinstance(data['statusline'], dict):
                data['statusline'] = StatusLineConfig(**data['statusline'])

            self._config = AppConfig(**data)
            logger.info(f"Loaded config from {self.config_path}")
            return self._config

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted config file, using defaults: {e}")
            self._config = AppConfig()
            return self._config
        except TypeError as e:
            logger.warning(f"Config has unknown fields, using partial: {e}")
            self._config = AppConfig()
            return self._config

    def save(self, config: AppConfig) -> None:
        """
        Salva configuração em disco.

        Args:
            config: AppConfig a salvar

        Raises:
            ConfigError: Se falhar ao salvar
        """
        try:
            data = self._serialize_config(config)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._config = config
            logger.info(f"Saved config to {self.config_path}")

        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}") from e

    def get(self) -> AppConfig:
        """
        Retorna configuração atual (carrega se necessário).

        Returns:
            AppConfig atual
        """
        if self._config is None:
            return self.load()
        return self._config

    def update(self, **kwargs) -> AppConfig:
        """
        Atualiza campos específicos e salva.

        Args:
            **kwargs: Campos a atualizar

        Returns:
            AppConfig atualizado

        Example:
            config_mgr.update(theme="light", font_size=16)
        """
        config = self.get()

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
            elif hasattr(config.statusline, key):
                setattr(config.statusline, key, value)
            else:
                logger.warning(f"Unknown config key: {key}")

        self.save(config)
        return config

    def reset(self) -> AppConfig:
        """
        Reseta para configuração padrão.

        Returns:
            AppConfig default
        """
        self._config = AppConfig()
        self.save(self._config)
        logger.info("Config reset to defaults")
        return self._config

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor específico de configuração.

        Args:
            key: Nome do campo (suporta "statusline.show_model")
            default: Valor padrão se não encontrado

        Returns:
            Valor do campo ou default
        """
        config = self.get()

        if '.' in key:
            parts = key.split('.')
            obj = config
            for part in parts:
                if hasattr(obj, part):
                    obj = getattr(obj, part)
                else:
                    return default
            return obj

        return getattr(config, key, default)

    def set_value(self, key: str, value: Any) -> None:
        """
        Define valor específico de configuração.

        Args:
            key: Nome do campo (suporta "statusline.show_model")
            value: Novo valor
        """
        config = self.get()

        if '.' in key:
            parts = key.split('.')
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)
        else:
            setattr(config, key, value)

        self.save(config)

    def _serialize_config(self, config: AppConfig) -> Dict[str, Any]:
        """Converte AppConfig para dicionário serializável."""
        data = {
            'default_project': config.default_project,
            'skip_permissions': config.skip_permissions,
            'auto_reconnect': config.auto_reconnect,
            'theme': config.theme,
            'font_family': config.font_family,
            'font_size': config.font_size,
            'cli_timeout': config.cli_timeout,
            'reconnect_delay': config.reconnect_delay,
            'max_reconnect_attempts': config.max_reconnect_attempts,
            'output_buffer_size': config.output_buffer_size,
            'statusline': {
                'show_model': config.statusline.show_model,
                'show_path': config.statusline.show_path,
                'show_git': config.statusline.show_git,
                'show_context': config.statusline.show_context,
                'show_cost': config.statusline.show_cost,
                'show_time': config.statusline.show_time,
                'color_model': config.statusline.color_model,
                'color_path': config.statusline.color_path,
                'color_git': config.statusline.color_git,
                'color_context': config.statusline.color_context,
                'color_cost': config.statusline.color_cost,
                'color_time': config.statusline.color_time,
            }
        }
        return data

    def export_config(self) -> str:
        """
        Exporta configuração como JSON string.

        Returns:
            JSON formatado
        """
        config = self.get()
        data = self._serialize_config(config)
        return json.dumps(data, indent=2)

    def import_config(self, json_str: str) -> AppConfig:
        """
        Importa configuração de JSON string.

        Args:
            json_str: JSON de configuração

        Returns:
            AppConfig importado e salvo

        Raises:
            ConfigError: Se JSON inválido
        """
        try:
            data = json.loads(json_str)

            if 'statusline' in data and isinstance(data['statusline'], dict):
                data['statusline'] = StatusLineConfig(**data['statusline'])

            config = AppConfig(**data)
            self.save(config)
            return config

        except (json.JSONDecodeError, TypeError) as e:
            raise ConfigError(f"Invalid config JSON: {e}") from e

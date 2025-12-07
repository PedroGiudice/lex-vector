"""
Claude Code UI - Backend

Backend Python para interface gráfica do Claude Code CLI.

Este módulo fornece:
- ClaudeCodeWrapper: Comunicação com o CLI via subprocess
- OutputParser: Parse de output em blocos estruturados
- StatusLineParser: Parse de dados da statusline
- SessionManager: Gestão de sessões com persistência
- ConfigManager: Configuração persistente

Usage:
    from backend import ClaudeCodeWrapper, OutputParser, SessionManager

    wrapper = ClaudeCodeWrapper(
        project_path="/path/to/project",
        on_output=lambda text: print(text)
    )
    wrapper.start()
    wrapper.send("Hello Claude")
    wrapper.stop()
"""

# Core wrapper
from .wrapper import ClaudeCodeWrapper

# Parsers
from .parser import OutputParser
from .statusline import StatusLineParser

# Managers
from .session import SessionManager
from .config import ConfigManager, AppConfig, StatusLineConfig

# Models
from .models import (
    CLIState,
    ContentType,
    ContentBlock,
    StatusLineData,
    Message,
    Session,
)

# Exceptions
from .exceptions import (
    ClaudeUIError,
    CLINotFoundError,
    CLIConnectionError,
    CLITimeoutError,
    SessionNotFoundError,
    ConfigError,
)

__version__ = "0.1.0"
__author__ = "Claude UI Team"

__all__ = [
    # Core
    "ClaudeCodeWrapper",

    # Parsers
    "OutputParser",
    "StatusLineParser",

    # Managers
    "SessionManager",
    "ConfigManager",
    "AppConfig",
    "StatusLineConfig",

    # Models
    "CLIState",
    "ContentType",
    "ContentBlock",
    "StatusLineData",
    "Message",
    "Session",

    # Exceptions
    "ClaudeUIError",
    "CLINotFoundError",
    "CLIConnectionError",
    "CLITimeoutError",
    "SessionNotFoundError",
    "ConfigError",
]

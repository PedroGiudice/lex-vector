"""Exceções customizadas do backend."""

class ClaudeUIError(Exception):
    """Base para todas as exceções do backend."""
    pass

class CLINotFoundError(ClaudeUIError):
    """Claude Code CLI não está instalado."""
    pass

class CLIConnectionError(ClaudeUIError):
    """Falha ao conectar/comunicar com o CLI."""
    pass

class CLITimeoutError(ClaudeUIError):
    """Timeout esperando resposta do CLI."""
    pass

class SessionNotFoundError(ClaudeUIError):
    """Sessão não encontrada."""
    pass

class ConfigError(ClaudeUIError):
    """Erro de configuração."""
    pass

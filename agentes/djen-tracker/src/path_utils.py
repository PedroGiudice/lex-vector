"""
Path Utils - Auto-detecção de ambiente (Windows vs WSL2)

Resolve o problema de paths hardcoded que não funcionam em ambientes diferentes.
Detecta automaticamente se está rodando em:
- Windows (E:/claude-code-data)
- WSL2 (/mnt/e/claude-code-data)
- Fallback (~/.claude-code-data)
"""
import os
from pathlib import Path
from typing import Optional


def get_data_root() -> Path:
    """
    Auto-detecta data root baseado no sistema operacional.

    Tenta em ordem:
    1. Variável de ambiente CLAUDE_DATA_ROOT (override manual)
    2. WSL2: /mnt/e/claude-code-data
    3. Windows: E:/claude-code-data
    4. Fallback: ~/.claude-code-data

    Returns:
        Path object para data root

    Examples:
        >>> data_root = get_data_root()
        >>> downloads_dir = data_root / "agentes" / "djen-tracker" / "downloads"
    """
    # 1. Override manual via environment variable
    if env_root := os.getenv('CLAUDE_DATA_ROOT'):
        path = Path(env_root)
        if path.exists():
            return path

    # 2. WSL2 path (Linux mounting Windows drive)
    wsl_path = Path('/mnt/e/claude-code-data')
    if wsl_path.exists():
        return wsl_path

    # 3. Windows path
    win_path = Path('E:/claude-code-data')
    if win_path.exists():
        return win_path

    # 4. Fallback: Home directory
    fallback = Path.home() / '.claude-code-data'
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_agent_data_dir(agent_name: str, subdir: str = "") -> Path:
    """
    Retorna path para diretório de dados do agente.

    Args:
        agent_name: Nome do agente (ex: 'djen-tracker', 'oab-watcher')
        subdir: Subdiretório opcional (ex: 'downloads', 'logs', 'cache')

    Returns:
        Path object para diretório do agente

    Examples:
        >>> logs_dir = get_agent_data_dir('djen-tracker', 'logs')
        >>> cache_dir = get_agent_data_dir('oab-watcher', 'cache')
    """
    data_root = get_data_root()
    agent_dir = data_root / 'agentes' / agent_name

    if subdir:
        return agent_dir / subdir

    return agent_dir


def resolve_config_paths(config: dict, agent_name: str) -> dict:
    """
    Resolve paths hardcoded no config.json para paths absolutos corretos.

    Args:
        config: Dict de configuração (config.json)
        agent_name: Nome do agente

    Returns:
        Config atualizado com paths corretos

    Examples:
        >>> config = json.load(open('config.json'))
        >>> config = resolve_config_paths(config, 'djen-tracker')
        >>> print(config['paths']['data_root'])  # /mnt/e/claude-code-data/agentes/djen-tracker
    """
    config = config.copy()

    # Resolver data_root
    data_root = get_agent_data_dir(agent_name)
    config['paths']['data_root'] = str(data_root)

    return config


def detect_environment() -> str:
    """
    Detecta em qual ambiente o código está rodando.

    Returns:
        'wsl2', 'windows', ou 'unknown'

    Examples:
        >>> env = detect_environment()
        >>> print(f"Rodando em: {env}")
    """
    if Path('/mnt/wsl').exists() or Path('/mnt/c').exists():
        return 'wsl2'
    elif os.name == 'nt':
        return 'windows'
    else:
        return 'unknown'


if __name__ == "__main__":
    # Self-test
    print("Path Utils - Auto-detecção de Ambiente")
    print("=" * 70)
    print(f"Ambiente detectado: {detect_environment()}")
    print(f"Data root: {get_data_root()}")
    print(f"DJEN Tracker data: {get_agent_data_dir('djen-tracker')}")
    print(f"DJEN Tracker logs: {get_agent_data_dir('djen-tracker', 'logs')}")
    print("=" * 70)

"""
Path management utilities - WSL local com cache
Compliance: CLAUDE.md three-layer separation

PC Casa: Acesso direto filesystem local + cache para otimização
PC Trabalho: Servidor corporativo (adaptação futura)
"""
from pathlib import Path
import shutil
from typing import Optional


# Configuração global (PC Casa - acesso local)
DATA_ROOT = Path.home() / 'claude-code-data'
CACHE_ROOT = Path.home() / 'documentos-juridicos-cache'
OUTPUTS = DATA_ROOT / 'outputs'


def get_data_dir(agent_name: str, subdir: str = "") -> Path:
    """
    Retorna path para diretório de dados do agente.

    Args:
        agent_name: Nome do agente (ex: 'oab-watcher')
        subdir: Subdiretório (ex: 'downloads', 'logs', 'outputs')

    Returns:
        Path object para diretório de dados

    Examples:
        >>> get_data_dir('oab-watcher', 'downloads')
        PosixPath('/home/cmr-auto/claude-code-data/agentes/oab-watcher/downloads')
    """
    agent_data = DATA_ROOT / 'agentes' / agent_name

    if subdir:
        return agent_data / subdir
    return agent_data


def ensure_data_dirs(agent_name: str, subdirs: list[str]) -> dict[str, Path]:
    """
    Garante que diretórios de dados existam, criando se necessário.

    Args:
        agent_name: Nome do agente
        subdirs: Lista de subdiretórios necessários

    Returns:
        Dict mapeando nome -> Path criado

    Examples:
        >>> ensure_data_dirs('oab-watcher', ['downloads', 'logs', 'outputs'])
        {'downloads': Path(...), 'logs': Path(...), 'outputs': Path(...)}
    """
    paths = {}

    for subdir in subdirs:
        path = get_data_dir(agent_name, subdir)
        path.mkdir(parents=True, exist_ok=True)
        paths[subdir] = path

    return paths


def get_cache_path(relative_path: str = "") -> Path:
    """
    Retorna path para cache local (otimização de performance).

    Args:
        relative_path: Caminho relativo dentro do cache

    Returns:
        Path object para cache

    Examples:
        >>> get_cache_path('processos/12345.pdf')
        PosixPath('/home/cmr-auto/documentos-juridicos-cache/processos/12345.pdf')
    """
    if relative_path:
        return CACHE_ROOT / relative_path
    return CACHE_ROOT


def get_output_path(agent_name: str, subdir: str = "") -> Path:
    """
    Retorna path para outputs do agente.

    Args:
        agent_name: Nome do agente
        subdir: Subdiretório de output (opcional)

    Returns:
        Path object para outputs

    Examples:
        >>> get_output_path('oab-watcher', 'relatorios')
        PosixPath('/home/cmr-auto/claude-code-data/outputs/oab-watcher/relatorios')
    """
    agent_output = OUTPUTS / agent_name

    if subdir:
        return agent_output / subdir
    return agent_output


def get_documento(filename: str, source_dir: Path, use_cache: bool = True) -> Path:
    """
    Obtém documento com estratégia cache-first (otimização).

    Args:
        filename: Nome do arquivo (ex: 'publicacao_123.pdf')
        source_dir: Diretório fonte original
        use_cache: Se True, tenta cache primeiro

    Returns:
        Path para arquivo (cache ou original)

    Estratégia:
        1. Se use_cache=True e arquivo em cache atualizado → retorna cache (rápido)
        2. Senão, copia de source_dir para cache → retorna cache
        3. Se cache falhar, retorna source_dir diretamente
    """
    cache_file = CACHE_ROOT / filename
    source_file = source_dir / filename

    if not source_file.exists():
        raise FileNotFoundError(f"Documento {filename} não encontrado em {source_dir}")

    # Se cache desabilitado, retorna fonte direto
    if not use_cache:
        return source_file

    # Cache habilitado: verificar se cache está atualizado
    if cache_file.exists():
        # Comparar timestamps (cache atualizado?)
        if cache_file.stat().st_mtime >= source_file.stat().st_mtime:
            return cache_file  # Cache válido, usar

    # Cache desatualizado ou não existe: copiar de fonte
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, cache_file)
        return cache_file
    except Exception as e:
        # Se cache falhar, retorna fonte diretamente (fallback seguro)
        print(f"Aviso: Falha ao cachear {filename}: {e}. Usando fonte direta.")
        return source_file


def cleanup_cache(max_age_days: int = 30):
    """
    Limpa arquivos antigos do cache (otimização de espaço).

    Args:
        max_age_days: Idade máxima em dias (padrão: 30)
    """
    import time

    if not CACHE_ROOT.exists():
        return

    cutoff_time = time.time() - (max_age_days * 86400)
    removed_count = 0

    for file_path in CACHE_ROOT.rglob('*'):
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                removed_count += 1

    print(f"Cache cleanup: {removed_count} arquivos removidos (>{max_age_days} dias)")

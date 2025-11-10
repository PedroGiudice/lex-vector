"""
Utilities - Funções auxiliares
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict


def configurar_logging(config: Dict) -> logging.Logger:
    """
    Configura sistema de logging

    Args:
        config: Configuração do agente

    Returns:
        Logger configurado
    """
    data_root = Path(config['paths']['data_root'])
    logs_dir = data_root / config['paths']['logs']
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Nome do arquivo de log com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f'legal_lens_{timestamp}.log'

    # Configurar formato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configurar handlers
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configurado - Arquivo: {log_file}")

    return logger


def formatar_tamanho(bytes_size: int) -> str:
    """
    Formata tamanho de arquivo em formato legível

    Args:
        bytes_size: Tamanho em bytes

    Returns:
        String formatada (ex: '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto para exibição

    Args:
        text: Texto original
        max_length: Comprimento máximo
        suffix: Sufixo para textos truncados

    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def ensure_dir(path: Path) -> Path:
    """
    Garante que diretório existe

    Args:
        path: Caminho do diretório

    Returns:
        Path do diretório criado
    """
    path.mkdir(parents=True, exist_ok=True)
    return path

"""
Configuracao do sistema STJ Dados Abertos

Sistema de armazenamento local simplificado.
Todos os dados sao armazenados em data/ dentro do projeto.
"""
from __future__ import annotations

import logging
import os
import shutil
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import Final, TypedDict

# Logger for this module
logger = logging.getLogger(__name__)


# Type definitions
class OrgaoConfig(TypedDict):
    """Configuração de um órgão julgador."""
    name: str
    path: str
    priority: int


# Project structure
PROJECT_ROOT: Final[Path] = Path(__file__).parent
SRC_DIR: Final[Path] = PROJECT_ROOT / "src"
DATA_ROOT: Final[Path] = PROJECT_ROOT / "data"

# Data directories (all local)
STAGING_DIR: Final[Path] = DATA_ROOT / "staging"
ARCHIVE_DIR: Final[Path] = DATA_ROOT / "archive"
DATABASE_DIR: Final[Path] = DATA_ROOT / "database"
LOGS_DIR: Final[Path] = DATA_ROOT / "logs"
METADATA_DIR: Final[Path] = DATA_ROOT / "metadata"

# Database paths
DATABASE_PATH: Final[Path] = DATABASE_DIR / "stj.duckdb"
DATABASE_BACKUP_DIR: Final[Path] = DATABASE_DIR / "backups"
METADATA_DB_PATH: Final[Path] = METADATA_DIR / "metadata.db"
STATS_PATH: Final[Path] = METADATA_DIR / "stats.json"

# Create all necessary directories
for dir_path in [STAGING_DIR, ARCHIVE_DIR, DATABASE_DIR, LOGS_DIR,
                 METADATA_DIR, DATABASE_BACKUP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# CKAN API Configuration (New Data Source)
CKAN_BASE_URL: Final[str] = "https://dadosabertos.web.stj.jus.br"
CKAN_API_VERSION: Final[str] = "3"

# Map orgao keys to CKAN dataset IDs
CKAN_DATASETS: Final[dict[str, str]] = {
    "corte_especial": "espelhos-de-acordaos-corte-especial",
    "primeira_secao": "espelhos-de-acordaos-primeira-secao",
    "segunda_secao": "espelhos-de-acordaos-segunda-secao",
    "terceira_secao": "espelhos-de-acordaos-terceira-secao",
    "primeira_turma": "espelhos-de-acordaos-primeira-turma",
    "segunda_turma": "espelhos-de-acordaos-segunda-turma",
    "terceira_turma": "espelhos-de-acordaos-terceira-turma",
    "quarta_turma": "espelhos-de-acordaos-quarta-turma",
    "quinta_turma": "espelhos-de-acordaos-quinta-turma",
    "sexta_turma": "espelhos-de-acordaos-sexta-turma",
}

# Legacy URL (DEPRECATED - returns 404)
STJ_BASE_URL_LEGACY: Final[str] = "https://www.stj.jus.br/sites/portalp/SiteAssets/documentos/noticias/abertos/"

# Keep old name for backward compatibility (DEPRECATED)
STJ_BASE_URL: Final[str] = STJ_BASE_URL_LEGACY


def get_orgao_dataset_id(orgao: str) -> str:
    """
    Get CKAN dataset ID for an orgao key.

    Args:
        orgao: Orgao key (e.g., "primeira_turma")

    Returns:
        CKAN dataset ID (e.g., "espelhos-de-acordaos-primeira-turma")

    Raises:
        KeyError: If orgao not found in CKAN_DATASETS
    """
    return CKAN_DATASETS[orgao]


def get_ckan_package_url(orgao: str) -> str:
    """
    Get CKAN API URL for package metadata.

    Args:
        orgao: Orgao key (e.g., "primeira_turma")

    Returns:
        Full CKAN API URL for package_show endpoint
    """
    dataset_id = get_orgao_dataset_id(orgao)
    return f"{CKAN_BASE_URL}/api/{CKAN_API_VERSION}/action/package_show?id={dataset_id}"

# Datasets de Acórdãos por Órgão Julgador
ORGAOS_JULGADORES: Final[dict[str, OrgaoConfig]] = {
    "corte_especial": {
        "name": "Corte Especial",
        "path": "CorteEspecial",
        "priority": 1
    },
    "primeira_secao": {
        "name": "Primeira Seção",
        "path": "PrimeiraSecao",
        "priority": 2
    },
    "segunda_secao": {
        "name": "Segunda Seção",
        "path": "SegundaSecao",
        "priority": 2
    },
    "terceira_secao": {
        "name": "Terceira Seção",
        "path": "TerceiraSecao",
        "priority": 3
    },
    "primeira_turma": {
        "name": "Primeira Turma",
        "path": "PrimeiraTurma",
        "priority": 4
    },
    "segunda_turma": {
        "name": "Segunda Turma",
        "path": "SegundaTurma",
        "priority": 4
    },
    "terceira_turma": {
        "name": "Terceira Turma",
        "path": "TerceiraTurma",
        "priority": 4
    },
    "quarta_turma": {
        "name": "Quarta Turma",
        "path": "QuartaTurma",
        "priority": 4
    },
    "quinta_turma": {
        "name": "Quinta Turma",
        "path": "QuintaTurma",
        "priority": 4
    },
    "sexta_turma": {
        "name": "Sexta Turma",
        "path": "SextaTurma",
        "priority": 4
    }
}

# Download configuration
DEFAULT_TIMEOUT: Final[int] = 30  # seconds
DEFAULT_RETRY_ATTEMPTS: Final[int] = 3
DEFAULT_RETRY_DELAY: Final[int] = 5  # seconds
CONCURRENT_DOWNLOADS: Final[int] = 4  # Parallel downloads
BATCH_SIZE: Final[int] = 1000  # Records per transaction

# Date ranges
MIN_DATE: Final[datetime] = datetime(2022, 5, 1)  # STJ data starts from May 2022
MAX_DAYS_MVP: Final[int] = 30  # MVP: Last 30 days only

# Logging
LOG_LEVEL: Final[str] = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE: Final[Path] = LOGS_DIR / f"stj_{datetime.now():%Y%m}.log"

# Performance settings
DUCKDB_MEMORY_LIMIT: Final[str] = "4GB"  # DuckDB memory limit
DUCKDB_THREADS: Final[int] = 4  # Number of threads for DuckDB
CHUNK_SIZE: Final[int] = 10000  # Process records in chunks

# Schema monitoring
SCHEMA_VERSION: Final[str] = "1.0.0"
SCHEMA_CHECK_ENABLED: Final[bool] = True
SCHEMA_FIELDS_EXPECTED: Final[list[str]] = [
    "id",
    "numeroProcesso",
    "dataPublicacao",
    "dataJulgamento",
    "orgaoJulgador",
    "relator",
    "ementa",
    "textoIntegral"
]


def get_date_range_urls(start_date: datetime, end_date: datetime, orgao: str) -> list[dict[str, str | int]]:
    """
    DEPRECATED: Legacy URL pattern no longer works (returns 404).

    Use CKANClient.get_resources() instead to discover available CSV files
    via the CKAN API.

    Args:
        start_date: Data inicial do periodo (ignored)
        end_date: Data final do periodo (ignored)
        orgao: Chave do orgao julgador (ignored)

    Returns:
        Empty list (legacy URLs return 404)
    """
    warnings.warn(
        "get_date_range_urls() is deprecated. Legacy STJ URLs return 404. "
        "Use CKANClient.get_resources() to discover available files via CKAN API.",
        DeprecationWarning,
        stacklevel=2,
    )
    logger.warning(
        "get_date_range_urls() called but is deprecated. "
        "Legacy URL pattern %s no longer works. Use CKAN API instead.",
        STJ_BASE_URL_LEGACY,
    )
    return []


def get_mvp_urls() -> list[dict[str, str | int]]:
    """
    DEPRECATED: Legacy URL pattern no longer works (returns 404).

    Use CKANClient to discover and download resources via CKAN API.

    Returns:
        Empty list (legacy URLs return 404)
    """
    warnings.warn(
        "get_mvp_urls() is deprecated. Legacy STJ URLs return 404. "
        "Use CKANClient to discover available files via CKAN API.",
        DeprecationWarning,
        stacklevel=2,
    )
    logger.warning(
        "get_mvp_urls() called but is deprecated. Use CKAN API instead."
    )
    return []


def get_storage_info() -> dict[str, str | float | bool]:
    """
    Retorna informações sobre armazenamento local.

    Returns:
        Dicionário com informações de espaço e uso do DATA_ROOT
    """
    info: dict[str, str | float | bool] = {
        "path": str(DATA_ROOT),
        "free_gb": 0.0,
        "used_gb": 0.0,
        "total_gb": 0.0,
        "valid": False
    }

    try:
        usage = shutil.disk_usage(DATA_ROOT)
        info["free_gb"] = usage.free / (1024**3)
        info["used_gb"] = usage.used / (1024**3)
        info["total_gb"] = usage.total / (1024**3)
        info["valid"] = True
    except Exception:
        pass

    return info

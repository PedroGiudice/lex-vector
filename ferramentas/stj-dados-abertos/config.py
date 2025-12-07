"""
Configuração do sistema STJ Dados Abertos

Sistema de armazenamento local simplificado.
Todos os dados são armazenados em data/ dentro do projeto.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Final, TypedDict


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

# STJ Dados Abertos URLs
STJ_BASE_URL: Final[str] = "https://www.stj.jus.br/sites/portalp/SiteAssets/documentos/noticias/abertos/"

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
    Gera URLs para download de JSONs em um período.

    STJ organiza por ano/mês, ex:
    - 2024/202401.json (Janeiro 2024)
    - 2024/202402.json (Fevereiro 2024)

    Args:
        start_date: Data inicial do período
        end_date: Data final do período
        orgao: Chave do órgão julgador em ORGAOS_JULGADORES

    Returns:
        Lista de dicionários com url, year, month, orgao, filename
    """
    urls: list[dict[str, str | int]] = []
    current = start_date.replace(day=1)

    while current <= end_date:
        year = current.year
        month = f"{current.year}{current.month:02d}"

        # URL pattern: base/orgao/year/YYYYMM.json
        url = f"{STJ_BASE_URL}{ORGAOS_JULGADORES[orgao]['path']}/{year}/{month}.json"
        urls.append({
            "url": url,
            "year": year,
            "month": current.month,
            "orgao": orgao,
            "filename": f"{orgao}_{month}.json"
        })

        # Next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return urls


def get_mvp_urls() -> list[dict[str, str | int]]:
    """
    Retorna URLs para MVP (últimos 30 dias, Corte Especial apenas).

    Returns:
        Lista de URLs para download do MVP
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=MAX_DAYS_MVP)

    # Para MVP, pegar apenas Corte Especial (mais importante)
    return get_date_range_urls(start_date, end_date, "corte_especial")


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

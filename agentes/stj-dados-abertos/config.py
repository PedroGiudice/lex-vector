"""
Configuração do sistema STJ Dados Abertos
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Paths configuration
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

# ARQUITETURA HÍBRIDA: Índices no SSD, Dados no HD
# Performance comprovada: índices no SSD são 125x mais rápidos para random reads
import shutil

# CAMADA 1: ÍNDICES (SSD - Rápido, 2-5GB)
# Índices DuckDB, metadados, cache - tudo que precisa acesso rápido
INDEX_PATH = Path.home() / "stj-indices"
INDEX_PATH.mkdir(exist_ok=True)

# CAMADA 2: DADOS (HD Externo - Grande capacidade, 50GB+)
# Documentos completos, JSONs, backups - tudo que ocupa muito espaço
EXTERNAL_DRIVE = None
drive_info = []

# Detectar HD externo com mais espaço
for drive_letter in ['d', 'e', 'f', 'g', 'h']:
    mount_point = Path(f"/mnt/{drive_letter}")
    if mount_point.exists() and os.access(mount_point, os.W_OK):
        try:
            usage = shutil.disk_usage(mount_point)
            free_gb = usage.free / (1024**3)
            drive_info.append((mount_point, free_gb))
        except:
            continue

# Escolher drive com mais espaço livre (mínimo 50GB para dados)
MIN_SPACE_GB = 50
for drive, free_gb in sorted(drive_info, key=lambda x: x[1], reverse=True):
    if free_gb >= MIN_SPACE_GB:
        EXTERNAL_DRIVE = drive
        print(f"✅ HD externo detectado: {drive} ({free_gb:.1f}GB livres)")
        break

if not EXTERNAL_DRIVE:
    print("⚠️  HD externo não encontrado! Usando /tmp temporariamente.")
    print("   AVISO: Performance será degradada sem HD externo!")
    EXTERNAL_DRIVE = Path("/tmp/stj-data-temp")
    EXTERNAL_DRIVE.mkdir(exist_ok=True)

# Paths híbridos
DATA_ROOT = EXTERNAL_DRIVE / "juridico-data" / "stj"  # HD: Dados grandes
INDEX_DB_PATH = INDEX_PATH / "stj.duckdb"             # SSD: Índices DuckDB
METADATA_DB_PATH = INDEX_PATH / "metadata.db"         # SSD: Cache metadados
STATS_PATH = INDEX_PATH / "stats.json"                # SSD: Estatísticas
STAGING_DIR = DATA_ROOT / "staging"
ARCHIVE_DIR = DATA_ROOT / "archive"
DATABASE_DIR = DATA_ROOT / "database"
LOGS_DIR = DATA_ROOT / "logs"

# Create directories if they don't exist
for dir_path in [STAGING_DIR, ARCHIVE_DIR, DATABASE_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Database configuration
DATABASE_PATH = DATABASE_DIR / "stj.duckdb"
DATABASE_BACKUP_DIR = DATABASE_DIR / "backups"
DATABASE_BACKUP_DIR.mkdir(exist_ok=True)

# STJ Dados Abertos URLs
STJ_BASE_URL = "https://www.stj.jus.br/sites/portalp/SiteAssets/documentos/noticias/abertos/"

# Datasets de Acórdãos por Órgão Julgador
ORGAOS_JULGADORES = {
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
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 5  # seconds
CONCURRENT_DOWNLOADS = 4  # Parallel downloads
BATCH_SIZE = 1000  # Records per transaction

# Date ranges
MIN_DATE = datetime(2022, 5, 1)  # STJ data starts from May 2022
MAX_DAYS_MVP = 30  # MVP: Last 30 days only

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / f"stj_{datetime.now():%Y%m}.log"

# Performance settings
DUCKDB_MEMORY_LIMIT = "4GB"  # DuckDB memory limit
DUCKDB_THREADS = 4  # Number of threads for DuckDB
CHUNK_SIZE = 10000  # Process records in chunks

# Schema monitoring
SCHEMA_VERSION = "1.0.0"
SCHEMA_CHECK_ENABLED = True
SCHEMA_FIELDS_EXPECTED = [
    "id",
    "numeroProcesso",
    "dataPublicacao",
    "dataJulgamento",
    "orgaoJulgador",
    "relator",
    "ementa",
    "textoIntegral"
]

def get_date_range_urls(start_date: datetime, end_date: datetime, orgao: str) -> list:
    """
    Gera URLs para download de JSONs em um período.

    STJ organiza por ano/mês, ex:
    - 2024/202401.json (Janeiro 2024)
    - 2024/202402.json (Fevereiro 2024)
    """
    urls = []
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

def get_mvp_urls() -> list:
    """
    Retorna URLs para MVP (últimos 30 dias, Corte Especial apenas).
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=MAX_DAYS_MVP)

    # Para MVP, pegar apenas Corte Especial (mais importante)
    return get_date_range_urls(start_date, end_date, "corte_especial")

def validar_configuracao_hibrida() -> bool:
    """
    Valida se a configuração híbrida está funcionando.

    Returns:
        bool: True se tudo OK, False se há problemas
    """
    errors = []

    # Verificar índices no SSD
    if not INDEX_PATH.exists():
        errors.append(f"❌ Diretório de índices não existe: {INDEX_PATH}")
    elif not os.access(INDEX_PATH, os.W_OK):
        errors.append(f"❌ Sem permissão de escrita em: {INDEX_PATH}")

    # Verificar HD externo
    if not DATA_ROOT.exists():
        errors.append(f"❌ Diretório de dados não existe: {DATA_ROOT}")
    elif not os.access(DATA_ROOT, os.W_OK):
        errors.append(f"❌ Sem permissão de escrita em: {DATA_ROOT}")

    # Verificar espaço disponível
    try:
        # SSD (índices)
        ssd_usage = shutil.disk_usage(INDEX_PATH)
        ssd_free_gb = ssd_usage.free / (1024**3)
        if ssd_free_gb < 5:
            errors.append(f"⚠️  SSD com pouco espaço: {ssd_free_gb:.1f}GB livres (mínimo: 5GB)")

        # HD (dados)
        hd_usage = shutil.disk_usage(DATA_ROOT)
        hd_free_gb = hd_usage.free / (1024**3)
        if hd_free_gb < 50:
            errors.append(f"⚠️  HD com pouco espaço: {hd_free_gb:.1f}GB livres (mínimo: 50GB)")
    except:
        errors.append("❌ Erro ao verificar espaço em disco")

    if errors:
        print("\n".join(errors))
        return False

    print(f"✅ Configuração híbrida validada:")
    print(f"   - Índices (SSD): {INDEX_PATH} ({ssd_free_gb:.1f}GB livres)")
    print(f"   - Dados (HD): {DATA_ROOT} ({hd_free_gb:.1f}GB livres)")
    return True

def get_storage_info() -> dict:
    """
    Retorna informações sobre armazenamento híbrido.

    Returns:
        dict: Informações de espaço e uso
    """
    info = {
        "ssd": {"path": str(INDEX_PATH), "free_gb": 0, "used_gb": 0},
        "hd": {"path": str(DATA_ROOT), "free_gb": 0, "used_gb": 0},
        "valid": False
    }

    try:
        # SSD
        ssd_usage = shutil.disk_usage(INDEX_PATH)
        info["ssd"]["free_gb"] = ssd_usage.free / (1024**3)
        info["ssd"]["used_gb"] = ssd_usage.used / (1024**3)

        # HD
        hd_usage = shutil.disk_usage(DATA_ROOT)
        info["hd"]["free_gb"] = hd_usage.free / (1024**3)
        info["hd"]["used_gb"] = hd_usage.used / (1024**3)

        info["valid"] = True
    except:
        pass

    return info
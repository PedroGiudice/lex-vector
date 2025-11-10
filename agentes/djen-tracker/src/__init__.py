"""
DJEN Tracker v1.0 - Monitor contínuo de cadernos DJEN

Download automático de cadernos de:
- STF (Supremo Tribunal Federal)
- STJ (Superior Tribunal de Justiça)
- TJSP 2ª Instância

Features:
- Download contínuo com rate limiting
- Checkpoint para resumir downloads
- Integração com oab-watcher para análise
"""

__version__ = "1.0.0"
__author__ = "PedroGiudice"

from .rate_limiter import RateLimiter
from .continuous_downloader import ContinuousDownloader, DownloadStatus

__all__ = [
    "RateLimiter",
    "ContinuousDownloader",
    "DownloadStatus",
    "__version__",
    "__author__",
]

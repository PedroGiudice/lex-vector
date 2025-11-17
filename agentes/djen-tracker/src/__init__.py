"""
DJEN Tracker v2.0 - Monitor contínuo de cadernos DJEN + Filtro OAB Profissional

Download automático de cadernos de:
- STF (Supremo Tribunal Federal)
- STJ (Superior Tribunal de Justiça)
- TJSP 2ª Instância
- 65 tribunais via MCP Server

Features v1.0:
- Download contínuo com rate limiting
- Checkpoint para resumir downloads
- Rate limiting inteligente com backoff

Features v2.0 (Filtro OAB Profissional):
- Detecção robusta de OABs (13+ padrões regex)
- Extração multi-estratégia (pdfplumber, PyPDF2, OCR)
- Cache inteligente com hash validation
- Scoring contextual de relevância
- Processamento paralelo em batch
- Exportação multi-formato (JSON, MD, TXT, Excel, HTML)
"""

__version__ = "2.0.0"
__author__ = "PedroGiudice / Claude Code"

# Legacy components
from .rate_limiter import RateLimiter
from .continuous_downloader import ContinuousDownloader, DownloadStatus
from .path_utils import get_data_root, get_agent_data_dir, resolve_config_paths

# New OAB filter components
from .oab_filter import OABFilter, PublicacaoMatch
from .pdf_text_extractor import PDFTextExtractor, ExtractionResult, ExtractionStrategy
from .cache_manager import CacheManager, CacheEntry, CacheStats
from .oab_matcher import OABMatcher, OABMatch
from .result_exporter import ResultExporter
from .parallel_processor import ParallelProcessor, ProcessingResult

__all__ = [
    # Legacy
    "RateLimiter",
    "ContinuousDownloader",
    "DownloadStatus",
    "get_data_root",
    "get_agent_data_dir",
    "resolve_config_paths",

    # New (filtro OAB profissional)
    "OABFilter",
    "PublicacaoMatch",
    "PDFTextExtractor",
    "ExtractionResult",
    "ExtractionStrategy",
    "CacheManager",
    "CacheEntry",
    "CacheStats",
    "OABMatcher",
    "OABMatch",
    "ResultExporter",
    "ParallelProcessor",
    "ProcessingResult",

    # Metadata
    "__version__",
    "__author__",
]

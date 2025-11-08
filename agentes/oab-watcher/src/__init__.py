"""
OAB Watcher v2.0 - Monitor de publicações DJEN com busca inteligente

Sistema híbrido com:
- Cache SQLite + gzip
- Filtro multi-camada (regex + estruturado)
- Paginação automática
- Scoring de relevância
"""

__version__ = "2.0.0"
__author__ = "PedroGiudice"

# Imports principais para uso externo
from .cache_manager import CacheManager
from .text_parser import TextParser, OABMatch
from .busca_inteligente import BuscaInteligente, ResultadoFiltro, Normalizador
from .busca_oab_v2 import BuscaOABv2
from .api_client import DJENClient
from .models import (
    Advogado,
    DestinatarioAdvogado,
    Destinatario,
    ComunicacaoOAB,
    RespostaBuscaOAB,
    CadernoTribunal,
)

__all__ = [
    # Core
    "CacheManager",
    "TextParser",
    "BuscaInteligente",
    "BuscaOABv2",
    "DJENClient",

    # Models
    "OABMatch",
    "ResultadoFiltro",
    "Normalizador",
    "Advogado",
    "DestinatarioAdvogado",
    "Destinatario",
    "ComunicacaoOAB",
    "RespostaBuscaOAB",
    "CadernoTribunal",

    # Metadata
    "__version__",
    "__author__",
]

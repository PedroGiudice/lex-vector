"""
Backend Proxy Services.

BFF layer for communicating with Docker backend services.
All API calls go through this layer - browser NEVER sees tokens.

Usage:
    from services import STJClient, quick_search

    # Context manager (recommended)
    async with STJClient() as client:
        results = await client.search(termo="responsabilidade civil")
        stats = await client.get_stats()

    # One-off calls
    results = await quick_search("responsabilidade civil", dias=180)
"""

from .stj_client import (
    # Client
    STJClient,

    # Exceptions
    STJClientError,
    STJConnectionError,
    STJTimeoutError,
    STJNotFoundError,
    STJValidationError,
    STJServerError,

    # Models
    AcordaoSummary,
    AcordaoDetail,
    SearchResponse,
    StatsResponse,
    SyncStatus,
    HealthResponse,
    ResultadoJulgamento,
    TipoDecisao,

    # Convenience functions
    quick_search,
    quick_health_check,

    # Config
    Config
)

__all__ = [
    # Client
    "STJClient",

    # Exceptions
    "STJClientError",
    "STJConnectionError",
    "STJTimeoutError",
    "STJNotFoundError",
    "STJValidationError",
    "STJServerError",

    # Models
    "AcordaoSummary",
    "AcordaoDetail",
    "SearchResponse",
    "StatsResponse",
    "SyncStatus",
    "HealthResponse",
    "ResultadoJulgamento",
    "TipoDecisao",

    # Convenience functions
    "quick_search",
    "quick_health_check",

    # Config
    "Config"
]

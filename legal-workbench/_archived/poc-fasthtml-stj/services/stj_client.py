"""
STJ Backend Proxy Client.

Backend-for-Frontend (BFF) proxy layer for STJ API.
All API calls to Docker backend services go through this layer.

Security:
- API tokens and credentials NEVER reach the browser
- All sensitive data stays server-side
- HTTP client with timeout and retry logic

Architecture:
    Browser (HTMX) <-> FastHTML BFF <-> [THIS LAYER] <-> STJ API (Docker)
"""
from __future__ import annotations

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------
# Configuration
# -----------------------

class Config:
    """STJ Client configuration from environment variables."""

    STJ_API_URL: str = os.getenv("STJ_API_URL", "http://lw-stj-api:8000")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    @classmethod
    def validate(cls):
        """Validate configuration on startup."""
        logger.info(f"STJ Client Config: URL={cls.STJ_API_URL}, Timeout={cls.REQUEST_TIMEOUT}s, Retries={cls.MAX_RETRIES}")


# -----------------------
# Custom Exceptions
# -----------------------

class STJClientError(Exception):
    """Base exception for STJ client errors."""
    pass


class STJConnectionError(STJClientError):
    """Connection to STJ API failed."""
    pass


class STJTimeoutError(STJClientError):
    """Request to STJ API timed out."""
    pass


class STJNotFoundError(STJClientError):
    """Resource not found (404)."""
    pass


class STJValidationError(STJClientError):
    """Request validation failed (422)."""
    pass


class STJServerError(STJClientError):
    """STJ API returned 5xx error."""
    pass


# -----------------------
# Data Models (matching API)
# -----------------------

class ResultadoJulgamento(str, Enum):
    """Resultado do julgamento."""
    PROVIMENTO = "provimento"
    PARCIAL_PROVIMENTO = "parcial_provimento"
    DESPROVIMENTO = "desprovimento"
    NAO_CONHECIDO = "nao_conhecido"
    INDETERMINADO = "indeterminado"


class TipoDecisao(str, Enum):
    """Tipo de decisão."""
    ACORDAO = "Acórdão"
    MONOCRATICA = "Decisão Monocrática"


class AcordaoSummary:
    """Summary of an acordão (search result)."""

    def __init__(self, **data):
        self.id: str = data.get("id", "")
        self.numero_processo: str = data.get("numero_processo", "")
        self.orgao_julgador: str = data.get("orgao_julgador", "")
        self.tipo_decisao: Optional[str] = data.get("tipo_decisao")
        self.relator: Optional[str] = data.get("relator")
        self.data_publicacao: Optional[datetime] = self._parse_datetime(data.get("data_publicacao"))
        self.data_julgamento: Optional[datetime] = self._parse_datetime(data.get("data_julgamento"))
        self.ementa: Optional[str] = data.get("ementa")
        self.resultado_julgamento: Optional[str] = data.get("resultado_julgamento")

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """Parse datetime from string or return as-is."""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class AcordaoDetail:
    """Full details of an acordão."""

    def __init__(self, **data):
        self.id: str = data.get("id", "")
        self.numero_processo: str = data.get("numero_processo", "")
        self.hash_conteudo: str = data.get("hash_conteudo", "")
        self.tribunal: str = data.get("tribunal", "")
        self.orgao_julgador: str = data.get("orgao_julgador", "")
        self.tipo_decisao: Optional[str] = data.get("tipo_decisao")
        self.classe_processual: Optional[str] = data.get("classe_processual")
        self.ementa: Optional[str] = data.get("ementa")
        self.texto_integral: Optional[str] = data.get("texto_integral")
        self.relator: Optional[str] = data.get("relator")
        self.resultado_julgamento: Optional[str] = data.get("resultado_julgamento")
        self.data_publicacao: Optional[datetime] = self._parse_datetime(data.get("data_publicacao"))
        self.data_julgamento: Optional[datetime] = self._parse_datetime(data.get("data_julgamento"))
        self.data_insercao: Optional[datetime] = self._parse_datetime(data.get("data_insercao"))
        self.assuntos: Optional[str] = data.get("assuntos")
        self.fonte: Optional[str] = data.get("fonte")
        self.fonte_url: Optional[str] = data.get("fonte_url")
        self.metadata: Optional[str] = data.get("metadata")

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """Parse datetime from string or return as-is."""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class SearchResponse:
    """Search response with pagination."""

    def __init__(self, total: int, limit: int, offset: int, resultados: List[Dict]):
        self.total = total
        self.limit = limit
        self.offset = offset
        self.resultados = [AcordaoSummary(**r) for r in resultados]


class StatsResponse:
    """Database statistics."""

    def __init__(self, **data):
        self.total_acordaos: int = data.get("total_acordaos", 0)
        self.por_orgao: Dict[str, int] = data.get("por_orgao", {})
        self.por_tipo: Dict[str, int] = data.get("por_tipo", {})
        self.periodo: Dict[str, Optional[datetime]] = data.get("periodo", {})
        self.tamanho_db_mb: float = data.get("tamanho_db_mb", 0.0)
        self.ultimos_30_dias: int = data.get("ultimos_30_dias", 0)


class SyncStatus:
    """Sync operation status."""

    def __init__(self, **data):
        self.status: str = data.get("status", "unknown")
        self.started_at: Optional[datetime] = self._parse_datetime(data.get("started_at"))
        self.completed_at: Optional[datetime] = self._parse_datetime(data.get("completed_at"))
        self.downloaded: int = data.get("downloaded", 0)
        self.processed: int = data.get("processed", 0)
        self.inserted: int = data.get("inserted", 0)
        self.duplicates: int = data.get("duplicates", 0)
        self.errors: int = data.get("errors", 0)
        self.message: Optional[str] = data.get("message")

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """Parse datetime from string or return as-is."""
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class HealthResponse:
    """Health check response."""

    def __init__(self, **data):
        self.status: str = data.get("status", "unknown")
        self.version: str = data.get("version", "unknown")
        self.database: str = data.get("database", "unknown")
        self.timestamp: datetime = self._parse_datetime(data.get("timestamp")) or datetime.now()

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


# -----------------------
# HTTP Client
# -----------------------

class STJClient:
    """
    Async HTTP client for STJ API backend service.

    Features:
    - Automatic retry with exponential backoff
    - Timeout handling
    - Error translation to custom exceptions
    - Connection pooling
    - Structured logging

    Usage:
        async with STJClient() as client:
            results = await client.search(termo="responsabilidade civil")
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        """
        Initialize STJ API client.

        Args:
            base_url: STJ API base URL (defaults to Config.STJ_API_URL)
            timeout: Request timeout in seconds (defaults to Config.REQUEST_TIMEOUT)
            max_retries: Maximum retry attempts (defaults to Config.MAX_RETRIES)
        """
        self.base_url = base_url or Config.STJ_API_URL
        self.timeout = timeout or Config.REQUEST_TIMEOUT
        self.max_retries = max_retries or Config.MAX_RETRIES
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(f"STJClient initialized: {self.base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _handle_error(self, response: httpx.Response, endpoint: str):
        """
        Translate HTTP errors to custom exceptions.

        Args:
            response: HTTP response object
            endpoint: Endpoint that was called

        Raises:
            STJNotFoundError: 404 response
            STJValidationError: 422 response
            STJServerError: 5xx response
            STJClientError: Other errors
        """
        status = response.status_code

        try:
            error_detail = response.json().get("detail", response.text)
        except Exception:
            error_detail = response.text

        error_msg = f"[{endpoint}] HTTP {status}: {error_detail}"

        if status == 404:
            raise STJNotFoundError(error_msg)
        elif status == 422:
            raise STJValidationError(error_msg)
        elif 500 <= status < 600:
            raise STJServerError(error_msg)
        else:
            raise STJClientError(error_msg)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Parsed JSON response

        Raises:
            STJConnectionError: Connection failed
            STJTimeoutError: Request timed out
            STJClientError: Other errors
        """
        if not self._client:
            raise STJClientError("Client not initialized. Use 'async with STJClient()' context manager.")

        try:
            logger.debug(f"{method} {endpoint} {kwargs}")
            response = await self._client.request(method, endpoint, **kwargs)

            if not response.is_success:
                self._handle_error(response, endpoint)

            return response.json()

        except httpx.ConnectError as e:
            logger.error(f"Connection error: {e}")
            raise STJConnectionError(f"Failed to connect to STJ API at {self.base_url}: {e}")

        except httpx.TimeoutException as e:
            logger.error(f"Timeout error: {e}")
            raise STJTimeoutError(f"Request to {endpoint} timed out after {self.timeout}s")

        except (STJClientError, STJNotFoundError, STJValidationError, STJServerError):
            # Re-raise custom exceptions
            raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            raise STJClientError(f"Unexpected error calling {endpoint}: {e}")

    # -----------------------
    # API Methods
    # -----------------------

    async def search(
        self,
        termo: str,
        orgao: Optional[str] = None,
        dias: int = 365,
        limit: int = 100,
        offset: int = 0,
        campo: str = "ementa"
    ) -> SearchResponse:
        """
        Search STJ jurisprudence.

        Args:
            termo: Search term (minimum 3 characters)
            orgao: Filter by órgão julgador (optional)
            dias: Search in last N days (default: 365)
            limit: Maximum results (default: 100, max: 1000)
            offset: Pagination offset (default: 0)
            campo: Field to search - "ementa" or "texto_integral" (default: "ementa")

        Returns:
            SearchResponse with paginated results

        Raises:
            STJValidationError: Invalid parameters
            STJServerError: Backend error

        Example:
            async with STJClient() as client:
                results = await client.search(
                    termo="responsabilidade civil",
                    orgao="TERCEIRA TURMA",
                    dias=180
                )
                print(f"Found {results.total} results")
        """
        if len(termo) < 3:
            raise STJValidationError("Search term must be at least 3 characters")

        if campo not in ["ementa", "texto_integral"]:
            raise STJValidationError("campo must be 'ementa' or 'texto_integral'")

        params = {
            "termo": termo,
            "dias": dias,
            "limit": limit,
            "offset": offset,
            "campo": campo
        }

        if orgao:
            params["orgao"] = orgao

        logger.info(f"Searching: termo={termo}, orgao={orgao}, dias={dias}, campo={campo}")

        data = await self._request("GET", "/api/v1/search", params=params)
        return SearchResponse(**data)

    async def get_case(self, case_id: str) -> AcordaoDetail:
        """
        Get full details of a case by ID.

        Args:
            case_id: Unique case identifier

        Returns:
            AcordaoDetail with full case information

        Raises:
            STJNotFoundError: Case not found
            STJServerError: Backend error

        Example:
            async with STJClient() as client:
                case = await client.get_case("abc123")
                print(case.ementa)
        """
        logger.info(f"Getting case: {case_id}")

        data = await self._request("GET", f"/api/v1/case/{case_id}")
        return AcordaoDetail(**data)

    async def get_stats(self) -> StatsResponse:
        """
        Get database statistics.

        Returns:
            StatsResponse with counts by órgão, tipo, date range, and DB size

        Raises:
            STJServerError: Backend error

        Example:
            async with STJClient() as client:
                stats = await client.get_stats()
                print(f"Total acordãos: {stats.total_acordaos}")
        """
        logger.info("Getting statistics")

        data = await self._request("GET", "/api/v1/stats")
        return StatsResponse(**data)

    async def trigger_sync(
        self,
        orgaos: Optional[List[str]] = None,
        dias: int = 30,
        force: bool = False
    ) -> SyncStatus:
        """
        Trigger data synchronization (runs in background).

        Downloads and processes new data from STJ Dados Abertos.
        Returns immediately with initial status.

        Args:
            orgaos: List of órgãos to sync (None = all)
            dias: Sync last N days (default: 30, max: 365)
            force: Force re-download of existing files (default: False)

        Returns:
            SyncStatus with initial status (status="running")

        Raises:
            STJServerError: Backend error

        Example:
            async with STJClient() as client:
                status = await client.trigger_sync(dias=7, force=True)
                print(f"Sync started: {status.message}")
        """
        logger.info(f"Triggering sync: orgaos={orgaos}, dias={dias}, force={force}")

        payload = {
            "orgaos": orgaos,
            "dias": dias,
            "force": force
        }

        data = await self._request("POST", "/api/v1/sync", json=payload)
        return SyncStatus(**data)

    async def get_sync_status(self) -> SyncStatus:
        """
        Get current sync status.

        Returns status of the last/current sync operation.

        Returns:
            SyncStatus with current sync information

        Raises:
            STJServerError: Backend error

        Example:
            async with STJClient() as client:
                status = await client.get_sync_status()
                if status.status == "running":
                    print(f"Sync in progress: {status.processed}/{status.downloaded}")
        """
        logger.info("Getting sync status")

        data = await self._request("GET", "/api/v1/sync/status")
        return SyncStatus(**data)

    async def health_check(self) -> HealthResponse:
        """
        Health check endpoint.

        Returns API status and database connectivity.

        Returns:
            HealthResponse with status information

        Raises:
            STJConnectionError: Cannot connect to API

        Example:
            async with STJClient() as client:
                health = await client.health_check()
                print(f"API status: {health.status}, DB: {health.database}")
        """
        logger.info("Health check")

        data = await self._request("GET", "/health")
        return HealthResponse(**data)


# -----------------------
# Module Initialization
# -----------------------

# Validate config on import
Config.validate()


# -----------------------
# Convenience Functions
# -----------------------

async def quick_search(termo: str, **kwargs) -> SearchResponse:
    """
    Quick search without context manager.

    Convenience function for one-off searches.
    For multiple calls, use STJClient context manager.

    Args:
        termo: Search term
        **kwargs: Additional search parameters

    Returns:
        SearchResponse
    """
    async with STJClient() as client:
        return await client.search(termo, **kwargs)


async def quick_health_check() -> HealthResponse:
    """
    Quick health check without context manager.

    Returns:
        HealthResponse
    """
    async with STJClient() as client:
        return await client.health_check()

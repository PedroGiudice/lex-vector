"""
STJ Dados Abertos API - FastAPI application.

REST API for querying STJ jurisprudence database.

Endpoints:
- GET  /api/v1/search         - Search jurisprudence
- GET  /api/v1/case/{id}      - Get case details
- POST /api/v1/sync           - Force sync
- GET  /api/v1/stats          - Database statistics
- GET  /health                - Health check
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add backend path to sys.path
BACKEND_PATH = Path(__file__).parent.parent.parent.parent / "ferramentas/stj-dados-abertos"
sys.path.insert(0, str(BACKEND_PATH))

from src.database import STJDatabase
from api import __version__
from api.models import (
    SearchRequest,
    SearchResponse,
    AcordaoSummary,
    AcordaoDetail,
    StatsResponse,
    SyncRequest,
    SyncStatus,
    HealthResponse
)
from api.dependencies import get_database, close_database, get_cache, invalidate_cache
from api.scheduler import start_scheduler, stop_scheduler, run_sync_task, get_sync_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="STJ Dados Abertos API",
    description="REST API para consulta de jurisprudência do STJ",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("Starting STJ API")

    # Initialize database connection
    db = next(get_database())
    logger.info("Database connection initialized")

    # Start background scheduler
    start_scheduler()
    logger.info("Background scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    logger.info("Shutting down STJ API")

    # Stop scheduler
    stop_scheduler()

    # Close database
    close_database()
    logger.info("Resources cleaned up")


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: STJDatabase = Depends(get_database)):
    """
    Health check endpoint.

    Returns API status and database connectivity.
    """
    try:
        # Test database connection
        stats = db.obter_estatisticas()
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        version=__version__,
        database=db_status,
        timestamp=datetime.now()
    )


# Search endpoint (GET with query params)
@app.get("/api/v1/search", response_model=SearchResponse, tags=["Search"])
async def search_jurisprudence(
    termo: str = Query(..., description="Termo para buscar", min_length=3),
    orgao: Optional[str] = Query(None, description="Órgão julgador para filtrar"),
    dias: int = Query(365, description="Buscar nos últimos N dias", ge=1, le=3650),
    limit: int = Query(100, description="Máximo de resultados", ge=1, le=1000),
    offset: int = Query(0, description="Offset para paginação", ge=0),
    campo: str = Query("ementa", description="Campo para buscar (ementa ou texto_integral)"),
    db: STJDatabase = Depends(get_database)
):
    """
    Search jurisprudence by term.

    Searches in ementa (default) or texto_integral fields.
    Supports filtering by órgão julgador and date range.
    Results are paginated.

    Args:
        termo: Search term (minimum 3 characters)
        orgao: Filter by órgão julgador (optional)
        dias: Search in last N days (default: 365)
        limit: Maximum results (default: 100, max: 1000)
        offset: Pagination offset (default: 0)
        campo: Field to search (ementa or texto_integral)

    Returns:
        SearchResponse with paginated results
    """
    try:
        logger.info(f"Search: termo={termo}, orgao={orgao}, dias={dias}, campo={campo}")

        # Check cache
        cache = get_cache()
        cache_key = f"search:{termo}:{orgao}:{dias}:{limit}:{offset}:{campo}"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info("Cache hit")
            return cached_result

        # Search based on field
        if campo == "ementa":
            results = db.buscar_ementa(termo, orgao, dias, limit + offset)
        else:  # texto_integral
            results = db.buscar_acordao(termo, orgao, dias, limit + offset)

        # Apply pagination
        total = len(results)
        paginated_results = results[offset:offset + limit]

        # Convert to response model
        acordaos = [AcordaoSummary(**r) for r in paginated_results]

        response = SearchResponse(
            total=total,
            limit=limit,
            offset=offset,
            resultados=acordaos
        )

        # Cache result
        cache.set(cache_key, response)

        logger.info(f"Search completed: {total} results")
        return response

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


# Get case by ID
@app.get("/api/v1/case/{case_id}", response_model=AcordaoDetail, tags=["Cases"])
async def get_case_details(
    case_id: str,
    db: STJDatabase = Depends(get_database)
):
    """
    Get full details of a case by ID.

    Args:
        case_id: Unique case identifier

    Returns:
        AcordaoDetail with full case information
    """
    try:
        logger.info(f"Getting case details: {case_id}")

        # Check cache
        cache = get_cache()
        cache_key = f"case:{case_id}"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info("Cache hit")
            return cached_result

        # Query database
        query = "SELECT * FROM acordaos WHERE id = ?"
        result = db.conn.execute(query, [case_id]).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Caso não encontrado")

        # Convert to dict
        columns = [desc[0] for desc in db.conn.execute(query, [case_id]).description]
        case_dict = dict(zip(columns, result))

        # Convert to response model
        case_detail = AcordaoDetail(**case_dict)

        # Cache result
        cache.set(cache_key, case_detail)

        logger.info(f"Case details retrieved: {case_id}")
        return case_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao buscar caso: {str(e)}")


# Get statistics
@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_statistics(db: STJDatabase = Depends(get_database)):
    """
    Get database statistics.

    Returns counts by órgão, tipo, date range, and database size.
    """
    try:
        logger.info("Getting statistics")

        # Check cache
        cache = get_cache()
        cache_key = "stats"
        cached_result = cache.get(cache_key)

        if cached_result:
            logger.info("Cache hit")
            return cached_result

        # Get stats from database
        stats = db.obter_estatisticas()

        response = StatsResponse(**stats)

        # Cache result (shorter TTL for stats)
        cache.set(cache_key, response)

        logger.info("Statistics retrieved")
        return response

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


# Sync endpoint
@app.post("/api/v1/sync", response_model=SyncStatus, tags=["Sync"])
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger data synchronization.

    Downloads and processes new data from STJ Dados Abertos.
    Runs in background and returns immediately.

    Args:
        request: SyncRequest with orgaos, dias, and force options

    Returns:
        SyncStatus with current sync status
    """
    try:
        logger.info(f"Sync requested: orgaos={request.orgaos}, dias={request.dias}, force={request.force}")

        # Check if sync is already running
        status = get_sync_status()
        if status["status"] == "running":
            logger.warning("Sync already running")
            return SyncStatus(**status)

        # Run sync in background
        background_tasks.add_task(
            run_sync_task,
            orgaos=request.orgaos,
            dias=request.dias,
            force=request.force
        )

        # Return initial status
        return SyncStatus(
            status="running",
            started_at=datetime.now(),
            message="Sync started in background"
        )

    except Exception as e:
        logger.error(f"Failed to trigger sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar sincronização: {str(e)}")


# Get sync status
@app.get("/api/v1/sync/status", response_model=SyncStatus, tags=["Sync"])
async def get_sync_status_endpoint():
    """
    Get current sync status.

    Returns status of the last/current sync operation.
    """
    try:
        status = get_sync_status()
        return SyncStatus(**status)

    except Exception as e:
        logger.error(f"Failed to get sync status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro ao obter status de sincronização: {str(e)}")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "message": "STJ Dados Abertos API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

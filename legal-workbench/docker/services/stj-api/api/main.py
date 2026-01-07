"""
STJ Dados Abertos API - FastAPI application.

REST API for querying STJ jurisprudence database.

Endpoints:
- GET  /api/v1/search         - Search jurisprudence
- GET  /api/v1/case/{id}      - Get case details
- POST /api/v1/sync           - Force sync
- GET  /api/v1/stats          - Database statistics
- GET  /health                - Health check
- GET  /debug/sentry          - Sentry test endpoint
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path

# Add shared module path for logging and Sentry
sys.path.insert(0, '/app')

# Initialize Sentry BEFORE importing FastAPI for proper instrumentation
try:
    from shared.sentry_config import init_sentry
    init_sentry("stj-api")
except ImportError:
    pass  # Sentry not available, continue without it

# Configure structured JSON logging
from shared.logging_config import setup_logging
from shared.middleware import RequestIDMiddleware

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logger = setup_logging("stj-api", level=log_level)

from datetime import datetime
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

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
    HealthResponse,
    ExportRequest,
    ExportFormat
)
from api.dependencies import get_database, close_database, get_cache, invalidate_cache
from api.scheduler import start_scheduler, stop_scheduler, run_sync_task, get_sync_status

# Initialize FastAPI app
app = FastAPI(
    title="STJ Dados Abertos API",
    description="REST API para consulta de jurisprudência do STJ",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request ID middleware for request tracing
app.add_middleware(RequestIDMiddleware)

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
    logger.info("Service starting", extra={"event": "startup", "version": __version__})

    # Initialize database connection
    db = next(get_database())
    logger.info("Database connection initialized", extra={"event": "db_init"})

    # Start background scheduler
    start_scheduler()
    logger.info("Background scheduler started", extra={"event": "scheduler_start"})


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    logger.info("Service shutting down", extra={"event": "shutdown"})

    # Stop scheduler
    stop_scheduler()

    # Close database
    close_database()
    logger.info("Resources cleaned up", extra={"event": "cleanup_complete"})


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

    Supports two modes:
    - By days: Use 'dias' parameter (1-1500) to sync last N days
    - By start date: Use 'data_inicio' (ISO format YYYY-MM-DD) as alternative

    Args:
        request: SyncRequest with orgaos, dias/data_inicio, and force options

    Returns:
        SyncStatus with current sync status
    """
    try:
        # Calculate effective dias from data_inicio if provided
        effective_dias = request.dias
        if request.data_inicio:
            try:
                start_date = datetime.strptime(request.data_inicio, "%Y-%m-%d")
                delta = datetime.now() - start_date
                effective_dias = max(1, delta.days)
                # Cap at 1500 days for safety
                if effective_dias > 1500:
                    effective_dias = 1500
                    logger.warning(f"data_inicio resulted in {delta.days} days, capped to 1500")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Formato de data inválido: {str(e)}")

        logger.info(f"Sync requested: orgaos={request.orgaos}, dias={effective_dias}, data_inicio={request.data_inicio}, force={request.force}")

        # Check if sync is already running
        status = get_sync_status()
        if status["status"] == "running":
            logger.warning("Sync already running")
            return SyncStatus(**status)

        # Run sync in background
        background_tasks.add_task(
            run_sync_task,
            orgaos=request.orgaos,
            dias=effective_dias,
            force=request.force
        )

        # Return initial status
        return SyncStatus(
            status="running",
            started_at=datetime.now(),
            message=f"Sync started in background (dias={effective_dias})"
        )

    except HTTPException:
        raise
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


# Export endpoint
@app.post("/api/v1/export", tags=["Export"])
async def export_results(
    request: ExportRequest,
    db: STJDatabase = Depends(get_database)
):
    """
    Export search results as downloadable file.

    Searches jurisprudence and returns results as JSON or CSV file.
    Supports mass retroactive downloads with date ranges up to 1500 days.

    Args:
        request: ExportRequest with termo, formato, dias, orgao, campo

    Returns:
        StreamingResponse with file download (Content-Disposition attachment)
    """
    import csv
    import json
    import io

    try:
        logger.info(f"Export requested: termo={request.termo}, formato={request.formato}, dias={request.dias}, orgao={request.orgao}")

        # Search based on field
        if request.campo == "ementa":
            results = db.buscar_ementa(request.termo, request.orgao, request.dias, limit=10000)
        else:  # texto_integral
            results = db.buscar_acordao(request.termo, request.orgao, request.dias, limit=10000)

        if not results:
            raise HTTPException(status_code=404, detail="Nenhum resultado encontrado para exportação")

        logger.info(f"Export: found {len(results)} results")

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        termo_safe = "".join(c if c.isalnum() else "_" for c in request.termo[:20])

        if request.formato == ExportFormat.CSV:
            # Generate CSV
            output = io.StringIO()
            fieldnames = ["numero_processo", "relator", "orgao_julgador", "data_julgamento", "ementa"]
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for row in results:
                # Format date if present
                row_copy = dict(row)
                if row_copy.get("data_julgamento"):
                    if hasattr(row_copy["data_julgamento"], "strftime"):
                        row_copy["data_julgamento"] = row_copy["data_julgamento"].strftime("%Y-%m-%d")
                writer.writerow(row_copy)

            content = output.getvalue()
            output.close()

            filename = f"stj_export_{termo_safe}_{timestamp}.csv"
            media_type = "text/csv"

            return StreamingResponse(
                iter([content]),
                media_type=media_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "X-Total-Records": str(len(results))
                }
            )

        else:  # JSON format
            # Full acordao data for JSON
            content = json.dumps({
                "termo": request.termo,
                "total": len(results),
                "exported_at": datetime.now().isoformat(),
                "dias": request.dias,
                "orgao": request.orgao,
                "resultados": results
            }, indent=2, default=str, ensure_ascii=False)

            filename = f"stj_export_{termo_safe}_{timestamp}.json"
            media_type = "application/json"

            return StreamingResponse(
                iter([content]),
                media_type=media_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "X-Total-Records": str(len(results))
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro na exportação: {str(e)}")


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


# Sentry debug endpoint
@app.get("/debug/sentry", tags=["Debug"])
async def debug_sentry():
    """
    Test Sentry integration by triggering a test exception.

    This endpoint is for debugging purposes only.
    In production, this should be disabled or protected.
    """
    raise Exception("Sentry test exception from stj-api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

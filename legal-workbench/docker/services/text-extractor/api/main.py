"""FastAPI application for Text Extractor service."""
import os
import uuid
import aiosqlite
import tempfile
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import RedirectResponse, JSONResponse
from celery.result import AsyncResult
import redis.asyncio as aioredis

from .models import (
    ExtractionRequest,
    ExtractionResponse,
    JobStatusResponse,
    ExtractionResult,
    HealthResponse,
    JobStatus,
    EngineType
)

# Environment variables
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
JOBS_DB_PATH = os.getenv("JOBS_DB_PATH", "/app/data/jobs.db")

# Global Redis connection
redis_client: Optional[aioredis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global redis_client

    # Startup: Initialize database and Redis
    await init_db()
    redis_client = await aioredis.from_url(CELERY_BROKER_URL, decode_responses=True)

    yield

    # Shutdown: Close connections
    if redis_client:
        await redis_client.close()


# Create FastAPI app
app = FastAPI(
    title="Text Extractor API",
    description="PDF text extraction service with Marker and pdfplumber engines",
    version="1.0.0",
    lifespan=lifespan
)


async def init_db():
    """Initialize SQLite database for job tracking."""
    db_path = Path(JOBS_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(JOBS_DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                engine TEXT NOT NULL,
                use_gemini INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                progress REAL DEFAULT 0.0,
                error_message TEXT,
                result_text TEXT,
                pages_processed INTEGER,
                execution_time REAL,
                metadata TEXT
            )
        """)
        await db.commit()


async def save_job(job_id: str, engine: str, use_gemini: bool):
    """Save new job to database."""
    async with aiosqlite.connect(JOBS_DB_PATH) as db:
        await db.execute(
            """INSERT INTO jobs (job_id, status, engine, use_gemini, created_at, progress)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (job_id, JobStatus.QUEUED.value, engine, int(use_gemini),
             datetime.utcnow().isoformat(), 0.0)
        )
        await db.commit()


async def update_job_status(job_id: str, status: JobStatus, **kwargs):
    """Update job status in database."""
    fields = ["status = ?"]
    values = [status.value]

    for key, value in kwargs.items():
        fields.append(f"{key} = ?")
        values.append(value)

    values.append(job_id)

    async with aiosqlite.connect(JOBS_DB_PATH) as db:
        await db.execute(
            f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?",
            values
        )
        await db.commit()


async def get_job(job_id: str) -> Optional[dict]:
    """Retrieve job from database."""
    async with aiosqlite.connect(JOBS_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    dependencies = {}

    # Check Redis connection
    try:
        if redis_client:
            await redis_client.ping()
            dependencies["redis"] = "connected"
        else:
            dependencies["redis"] = "not_initialized"
    except Exception as e:
        dependencies["redis"] = f"error: {str(e)}"

    # Check Celery (basic check via Redis)
    try:
        # Import here to avoid circular dependency
        from celery_worker import celery_app
        inspector = celery_app.control.inspect()
        active = inspector.active()
        dependencies["celery"] = "running" if active else "no_workers"
    except Exception as e:
        dependencies["celery"] = f"error: {str(e)}"

    # Check database
    try:
        async with aiosqlite.connect(JOBS_DB_PATH) as db:
            await db.execute("SELECT 1")
        dependencies["database"] = "connected"
    except Exception as e:
        dependencies["database"] = f"error: {str(e)}"

    overall_status = "healthy" if all(
        "error" not in v and v in ["connected", "running"]
        for v in dependencies.values()
    ) else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        dependencies=dependencies
    )


@app.post("/api/v1/extract", response_model=ExtractionResponse, status_code=202)
async def extract_text(
    file: Optional[UploadFile] = File(None),
    file_base64: Optional[str] = Form(None),
    engine: EngineType = Form(EngineType.MARKER),
    use_gemini: bool = Form(False),
    options: Optional[str] = Form(None)
):
    """
    Submit a PDF extraction job.

    Accepts either:
    - Multipart file upload (file parameter)
    - Base64 encoded file (file_base64 parameter)
    """
    # Validate input
    if not file and not file_base64:
        raise HTTPException(
            status_code=400,
            detail="Either 'file' or 'file_base64' must be provided"
        )

    if file and file_base64:
        raise HTTPException(
            status_code=400,
            detail="Provide only one of 'file' or 'file_base64'"
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save file to temp location
    temp_file = None
    try:
        if file:
            # Handle multipart upload
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            content = await file.read()
            temp_file.write(content)
            temp_file.close()
            temp_path = temp_file.name
        else:
            # Handle base64 upload
            try:
                content = base64.b64decode(file_base64)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid base64 encoding")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(content)
            temp_file.close()
            temp_path = temp_file.name

        # Parse options if provided
        import json
        parsed_options = {}
        if options:
            try:
                parsed_options = json.loads(options)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON in options")

        # Save job to database
        await save_job(job_id, engine.value, use_gemini)

        # Queue Celery task
        from celery_worker import extract_pdf
        task = extract_pdf.apply_async(
            args=[job_id, temp_path, engine.value, use_gemini, parsed_options],
            task_id=job_id
        )

        # NOTE: Temp file cleanup is handled by the Celery worker in its finally block
        # Do NOT cleanup here - causes race condition where file is deleted before worker reads it

        return ExtractionResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=datetime.utcnow(),
            estimated_completion=300  # 5 minutes estimate
        )

    except HTTPException:
        # Cleanup on validation errors
        if temp_file and os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise
    except Exception as e:
        # Cleanup on unexpected errors
        if temp_file and os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise HTTPException(status_code=500, detail=f"Job submission failed: {str(e)}")


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get the status of an extraction job."""
    job = await get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result_url = None
    if job["status"] == JobStatus.COMPLETED.value:
        result_url = f"/api/v1/jobs/{job_id}/result"

    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        progress=job["progress"],
        result_url=result_url,
        error_message=job["error_message"],
        created_at=datetime.fromisoformat(job["created_at"]),
        started_at=datetime.fromisoformat(job["started_at"]) if job["started_at"] else None,
        completed_at=datetime.fromisoformat(job["completed_at"]) if job["completed_at"] else None
    )


@app.get("/api/v1/jobs/{job_id}/result", response_model=ExtractionResult)
async def get_job_result(job_id: str):
    """Get the result of a completed extraction job."""
    job = await get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Job is not completed yet. Current status: {job['status']}"
        )

    # Parse metadata if present
    import json
    metadata = None
    if job["metadata"]:
        try:
            metadata = json.loads(job["metadata"])
        except json.JSONDecodeError:
            pass

    return ExtractionResult(
        job_id=job_id,
        text=job["result_text"] or "",
        pages_processed=job["pages_processed"] or 0,
        execution_time_seconds=job["execution_time"] or 0.0,
        engine_used=EngineType(job["engine"]),
        gemini_enhanced=bool(job["use_gemini"]),
        metadata=metadata
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

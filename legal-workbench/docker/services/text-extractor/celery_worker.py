"""Celery worker for PDF text extraction."""
import os
import signal
import time
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from celery import Celery, Task
from celery.signals import task_prerun, task_postrun, task_failure

# Configure logger
logger = logging.getLogger("celery_worker")
log_level = logging.DEBUG if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG" else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# Environment variables
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
JOBS_DB_PATH = os.getenv("JOBS_DB_PATH", "/app/data/jobs.db")
MARKER_CACHE_DIR = os.getenv("MARKER_CACHE_DIR", "/app/cache")
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "2"))
JOB_TIMEOUT_SECONDS = int(os.getenv("JOB_TIMEOUT_SECONDS", "600"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Create Celery app
celery_app = Celery(
    "text_extractor",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=MAX_CONCURRENT_JOBS,
    task_time_limit=JOB_TIMEOUT_SECONDS,
    task_soft_time_limit=JOB_TIMEOUT_SECONDS - 30,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,  # 1 hour
)

class MarkerTimeoutError(Exception):
    """Raised when Marker extraction exceeds timeout."""
    pass


def marker_timeout_handler(signum, frame):
    """Handle timeout signal for Marker extraction."""
    raise MarkerTimeoutError("Marker extraction timed out after 5 minutes")


# Singleton for Marker model artifacts (lazy loading)
_marker_artifacts = None


def get_marker_artifacts():
    """Get or initialize Marker model artifacts (singleton pattern)."""
    global _marker_artifacts

    if _marker_artifacts is None:
        try:
            from marker.models import create_model_dict
            logger.info("Loading Marker models... (this may take a while)")
            _marker_artifacts = create_model_dict()
            logger.info("Marker models loaded successfully")
        except Exception as e:
            logger.error("Failed to load Marker models: %s", e)
            raise

    return _marker_artifacts


def update_job_db(job_id: str, **fields):
    """Update job in SQLite database."""
    db_path = Path(JOBS_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    set_clause = ", ".join(f"{key} = ?" for key in fields.keys())
    values = list(fields.values()) + [job_id]

    with sqlite3.connect(JOBS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE jobs SET {set_clause} WHERE job_id = ?",
            values
        )
        conn.commit()


def save_job_log(job_id: str, level: str, message: str):
    """Save log entry to job_logs table."""
    db_path = Path(JOBS_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(JOBS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO job_logs (job_id, timestamp, level, message) VALUES (?, ?, ?, ?)",
            (job_id, datetime.utcnow().isoformat(), level, message)
        )
        conn.commit()


def extract_with_marker(pdf_path: str, options: Dict[str, Any]) -> tuple[str, int, Dict]:
    """Extract text using Marker engine with optimized config."""
    try:
        from marker.converters.pdf import PdfConverter
        from marker.config.parser import ConfigParser
        from marker.output import text_from_rendered

        # Get Marker model artifacts
        artifact_dict = get_marker_artifacts()

        logger.info("Starting Marker extraction for: %s", pdf_path)

        # OTIMIZACAO: Config igual ao marker_engine.py
        config_dict = {
            "output_format": "markdown",
            "paginate_output": True,
            "disable_image_extraction": True,  # CRITICO: evita 80MB de base64
            "disable_links": True,
            "drop_repeated_text": True,
            "keep_pageheader_in_output": False,
            "keep_pagefooter_in_output": False,
        }

        logger.debug("Marker config: %s", config_dict)
        logger.debug("PDF path: %s, size: %d bytes", pdf_path, os.path.getsize(pdf_path))

        # Create config parser
        config_parser = ConfigParser(config_dict)

        # Create converter with optimized config
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )

        # Set timeout for Marker extraction (5 minutes)
        MARKER_TIMEOUT = 300
        original_handler = signal.signal(signal.SIGALRM, marker_timeout_handler)
        signal.alarm(MARKER_TIMEOUT)

        try:
            # Convert PDF
            rendered = converter(pdf_path)
        finally:
            # Always restore original handler and cancel alarm
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)

        # Extract text from rendered output
        full_text = rendered.markdown if hasattr(rendered, 'markdown') else ""

        # Fallback for older Marker API
        if not full_text:
            full_text, _, images = text_from_rendered(rendered)

        # Get metadata from rendered document
        pages_processed = len(rendered.children) if hasattr(rendered, 'children') else 1

        extraction_metadata = {
            "ocr_applied": True,
            "file_size_bytes": os.path.getsize(pdf_path),
            "config_applied": config_dict,
        }

        logger.info("Marker extraction completed: %d pages", pages_processed)

        return full_text, pages_processed, extraction_metadata

    except Exception as e:
        logger.error("Marker extraction failed: %s", e)
        raise


def extract_with_pdfplumber(pdf_path: str, options: Dict[str, Any]) -> tuple[str, int, Dict]:
    """Extract text using pdfplumber engine."""
    try:
        import pdfplumber

        logger.info("Starting pdfplumber extraction")

        extracted_text = []
        pages_processed = 0

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                pages_processed += 1

        full_text = "\n\n".join(extracted_text)

        extraction_metadata = {
            "file_size_bytes": os.path.getsize(pdf_path),
            "ocr_applied": False
        }

        logger.info("pdfplumber extraction completed: %d pages", pages_processed)

        return full_text, pages_processed, extraction_metadata

    except Exception as e:
        logger.error("pdfplumber extraction failed: %s", e)
        raise


def enhance_with_gemini(text: str, options: Dict[str, Any]) -> str:
    """Post-process extracted text with Gemini."""
    if not GEMINI_API_KEY:
        logger.info("Gemini API key not configured, skipping enhancement")
        return text

    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-pro')

        prompt = options.get("gemini_prompt", """
        Clean and improve the following extracted text from a PDF document.
        Fix OCR errors, improve formatting, and maintain the original structure.
        Return only the cleaned text without any additional commentary.

        Text:
        {text}
        """).format(text=text[:8000])  # Limit to avoid token limits

        logger.info("Enhancing text with Gemini...")

        response = model.generate_content(prompt)
        enhanced_text = response.text

        logger.info("Gemini enhancement completed")

        return enhanced_text

    except Exception as e:
        logger.warning("Gemini enhancement failed: %s, returning original text", e)
        return text


class ExtractionTask(Task):
    """Custom task class with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        job_id = task_id
        error_msg = str(exc)[:500]  # Limit error message length

        logger.error("Task %s failed: %s", job_id, error_msg)

        update_job_db(
            job_id,
            status="failed",
            error_message=error_msg,
            completed_at=datetime.utcnow().isoformat()
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info("Task %s completed successfully", task_id)


@celery_app.task(
    bind=True,
    base=ExtractionTask,
    name="extract_pdf",
    time_limit=JOB_TIMEOUT_SECONDS,
    soft_time_limit=JOB_TIMEOUT_SECONDS - 30
)
def extract_pdf(
    self,
    job_id: str,
    pdf_path: str,
    engine: str,
    use_gemini: bool,
    options: Optional[Dict[str, Any]] = None
):
    """
    Extract text from PDF file.

    Args:
        job_id: Unique job identifier
        pdf_path: Path to PDF file
        engine: Extraction engine ('marker' or 'pdfplumber')
        use_gemini: Whether to use Gemini for post-processing
        options: Engine-specific options
    """
    if options is None:
        options = {}

    start_time = time.time()

    try:
        # Update job status to processing
        update_job_db(
            job_id,
            status="processing",
            started_at=datetime.utcnow().isoformat(),
            progress=0.0
        )
        save_job_log(job_id, "INFO", f"Job started with engine: {engine}")

        logger.info("Processing job %s with engine: %s", job_id, engine)

        # Validate PDF exists
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        save_job_log(job_id, "INFO", f"File validated: {pdf_path}")

        # Update progress
        update_job_db(job_id, progress=10.0)

        # Extract text based on engine
        if engine == "marker":
            full_text, pages_processed, metadata = extract_with_marker(pdf_path, options)
        elif engine == "pdfplumber":
            full_text, pages_processed, metadata = extract_with_pdfplumber(pdf_path, options)
        else:
            raise ValueError(f"Unknown engine: {engine}")
        save_job_log(job_id, "INFO", f"Extraction completed: {pages_processed} pages")

        # Update progress
        update_job_db(job_id, progress=70.0)

        # Optional Gemini enhancement
        if use_gemini:
            full_text = enhance_with_gemini(full_text, options)
            metadata["gemini_enhanced"] = True

        # Update progress
        update_job_db(job_id, progress=90.0)

        # Calculate execution time
        execution_time = time.time() - start_time

        # Update job with results
        update_job_db(
            job_id,
            status="completed",
            progress=100.0,
            result_text=full_text,
            pages_processed=pages_processed,
            execution_time=execution_time,
            completed_at=datetime.utcnow().isoformat(),
            metadata=json.dumps(metadata)
        )

        logger.info("Job %s completed in %.2fs", job_id, execution_time)

        return {
            "job_id": job_id,
            "status": "completed",
            "pages_processed": pages_processed,
            "execution_time": execution_time
        }

    except Exception as e:
        # Error handling is done by on_failure
        save_job_log(job_id, "ERROR", f"Job failed: {str(e)[:200]}")
        logger.error("Job %s failed with error: %s", job_id, e)
        raise

    finally:
        # Cleanup temporary file
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                logger.debug("Cleaned up temporary file: %s", pdf_path)
        except Exception as e:
            logger.warning("Failed to cleanup temporary file: %s", e)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Handle task prerun signal."""
    logger.info("Task %s starting: %s", task_id, task.name)


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Handle task postrun signal."""
    logger.info("Task %s finished: %s", task_id, task.name)


if __name__ == "__main__":
    # Run worker
    celery_app.worker_main([
        "worker",
        "--loglevel=info",
        f"--concurrency={MAX_CONCURRENT_JOBS}",
        "--pool=solo"  # Use solo pool for compatibility
    ])

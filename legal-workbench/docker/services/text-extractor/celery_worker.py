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
JOB_TIMEOUT_SECONDS = int(os.getenv("JOB_TIMEOUT_SECONDS", "2100"))  # 35 minutes for large PDFs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Marker-specific timeout (30 minutes for CPU-only processing of large legal documents)
MARKER_TIMEOUT = int(os.getenv("MARKER_TIMEOUT", "1800"))

# Modal GPU acceleration
MODAL_ENABLED = os.getenv("MODAL_ENABLED", "false").lower() == "true"
MODAL_TOKEN_ID = os.getenv("MODAL_TOKEN_ID")
MODAL_TOKEN_SECRET = os.getenv("MODAL_TOKEN_SECRET")

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
    raise MarkerTimeoutError(f"Marker extraction timed out after {MARKER_TIMEOUT} seconds")


# Singleton for Marker model artifacts (lazy loading)
_marker_artifacts = None


def get_marker_artifacts():
    """Get or initialize Marker model artifacts (singleton pattern)."""
    global _marker_artifacts

    if _marker_artifacts is None:
        try:
            from marker.models import create_model_dict

            # Log environment config for debugging
            torch_device = os.getenv("TORCH_DEVICE", "auto")
            detector_batch = os.getenv("DETECTOR_BATCH_SIZE", "default")
            recognition_batch = os.getenv("RECOGNITION_BATCH_SIZE", "default")

            logger.info("Loading Marker models...")
            logger.info("  TORCH_DEVICE=%s", torch_device)
            logger.info("  DETECTOR_BATCH_SIZE=%s", detector_batch)
            logger.info("  RECOGNITION_BATCH_SIZE=%s", recognition_batch)
            logger.info("  MARKER_TIMEOUT=%s seconds", MARKER_TIMEOUT)
            logger.info("This may take several minutes on CPU...")

            start_time = time.time()
            _marker_artifacts = create_model_dict()
            load_time = time.time() - start_time

            logger.info("Marker models loaded successfully in %.1f seconds", load_time)
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

        pdf_size = os.path.getsize(pdf_path)
        logger.info("PDF file: %s", pdf_path)
        logger.info("PDF size: %.2f MB", pdf_size / (1024 * 1024))
        logger.debug("Marker config: %s", config_dict)

        # Create config parser
        config_parser = ConfigParser(config_dict)

        # Create converter with optimized config
        logger.info("Creating PDF converter...")
        converter = PdfConverter(
            config=config_parser.generate_config_dict(),
            artifact_dict=artifact_dict,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
        )

        # Set timeout for Marker extraction
        logger.info("Starting extraction with %d second timeout...", MARKER_TIMEOUT)
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


def extract_with_modal(pdf_path: str, options: Dict[str, Any]) -> tuple[str, int, Dict]:
    """
    Extract text using Modal GPU-accelerated Marker.

    Requires:
    - MODAL_ENABLED=true
    - MODAL_TOKEN_ID and MODAL_TOKEN_SECRET set
    - modal package installed

    Falls back to local Marker if Modal fails.
    """
    if not MODAL_ENABLED:
        raise RuntimeError("Modal is not enabled")

    if not MODAL_TOKEN_ID or not MODAL_TOKEN_SECRET:
        raise RuntimeError("Modal tokens not configured (MODAL_TOKEN_ID, MODAL_TOKEN_SECRET)")

    try:
        import modal

        logger.info("Starting Modal GPU extraction for: %s", pdf_path)

        # Read PDF file
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()

        pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
        logger.info("PDF size: %.2f MB, sending to Modal GPU...", pdf_size_mb)

        # Get reference to deployed Modal function (Modal 1.0+ API)
        # from_name is lazy - hydrates on first use (remote call)
        extract_fn = modal.Function.from_name("lw-marker-extractor", "extract_pdf")

        # Call Modal function (blocking)
        start_time = time.time()
        result = extract_fn.remote(pdf_bytes, force_ocr=False)
        modal_time = time.time() - start_time

        logger.info("Modal extraction completed in %.2fs", modal_time)
        logger.info("  Pages: %d (%d native, %d OCR)",
                   result["pages"], result["native_pages"], result["ocr_pages"])
        logger.info("  Characters: %d", result["chars"])

        extraction_metadata = {
            "ocr_applied": result["ocr_pages"] > 0,
            "file_size_bytes": len(pdf_bytes),
            "modal_gpu": "A10G",
            "modal_processing_time": result["processing_time"],
            "modal_convert_time": result["convert_time"],
            "native_pages": result["native_pages"],
            "ocr_pages": result["ocr_pages"],
        }

        return result["text"], result["pages"], extraction_metadata

    except ImportError:
        logger.error("modal package not installed, falling back to local Marker")
        raise RuntimeError("modal package not installed")
    except Exception as e:
        logger.error("Modal extraction failed: %s", e)
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
            # Use Modal GPU when enabled (NO fallback - VM ARM cannot handle local Marker)
            if MODAL_ENABLED:
                save_job_log(job_id, "INFO", "Using Modal GPU acceleration (A10 24GB)")
                full_text, pages_processed, metadata = extract_with_modal(pdf_path, options)
                metadata["extraction_mode"] = "modal_gpu"
            else:
                # CPU-only mode (requires high-memory server, not suitable for ARM VM)
                save_job_log(job_id, "INFO", "Using CPU Marker (slow, requires >10GB RAM)")
                full_text, pages_processed, metadata = extract_with_marker(pdf_path, options)
                metadata["extraction_mode"] = "cpu"
        elif engine == "pdfplumber":
            full_text, pages_processed, metadata = extract_with_pdfplumber(pdf_path, options)
            metadata["extraction_mode"] = "pdfplumber"
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

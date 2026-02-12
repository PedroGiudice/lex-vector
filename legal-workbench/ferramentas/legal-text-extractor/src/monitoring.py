"""
Monitoring and Performance Tracking for Legal Text Extractor.

Provides Sentry v8 integration with detailed spans for tracking:
- Model loading (the 10% hang point)
- PDF conversion phases
- Memory usage during extraction

Usage:
    from src.monitoring import init_monitoring, start_span, track_memory

    # Initialize at startup
    init_monitoring("legal-text-extractor")

    # Track specific operations
    with start_span("marker.load_models") as span:
        models = create_model_dict()
        span.set_data("models_loaded", list(models.keys()))

Environment Variables:
    SENTRY_DSN: Sentry Data Source Name (required for Sentry to work)
    ENVIRONMENT: Environment name (development, staging, production)
    LTE_DEBUG: Set to "1" for verbose logging
"""

import logging
import os
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from functools import wraps
from typing import Any

import psutil

logger = logging.getLogger(__name__)

# Global state
_sentry_initialized = False
_start_time: float | None = None


def init_monitoring(service_name: str = "legal-text-extractor") -> bool:
    """
    Initialize Sentry for the Legal Text Extractor.

    Works standalone (no FastAPI required).

    Args:
        service_name: Identifier for this service

    Returns:
        True if Sentry was initialized, False if skipped
    """
    global _sentry_initialized, _start_time
    _start_time = time.time()

    dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        logger.info(f"[{service_name}] SENTRY_DSN not set, Sentry disabled")
        logger.info(f"[{service_name}] Using local logging only")
        _configure_verbose_logging()
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError as e:
        logger.warning(f"[{service_name}] sentry-sdk not installed: {e}")
        logger.info("Install with: pip install sentry-sdk")
        _configure_verbose_logging()
        return False

    environment = os.getenv("ENVIRONMENT", "development")
    release = os.getenv("APP_VERSION", "1.0.0")

    # Configure sample rates based on environment
    if environment == "production":
        traces_sample_rate = 0.3  # 30% - higher for debugging
        profiles_sample_rate = 0.2
    else:
        traces_sample_rate = 1.0  # 100% in dev/staging
        profiles_sample_rate = 0.5

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.DEBUG,  # Capture DEBUG and above as breadcrumbs
        event_level=logging.ERROR,  # Send ERROR and above as events
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=f"{service_name}@{release}",
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        integrations=[logging_integration],
        send_default_pii=False,
        attach_stacktrace=True,
        # Enable performance monitoring
        enable_tracing=True,
    )

    # Set service-specific tags
    sentry_sdk.set_tag("service", service_name)
    sentry_sdk.set_tag("python_version", sys.version.split()[0])

    # Set initial memory context
    mem = psutil.virtual_memory()
    sentry_sdk.set_context(
        "system",
        {
            "total_ram_gb": round(mem.total / (1024**3), 2),
            "available_ram_gb": round(mem.available / (1024**3), 2),
            "cpu_count": psutil.cpu_count(),
        },
    )

    _sentry_initialized = True
    logger.info(f"[{service_name}] Sentry initialized (env={environment}, release={release})")

    return True


def _configure_verbose_logging():
    """Configure verbose logging when Sentry is not available."""
    debug_mode = os.getenv("LTE_DEBUG", "0") == "1"

    # Create detailed formatter
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s", datefmt="%H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    if debug_mode:
        root_logger.setLevel(logging.DEBUG)
        logger.debug("LTE_DEBUG=1: Verbose logging enabled")
    else:
        root_logger.setLevel(logging.INFO)


@contextmanager
def start_span(op: str, description: str | None = None, **data: Any) -> Generator[Any, None, None]:
    """
    Start a performance span for tracking operations.

    Works with or without Sentry - falls back to logging.

    Args:
        op: Operation name (e.g., "marker.load_models", "marker.convert")
        description: Human-readable description
        **data: Additional data to attach to span

    Yields:
        Span object (or mock if Sentry not available)

    Example:
        with start_span("marker.load_models", model_count=5) as span:
            models = create_model_dict()
            span.set_data("loaded", True)
    """
    start_time = time.time()
    start_mem = psutil.Process().memory_info().rss / (1024**2)  # MB

    logger.info(f"[SPAN START] {op}: {description or ''}")

    if _sentry_initialized:
        try:
            import sentry_sdk

            with sentry_sdk.start_span(op=op, description=description) as span:
                for key, value in data.items():
                    span.set_data(key, value)

                # Track memory at start
                span.set_data("memory_start_mb", round(start_mem, 2))

                try:
                    yield span
                finally:
                    # Track duration and memory delta
                    elapsed = time.time() - start_time
                    end_mem = psutil.Process().memory_info().rss / (1024**2)
                    span.set_data("duration_seconds", round(elapsed, 3))
                    span.set_data("memory_end_mb", round(end_mem, 2))
                    span.set_data("memory_delta_mb", round(end_mem - start_mem, 2))

                    logger.info(
                        f"[SPAN END] {op}: {elapsed:.2f}s, "
                        f"mem: {start_mem:.0f}MB -> {end_mem:.0f}MB "
                        f"(delta: {end_mem - start_mem:+.0f}MB)"
                    )
            return
        except Exception as e:
            logger.warning(f"Sentry span error: {e}")

    # Fallback: mock span for logging
    class MockSpan:
        def set_data(self, key: str, value: Any) -> None:
            logger.debug(f"  {key}: {value}")

    mock = MockSpan()
    for key, value in data.items():
        mock.set_data(key, value)

    try:
        yield mock
    finally:
        elapsed = time.time() - start_time
        end_mem = psutil.Process().memory_info().rss / (1024**2)
        logger.info(
            f"[SPAN END] {op}: {elapsed:.2f}s, "
            f"mem: {start_mem:.0f}MB -> {end_mem:.0f}MB "
            f"(delta: {end_mem - start_mem:+.0f}MB)"
        )


def track_progress(current: int, total: int, operation: str = "processing"):
    """
    Track progress and log with percentage.

    Args:
        current: Current item number (1-indexed)
        total: Total items
        operation: What's being processed
    """
    pct = (current / total) * 100 if total > 0 else 0
    elapsed = time.time() - (_start_time or time.time())

    # Estimate remaining time
    if current > 0:
        rate = elapsed / current
        remaining = rate * (total - current)
        eta = f", ETA: {remaining:.0f}s" if remaining > 0 else ""
    else:
        eta = ""

    logger.info(f"[PROGRESS] {operation}: {current}/{total} ({pct:.1f}%){eta}")

    if _sentry_initialized:
        try:
            import sentry_sdk

            sentry_sdk.add_breadcrumb(
                message=f"{operation}: {current}/{total}",
                category="progress",
                level="info",
                data={"current": current, "total": total, "percent": pct},
            )
        except Exception:
            pass


def track_memory(context: str = "checkpoint"):
    """
    Log current memory usage.

    Args:
        context: Description of where this checkpoint is
    """
    process = psutil.Process()
    mem = process.memory_info()
    system_mem = psutil.virtual_memory()

    rss_mb = mem.rss / (1024**2)
    available_mb = system_mem.available / (1024**2)
    percent_used = system_mem.percent

    logger.info(
        f"[MEMORY] {context}: "
        f"Process={rss_mb:.0f}MB, "
        f"System={percent_used:.1f}% used, "
        f"Available={available_mb:.0f}MB"
    )

    if _sentry_initialized:
        try:
            import sentry_sdk

            sentry_sdk.set_context(
                "memory",
                {
                    "process_rss_mb": round(rss_mb, 2),
                    "system_percent": percent_used,
                    "system_available_mb": round(available_mb, 2),
                    "checkpoint": context,
                },
            )
        except Exception:
            pass

    # Warning if memory is getting low
    if available_mb < 2000:  # Less than 2GB available
        logger.warning(
            f"[MEMORY WARNING] Low memory at {context}: only {available_mb:.0f}MB available!"
        )


def capture_exception(error: Exception, **extra: Any) -> str | None:
    """
    Capture an exception with additional context.

    Args:
        error: The exception to capture
        **extra: Additional context to attach

    Returns:
        Event ID if captured, None if Sentry not available
    """
    # Always log locally
    logger.exception(f"Error captured: {error}")

    if _sentry_initialized:
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:
                for key, value in extra.items():
                    scope.set_extra(key, value)
                return sentry_sdk.capture_exception(error)
        except Exception:
            pass

    return None


def set_extraction_context(pdf_path: str, file_size_mb: float, page_count: int | None = None):
    """
    Set context for the current extraction operation.

    Args:
        pdf_path: Path to the PDF being processed
        file_size_mb: File size in megabytes
        page_count: Number of pages (if known)
    """
    context = {
        "pdf_name": os.path.basename(pdf_path),
        "file_size_mb": round(file_size_mb, 2),
    }
    if page_count:
        context["page_count"] = page_count

    logger.info(f"[CONTEXT] Processing: {context}")

    if _sentry_initialized:
        try:
            import sentry_sdk

            sentry_sdk.set_context("extraction", context)
            sentry_sdk.set_tag("pdf_size_category", _size_category(file_size_mb))
        except Exception:
            pass


def _size_category(size_mb: float) -> str:
    """Categorize file size for Sentry tags."""
    if size_mb < 1:
        return "small"
    elif size_mb < 10:
        return "medium"
    elif size_mb < 50:
        return "large"
    else:
        return "xlarge"


def timed(operation: str):
    """
    Decorator to time a function and log/track its duration.

    Args:
        operation: Name for the operation

    Example:
        @timed("load_models")
        def load_models():
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with start_span(f"lte.{operation}", description=func.__name__):
                return func(*args, **kwargs)

        return wrapper

    return decorator

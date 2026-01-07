"""
Sentry Configuration for Legal Workbench FastAPI Services.

Provides centralized error tracking and performance monitoring configuration
for all backend services in the Legal Workbench platform.

Usage:
    from shared.sentry_config import init_sentry

    # Call at the very beginning of main.py, before app initialization
    init_sentry("service-name")

Environment Variables:
    SENTRY_DSN: Sentry Data Source Name (required for Sentry to work)
    ENVIRONMENT: Environment name (development, staging, production)
    APP_VERSION: Application version for release tracking
"""

import os
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def init_sentry(service_name: str) -> bool:
    """
    Initialize Sentry for a FastAPI service.

    Must be called before FastAPI app initialization for proper instrumentation.

    Args:
        service_name: Identifier for this service (e.g., "stj-api", "text-extractor")

    Returns:
        True if Sentry was initialized, False if skipped (no DSN configured)
    """
    dsn = os.getenv("SENTRY_DSN")

    if not dsn:
        logger.info(f"[{service_name}] SENTRY_DSN not set, Sentry disabled")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError as e:
        logger.warning(f"[{service_name}] sentry-sdk not installed: {e}")
        return False

    environment = os.getenv("ENVIRONMENT", "development")
    release = os.getenv("APP_VERSION", "1.0.0")

    # Configure sample rates based on environment
    if environment == "production":
        traces_sample_rate = 0.1  # 10% of transactions
        profiles_sample_rate = 0.1  # 10% of sampled transactions
    else:
        traces_sample_rate = 1.0  # 100% in dev/staging
        profiles_sample_rate = 0.5

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture INFO and above as breadcrumbs
        event_level=logging.ERROR  # Send ERROR and above as events
    )

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=f"{service_name}@{release}",
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            logging_integration,
        ],
        # Security: Don't send PII
        send_default_pii=False,
        # Always attach stacktrace for debugging
        attach_stacktrace=True,
        # Filter non-actionable errors
        before_send=_filter_events,
        # Ignore common health check transactions
        traces_sampler=_traces_sampler,
    )

    # Set service-specific tag
    sentry_sdk.set_tag("service", service_name)

    logger.info(f"[{service_name}] Sentry initialized (env={environment}, release={release})")
    return True


def _filter_events(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter out non-actionable errors before sending to Sentry.

    Args:
        event: The Sentry event being processed
        hint: Additional context including exception info

    Returns:
        The event to send, or None to drop it
    """
    if "exc_info" in hint:
        exc_type, exc_value, _ = hint["exc_info"]
        exc_name = exc_type.__name__ if exc_type else ""

        # Skip common connection errors that aren't actionable
        connection_errors = (
            "ConnectionResetError",
            "BrokenPipeError",
            "ConnectionRefusedError",
            "ConnectionAbortedError",
        )
        if exc_name in connection_errors:
            return None

        # Skip client-side HTTP errors (4xx)
        if exc_name == "HTTPException":
            status_code = getattr(exc_value, "status_code", 500)
            if 400 <= status_code < 500:
                return None

        # Skip cancelled requests
        if exc_name in ("CancelledError", "asyncio.CancelledError"):
            return None

    return event


def _traces_sampler(sampling_context: dict) -> float:
    """
    Custom sampler to reduce noise from health checks and static assets.

    Args:
        sampling_context: Context about the transaction being sampled

    Returns:
        Sample rate between 0.0 and 1.0
    """
    transaction_context = sampling_context.get("transaction_context", {})
    name = transaction_context.get("name", "")

    # Don't sample health checks
    if "/health" in name:
        return 0.0

    # Don't sample static assets or docs
    if any(path in name for path in ["/docs", "/redoc", "/openapi.json", "/static"]):
        return 0.0

    # Use default sample rate for everything else
    # (Will use the traces_sample_rate from init)
    return 1.0


def capture_exception(error: Exception, **extra: Any) -> Optional[str]:
    """
    Capture an exception with additional context.

    Wrapper around sentry_sdk.capture_exception with safety checks.

    Args:
        error: The exception to capture
        **extra: Additional context to attach to the event

    Returns:
        Event ID if captured, None if Sentry is not initialized
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            return sentry_sdk.capture_exception(error)
    except ImportError:
        return None


def capture_message(message: str, level: str = "info", **extra: Any) -> Optional[str]:
    """
    Capture a message with additional context.

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **extra: Additional context to attach to the event

    Returns:
        Event ID if captured, None if Sentry is not initialized
    """
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            return sentry_sdk.capture_message(message, level=level)
    except ImportError:
        return None


def set_user(user_id: str, email: Optional[str] = None, **extra: Any) -> None:
    """
    Set user context for error tracking.

    Args:
        user_id: Unique user identifier
        email: Optional email address
        **extra: Additional user attributes
    """
    try:
        import sentry_sdk

        user_data = {"id": user_id}
        if email:
            user_data["email"] = email
        user_data.update(extra)
        sentry_sdk.set_user(user_data)
    except ImportError:
        pass


def add_breadcrumb(message: str, category: str = "custom", level: str = "info", **data: Any) -> None:
    """
    Add a breadcrumb for debugging context.

    Args:
        message: Breadcrumb message
        category: Category for grouping
        level: Severity level
        **data: Additional data to attach
    """
    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data if data else None
        )
    except ImportError:
        pass

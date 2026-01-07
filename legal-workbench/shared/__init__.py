"""
Shared utilities for Legal Workbench backend services.

This package provides common infrastructure components:
- logging_config: Structured JSON logging configuration
- middleware: FastAPI middleware for request tracking

Usage:
    # Setup logging for a service
    from shared.logging_config import setup_logging, get_logger
    logger = setup_logging("my-service")

    # Add request tracking middleware to FastAPI
    from fastapi import FastAPI
    from shared.middleware import RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    # Get request ID in handlers
    from shared.middleware import get_request_id
    request_id = get_request_id()
"""

from shared.logging_config import setup_logging, get_logger, JSONFormatter, request_id_var
from shared.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    get_request_id,
    request_id_ctx,
)
from shared.sentry_config import (
    init_sentry,
    capture_exception,
    capture_message,
    set_user,
    add_breadcrumb,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "JSONFormatter",
    "request_id_var",
    # Middleware
    "RequestIDMiddleware",
    "RequestLoggingMiddleware",
    "get_request_id",
    "request_id_ctx",
    # Sentry
    "init_sentry",
    "capture_exception",
    "capture_message",
    "set_user",
    "add_breadcrumb",
]

__version__ = "0.1.0"

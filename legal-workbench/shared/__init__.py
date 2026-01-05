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

from shared.logging_config import setup_logging, get_logger, JSONFormatter
from shared.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    get_request_id,
    request_id_ctx,
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "JSONFormatter",
    # Middleware
    "RequestIDMiddleware",
    "RequestLoggingMiddleware",
    "get_request_id",
    "request_id_ctx",
]

__version__ = "0.1.0"

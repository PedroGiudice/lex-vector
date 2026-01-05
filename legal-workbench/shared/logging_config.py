"""
Structured JSON logging configuration for Legal Workbench services.

This module provides a JSON formatter and setup function for consistent,
structured logging across all backend services. Each log entry includes:
- ISO 8601 timestamp with UTC timezone
- Log level
- Service name
- Request ID (for request tracing)
- Message and context
- Module/function/line information
- Exception details when applicable

Usage:
    from shared.logging_config import setup_logging

    logger = setup_logging("my-service-name")
    logger.info("Service started")

    # With request context
    logger.info("Processing request", extra={'request_id': 'abc-123'})
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON objects.

    This ensures logs are easily parseable by log aggregation tools
    like Elasticsearch, Datadog, or CloudWatch.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted string representing the log entry
        """
        log_obj: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": getattr(record, 'service', 'unknown'),
            "request_id": getattr(record, 'request_id', None),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include extra fields passed via extra= parameter
        # Exclude standard LogRecord attributes
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'pathname', 'process', 'processName', 'relativeCreated',
            'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
            'message', 'service', 'request_id'
        }

        extra_fields = {
            key: value for key, value in record.__dict__.items()
            if key not in standard_attrs and not key.startswith('_')
        }

        if extra_fields:
            log_obj["extra"] = extra_fields

        # Include exception information if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str, ensure_ascii=False)


def setup_logging(
    service_name: str,
    level: int = logging.INFO,
    stream: Optional[Any] = None
) -> logging.Logger:
    """
    Configure the root logger with JSON formatting for a service.

    This function:
    1. Creates a StreamHandler writing to stdout (or custom stream)
    2. Attaches the JSONFormatter
    3. Sets up a custom LogRecordFactory to inject service name

    Args:
        service_name: Name of the service (e.g., "legal-doc-assembler")
        level: Logging level (default: INFO)
        stream: Output stream (default: sys.stdout)

    Returns:
        Configured root logger

    Example:
        logger = setup_logging("api-gateway")
        logger.info("Server starting", extra={'port': 8000})
    """
    if stream is None:
        stream = sys.stdout

    # Create handler with JSON formatter
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())

    # Configure root logger
    logger = logging.getLogger()
    logger.handlers = [handler]
    logger.setLevel(level)

    # Create custom record factory to inject service name
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.service = service_name  # type: ignore[attr-defined]
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that inherits the JSON formatting configuration.

    Use this when you need a logger for a specific module but want
    to keep the JSON formatting from setup_logging().

    Args:
        name: Logger name (typically __name__)

    Returns:
        Named logger instance

    Example:
        # In a module
        logger = get_logger(__name__)
        logger.debug("Module initialized")
    """
    return logging.getLogger(name)

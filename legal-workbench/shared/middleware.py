"""
FastAPI middleware for request tracking and logging.

This module provides middleware components for:
- Request ID generation and propagation
- Request/response timing
- Structured request logging

Usage:
    from fastapi import FastAPI
    from shared.middleware import RequestIDMiddleware

    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
"""

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# Context variable for request ID - accessible throughout the request lifecycle
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    This can be called from anywhere in the request handling code
    to get the current request's ID for logging or tracing.

    Returns:
        Current request ID or None if not in a request context
    """
    return request_id_ctx.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates or propagates request IDs.

    Features:
    - Uses X-Request-ID header if provided by client/upstream service
    - Generates UUID if no request ID is provided
    - Stores request ID in context variable for access throughout request
    - Adds request ID to response headers
    - Logs request completion with timing information

    The request ID is useful for:
    - Tracing requests across distributed services
    - Correlating logs from a single request
    - Debugging and troubleshooting
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with ID tracking and logging.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/route handler

        Returns:
            The HTTP response with X-Request-ID header
        """
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in context for access by other parts of the application
        token = request_id_ctx.set(request_id)

        # Record start time for duration calculation
        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate request duration
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Log request completion with structured data
            logging.info(
                "Request completed",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'query_string': str(request.query_params) if request.query_params else None,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'client_ip': self._get_client_ip(request),
                    'user_agent': request.headers.get("User-Agent"),
                }
            )

            # Add request ID to response headers for client correlation
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Log exception with request context
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logging.exception(
                "Request failed with exception",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'error_type': type(e).__name__,
                }
            )
            raise

        finally:
            # Reset context variable
            request_id_ctx.reset(token)

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Extract client IP address, considering proxy headers.

        Args:
            request: The HTTP request

        Returns:
            Client IP address or None
        """
        # Check for forwarded headers (when behind a proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs; first is the client
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client connection
        if request.client:
            return request.client.host

        return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for detailed request/response logging.

    This is more verbose than RequestIDMiddleware and logs
    both the incoming request and outgoing response separately.
    Use for development or when detailed request logging is needed.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/route handler

        Returns:
            The HTTP response
        """
        request_id = get_request_id() or str(uuid.uuid4())

        # Log incoming request
        logging.info(
            "Request received",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'headers': dict(request.headers),
            }
        )

        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Log outgoing response
        logging.info(
            "Response sent",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'content_type': response.headers.get("content-type"),
                'content_length': response.headers.get("content-length"),
            }
        )

        return response

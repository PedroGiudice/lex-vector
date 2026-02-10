import os
import sys
import logging

# Add shared module path for logging and Sentry
sys.path.insert(0, '/app')

# Initialize Sentry BEFORE importing FastAPI for proper instrumentation
try:
    from shared.sentry_config import init_sentry
    init_sentry("ledes-converter")
except ImportError:
    pass  # Sentry not available, continue without it

# Configure structured JSON logging
from shared.logging_config import setup_logging
from shared.middleware import RequestIDMiddleware

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logger = setup_logging("ledes-converter", level=log_level)

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, Optional
import docx
import tempfile
from collections import defaultdict
import time
import magic
import json

from .models import LedesData, ConversionResponse, HealthResponse, LineItem, LedesConfig
from .ledes_generator import (
    sanitize_string,
    sanitize_ledes_field,
    parse_currency,
    format_ledes_currency,
    format_date_ledes,
    extract_ledes_data,
    generate_ledes_1998b,
    MAX_DESCRIPTION_LENGTH,
    MAX_LINE_ITEMS,
)

app = FastAPI(
    title="LEDES Converter API",
    description="Convert DOCX invoices to LEDES 1998B format",
    version="1.0.0"
)

# Request ID middleware for request tracing
app.add_middleware(RequestIDMiddleware)

# CORS middleware - configured for production security
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Log startup
@app.on_event("startup")
async def startup_event():
    logger.info("Service starting", extra={"event": "startup", "version": "1.0.0"})

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILENAME_LENGTH = 255
ALLOWED_MIME_TYPES = [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream"  # Some systems send DOCX as this
]

# Simple rate limiting (production should use Redis)
rate_limit_storage = defaultdict(list)


def rate_limit_check(client_ip: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
    """Simple in-memory rate limiting. Production should use Redis."""
    now = time.time()
    # Clean old entries
    rate_limit_storage[client_ip] = [
        ts for ts in rate_limit_storage[client_ip]
        if now - ts < window_seconds
    ]

    if len(rate_limit_storage[client_ip]) >= max_requests:
        return False

    rate_limit_storage[client_ip].append(now)
    return True


def validate_file_type(content: bytes, filename: str) -> bool:
    """Validate file type using magic bytes (MIME detection)."""
    try:
        mime = magic.from_buffer(content, mime=True)

        # Check MIME type
        if mime not in ALLOWED_MIME_TYPES:
            logger.warning(f"Invalid MIME type detected: {mime} for file extension .docx")
            return False

        # Additional check: DOCX files should start with PK (ZIP header)
        if not content.startswith(b'PK'):
            logger.warning("File does not have valid ZIP/DOCX header")
            return False

        return True
    except Exception as e:
        logger.error(f"File type validation error: {e}")
        return False


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return HealthResponse(status="ok", service="ledes-converter")


@app.post("/convert/docx-to-ledes", response_model=ConversionResponse)
async def convert_docx_to_ledes(
    request: Request,
    file: Annotated[UploadFile, File(description="DOCX file to convert to LEDES")],
    config: Annotated[Optional[str], Form(description="JSON string with LEDES configuration")] = None
) -> ConversionResponse:
    """
    Convert a DOCX invoice file to LEDES 1998B format.

    - **file**: DOCX file containing invoice data (max 10MB)
    - **config**: Optional JSON string with LEDES configuration (law_firm_id, client_id, matter_id, etc.)
    - Returns: LEDES formatted content and extracted data

    Security features:
    - Rate limiting (10 requests/minute per IP)
    - MIME type validation using magic bytes
    - File size validation
    - Input sanitization
    """
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limit_check(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

    # Validate filename
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    if len(file.filename) > MAX_FILENAME_LENGTH:
        raise HTTPException(status_code=400, detail="Filename too long.")

    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .docx file.")

    # Read and validate file size
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB."
        )

    # Validate MIME type using magic bytes
    if not validate_file_type(content, file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. File does not appear to be a valid DOCX document."
        )

    tmp_path = ""
    try:
        # Save temp file with secure permissions
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx", mode='wb') as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Set restrictive permissions
        os.chmod(tmp_path, 0o600)

        # Process DOCX with error handling
        try:
            doc = docx.Document(tmp_path)
        except Exception as docx_error:
            logger.error(f"Failed to parse DOCX: {docx_error}")
            raise HTTPException(
                status_code=400,
                detail="Unable to parse DOCX file. File may be corrupted or in an unsupported format."
            )

        full_text = []
        for para in doc.paragraphs:
            if para.text:
                full_text.append(para.text)

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text:
                        full_text.append(cell.text)

        text_content = "\n".join(full_text)

        # Validate extracted content
        if not text_content.strip():
            raise HTTPException(
                status_code=400,
                detail="No text content found in DOCX file."
            )

        # Extract Data
        extracted_data = extract_ledes_data(text_content)

        # Parse and validate config if provided
        ledes_config = None
        if config:
            try:
                config_dict = json.loads(config)
                ledes_config = LedesConfig(**config_dict)
                logger.info(f"Config provided: law_firm={ledes_config.law_firm_id}, client={ledes_config.client_id}, matter={ledes_config.matter_id}")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid JSON in config parameter: {str(e)}"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid config data: {str(e)}"
                )

        # Merge config with extracted data (config takes precedence)
        if ledes_config:
            # Firm/Client/Matter
            extracted_data["law_firm_id"] = ledes_config.law_firm_id
            extracted_data["law_firm_name"] = ledes_config.law_firm_name
            extracted_data["client_id"] = ledes_config.client_id
            extracted_data["client_name"] = ledes_config.client_name
            extracted_data["matter_id"] = ledes_config.matter_id
            extracted_data["matter_name"] = ledes_config.matter_name
            extracted_data["client_matter_id"] = ledes_config.client_matter_id or ""
            # Timekeeper
            extracted_data["timekeeper_id"] = ledes_config.timekeeper_id or ""
            extracted_data["timekeeper_name"] = ledes_config.timekeeper_name or ""
            extracted_data["timekeeper_classification"] = ledes_config.timekeeper_classification or ""
            extracted_data["unit_cost"] = ledes_config.unit_cost or 0
            # Billing period
            extracted_data["billing_start_date"] = ledes_config.billing_start_date or ""
            extracted_data["billing_end_date"] = ledes_config.billing_end_date or ""
        else:
            # Backward compatibility: use placeholders if no config provided
            extracted_data["law_firm_id"] = ""
            extracted_data["client_matter_id"] = ""
            logger.warning("No config provided, using empty law_firm_id (backward compatibility mode)")

        # Validate extracted data
        if not extracted_data.get("invoice_number"):
            logger.warning("Invoice number not found in document")

        if not extracted_data.get("line_items"):
            raise HTTPException(
                status_code=400,
                detail="No line items found in invoice. Please check document format."
            )

        # Generate LEDES
        ledes_content = generate_ledes_1998b(extracted_data)

        logger.info(f"Successfully converted invoice (lines: {len(extracted_data['line_items'])})")

        # Create validated response using Pydantic models
        line_items = [LineItem(**item) for item in extracted_data["line_items"]]
        ledes_data = LedesData(
            invoice_date=extracted_data["invoice_date"],
            invoice_number=extracted_data["invoice_number"],
            client_id=extracted_data["client_id"],
            matter_id=extracted_data["matter_id"],
            invoice_total=extracted_data["invoice_total"],
            line_items=line_items
        )

        return ConversionResponse(
            filename=sanitize_string(file.filename, MAX_FILENAME_LENGTH),
            status="success",
            extracted_data=ledes_data,
            ledes_content=ledes_content
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Conversion failed due to an internal error. Please contact support if the issue persists."
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp file: {cleanup_error}")


@app.get("/debug/sentry", tags=["Debug"])
async def debug_sentry():
    """
    Test Sentry integration by triggering a test exception.

    This endpoint is for debugging purposes only.
    In production, this should be disabled or protected.
    """
    raise Exception("Sentry test exception from ledes-converter")

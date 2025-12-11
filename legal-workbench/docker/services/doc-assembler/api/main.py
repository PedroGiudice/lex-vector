"""
FastAPI application for Legal Document Assembler.

RESTful API wrapping the DocumentEngine for web-based document generation.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path to import from ferramentas
# Support both local development and Docker deployment
if os.path.exists("/app/ferramentas"):
    # Running in Docker
    DOC_ASSEMBLER_PATH = Path("/app/ferramentas/legal-doc-assembler/src")
else:
    # Running locally
    LEGAL_WORKBENCH_ROOT = Path("/home/user/Claude-Code-Projetos/legal-workbench")
    DOC_ASSEMBLER_PATH = LEGAL_WORKBENCH_ROOT / "ferramentas/legal-doc-assembler/src"

sys.path.insert(0, str(DOC_ASSEMBLER_PATH))

from engine import DocumentEngine

from .models import (
    AssembleRequest,
    AssembleResponse,
    ValidateRequest,
    ValidateResponse,
    PreviewRequest,
    PreviewResponse,
    TemplateListResponse,
    TemplateDetailResponse,
    TemplateInfo,
    ValidationResult,
    HealthResponse,
    ErrorResponse,
)


# ============================================================================
# Configuration
# ============================================================================

# Base paths (can be overridden by environment variables)
TEMPLATES_DIR = Path(os.getenv("TEMPLATES_DIR", "/app/templates"))
OUTPUTS_DIR = Path(os.getenv("OUTPUTS_DIR", "/app/outputs"))
API_VERSION = "1.0.0"

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Legal Document Assembler API",
    description="RESTful API for generating Brazilian legal documents from templates",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    """Handle file not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            detail=str(exc),
            error_type="FileNotFoundError",
            status_code=404,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            detail=str(exc),
            error_type="ValueError",
            status_code=400,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail=f"Internal server error: {str(exc)}",
            error_type=type(exc).__name__,
            status_code=500,
            timestamp=datetime.utcnow().isoformat()
        ).dict()
    )


# ============================================================================
# Helper Functions
# ============================================================================

def resolve_template_path(template_path: str) -> Path:
    """
    Resolve template path relative to TEMPLATES_DIR.

    Args:
        template_path: Relative path to template

    Returns:
        Absolute Path to template

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    # Remove leading slash if present
    template_path = template_path.lstrip('/')

    # Build absolute path
    abs_path = TEMPLATES_DIR / template_path

    # Validate path is within TEMPLATES_DIR (security)
    try:
        abs_path.resolve().relative_to(TEMPLATES_DIR.resolve())
    except ValueError:
        raise FileNotFoundError(
            f"Template path '{template_path}' is outside templates directory"
        )

    # Check if file exists
    if not abs_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return abs_path


def generate_output_path(output_filename: str = None) -> Path:
    """
    Generate output path for assembled document.

    Args:
        output_filename: Optional custom filename

    Returns:
        Absolute Path for output file
    """
    if output_filename:
        # Sanitize filename
        filename = Path(output_filename).name
    else:
        # Generate unique filename
        filename = f"document_{uuid4().hex[:8]}.docx"

    return OUTPUTS_DIR / filename


def get_download_url(output_path: Path) -> str:
    """
    Generate download URL for generated document.

    Args:
        output_path: Absolute path to generated file

    Returns:
        Download URL (relative to /outputs/)
    """
    # Get relative path from OUTPUTS_DIR
    rel_path = output_path.relative_to(OUTPUTS_DIR)
    return f"/outputs/{rel_path}"


def list_templates_in_dir(directory: Path) -> List[TemplateInfo]:
    """
    List all .docx templates in directory and subdirectories.

    Args:
        directory: Directory to search

    Returns:
        List of TemplateInfo objects
    """
    templates = []

    for docx_file in directory.rglob("*.docx"):
        # Skip temporary files
        if docx_file.name.startswith("~$"):
            continue

        # Get relative path from TEMPLATES_DIR
        rel_path = docx_file.relative_to(TEMPLATES_DIR)

        # Generate template ID (path without extension)
        template_id = str(rel_path.with_suffix('')).replace(os.sep, '/')

        # Human-readable name (filename without extension)
        name = docx_file.stem

        templates.append(TemplateInfo(
            id=template_id,
            name=name,
            path=str(rel_path).replace(os.sep, '/'),
            filename=docx_file.name,
            size_bytes=docx_file.stat().st_size
        ))

    return sorted(templates, key=lambda t: t.id)


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns service status and version information.
    """
    # Get engine version from the imported module
    try:
        sys.path.insert(0, str(DOC_ASSEMBLER_PATH.parent))
        import src as engine_module
        engine_version = getattr(engine_module, '__version__', 'unknown')
        sys.path.pop(0)
    except Exception:
        engine_version = 'unknown'

    return HealthResponse(
        status="healthy",
        version=API_VERSION,
        engine_version=engine_version,
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/api/v1/templates", response_model=TemplateListResponse)
async def list_templates():
    """
    List all available document templates.

    Returns:
        List of template information objects
    """
    templates = list_templates_in_dir(TEMPLATES_DIR)

    return TemplateListResponse(
        templates=templates,
        count=len(templates)
    )


@app.get("/api/v1/templates/{template_id:path}", response_model=TemplateDetailResponse)
async def get_template_detail(template_id: str):
    """
    Get detailed information about a specific template.

    Args:
        template_id: Template identifier (path without extension)

    Returns:
        Template details including required variables
    """
    # Reconstruct template path
    template_path = f"{template_id}.docx"

    # Resolve absolute path
    abs_path = resolve_template_path(template_path)

    # Create engine instance
    engine = DocumentEngine()

    # Get template variables
    variables = engine.get_template_variables(abs_path)

    # Build template info
    template_info = TemplateInfo(
        id=template_id,
        name=abs_path.stem,
        path=template_path,
        filename=abs_path.name,
        size_bytes=abs_path.stat().st_size
    )

    return TemplateDetailResponse(
        template=template_info,
        variables=variables,
        variable_count=len(variables)
    )


@app.post("/api/v1/validate", response_model=ValidateResponse)
async def validate_data(request: ValidateRequest):
    """
    Validate data against template requirements.

    Args:
        request: Validation request with template path and data

    Returns:
        Validation results with missing/extra fields
    """
    # Resolve template path
    abs_template_path = resolve_template_path(request.template_path)

    # Create engine instance
    engine = DocumentEngine()

    # Validate data
    validation = engine.validate_data(abs_template_path, request.data)

    # Get template variables
    template_vars = engine.get_template_variables(abs_template_path)

    # Build validation result
    valid = len(validation['missing']) == 0

    warnings = []
    if validation['extra']:
        warnings.append(
            f"Data contains {len(validation['extra'])} unused fields that will be ignored"
        )
    if validation['missing']:
        warnings.append(
            f"Missing {len(validation['missing'])} required fields - "
            "they will appear as {{ field_name }} in output"
        )

    result = ValidationResult(
        valid=valid,
        missing=validation['missing'],
        extra=validation['extra'],
        warnings=warnings
    )

    return ValidateResponse(
        result=result,
        template_variables=template_vars,
        data_keys=sorted(list(request.data.keys()))
    )


@app.post("/api/v1/preview", response_model=PreviewResponse)
async def preview_document(request: PreviewRequest):
    """
    Generate text preview of document without saving to file.

    Args:
        request: Preview request with template, data, and options

    Returns:
        Rendered text content and structure
    """
    # Resolve template path
    abs_template_path = resolve_template_path(request.template_path)

    # Create engine instance
    engine = DocumentEngine(auto_normalize=request.auto_normalize)

    # Extract rendered text
    result = engine.extract_rendered_text(
        template_path=abs_template_path,
        data=request.data,
        field_types=request.field_types
    )

    return PreviewResponse(
        full_text=result['full_text'],
        paragraphs=result['paragraphs'],
        tables=result.get('tables', []),
        paragraph_count=result['paragraph_count'],
        table_count=result['table_count']
    )


@app.post("/api/v1/assemble", response_model=AssembleResponse)
async def assemble_document(request: AssembleRequest):
    """
    Assemble a legal document from template and data.

    Args:
        request: Assembly request with template, data, and options

    Returns:
        Success response with download URL
    """
    # Resolve template path
    abs_template_path = resolve_template_path(request.template_path)

    # Generate output path
    output_path = generate_output_path(request.output_filename)

    # Create engine instance
    engine = DocumentEngine(auto_normalize=request.auto_normalize)

    # Render document
    result_path = engine.render(
        template_path=abs_template_path,
        data=request.data,
        output_path=output_path,
        field_types=request.field_types
    )

    # Generate download URL
    download_url = get_download_url(result_path)

    return AssembleResponse(
        success=True,
        output_path=str(result_path),
        download_url=download_url,
        filename=result_path.name,
        message="Document generated successfully"
    )


# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    print(f"🚀 Legal Document Assembler API v{API_VERSION}")
    print(f"📁 Templates directory: {TEMPLATES_DIR}")
    print(f"📄 Outputs directory: {OUTPUTS_DIR}")

    # Count available templates
    templates = list_templates_in_dir(TEMPLATES_DIR)
    print(f"📋 Found {len(templates)} template(s)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

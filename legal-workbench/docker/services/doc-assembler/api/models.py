"""
Pydantic models for Doc Assembler API.

Request and response schemas for all endpoints.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Request Models
# ============================================================================

class AssembleRequest(BaseModel):
    """Request model for document assembly endpoint."""

    template_path: str = Field(
        ...,
        description="Path to the .docx template file",
        examples=["templates/petição_inicial.docx"]
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data dictionary with template variables",
        examples=[{
            "nome": "João da Silva",
            "cpf": "12345678901",
            "endereco": "Rua das Flores, 123"
        }]
    )
    output_filename: Optional[str] = Field(
        None,
        description="Optional custom output filename (without path)",
        examples=["petição_joão_silva.docx"]
    )
    field_types: Optional[Dict[str, str]] = Field(
        None,
        description="Optional field type mapping for normalization",
        examples=[{
            "nome": "name",
            "cpf": "cpf",
            "endereco": "address"
        }]
    )
    auto_normalize: bool = Field(
        True,
        description="Enable automatic text normalization"
    )

    @field_validator('template_path')
    @classmethod
    def validate_template_path(cls, v: str) -> str:
        """Ensure template path has .docx extension."""
        if not v.endswith('.docx'):
            raise ValueError("Template path must end with .docx")
        return v


class ValidateRequest(BaseModel):
    """Request model for data validation endpoint."""

    template_path: str = Field(
        ...,
        description="Path to the .docx template file"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data dictionary to validate against template"
    )


class PreviewRequest(BaseModel):
    """Request model for document preview endpoint."""

    template_path: str = Field(
        ...,
        description="Path to the .docx template file"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Data dictionary with template variables"
    )
    field_types: Optional[Dict[str, str]] = Field(
        None,
        description="Optional field type mapping for normalization"
    )
    auto_normalize: bool = Field(
        True,
        description="Enable automatic text normalization"
    )


# ============================================================================
# Response Models
# ============================================================================

class AssembleResponse(BaseModel):
    """Response model for successful document assembly."""

    success: bool = Field(True, description="Operation success status")
    output_path: str = Field(..., description="Absolute path to generated document")
    download_url: str = Field(..., description="URL to download the generated document")
    filename: str = Field(..., description="Name of the generated file")
    message: str = Field(
        "Document generated successfully",
        description="Success message"
    )


class TemplateInfo(BaseModel):
    """Model for template information."""

    id: str = Field(..., description="Template identifier (filename without extension)")
    name: str = Field(..., description="Human-readable template name")
    path: str = Field(..., description="Relative path to template file")
    filename: str = Field(..., description="Template filename")
    size_bytes: Optional[int] = Field(None, description="File size in bytes")


class TemplateListResponse(BaseModel):
    """Response model for template list endpoint."""

    templates: List[TemplateInfo] = Field(..., description="List of available templates")
    count: int = Field(..., description="Total number of templates")


class TemplateDetailResponse(BaseModel):
    """Response model for template detail endpoint."""

    template: TemplateInfo = Field(..., description="Template information")
    variables: List[str] = Field(..., description="Required template variables")
    variable_count: int = Field(..., description="Number of variables in template")


class ValidationResult(BaseModel):
    """Model for validation results."""

    valid: bool = Field(..., description="Whether data is valid for template")
    missing: List[str] = Field(
        default_factory=list,
        description="Variables required by template but missing from data"
    )
    extra: List[str] = Field(
        default_factory=list,
        description="Variables in data but not used by template"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-critical validation warnings"
    )


class ValidateResponse(BaseModel):
    """Response model for validation endpoint."""

    result: ValidationResult = Field(..., description="Validation results")
    template_variables: List[str] = Field(
        ...,
        description="All variables expected by template"
    )
    data_keys: List[str] = Field(..., description="All keys provided in data")


class PreviewResponse(BaseModel):
    """Response model for preview endpoint."""

    full_text: str = Field(..., description="Rendered document text")
    paragraphs: List[str] = Field(..., description="List of rendered paragraphs")
    tables: List[List[List[str]]] = Field(
        default_factory=list,
        description="Extracted table data"
    )
    paragraph_count: int = Field(..., description="Number of paragraphs")
    table_count: int = Field(..., description="Number of tables")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field("healthy", description="Service health status")
    version: str = Field(..., description="API version")
    engine_version: str = Field(..., description="Document engine version")
    timestamp: str = Field(..., description="Current server timestamp (ISO 8601)")


class ErrorResponse(BaseModel):
    """Response model for error cases."""

    detail: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type/category")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp (ISO 8601)")

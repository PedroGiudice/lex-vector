"""
Pydantic models for Template Builder API endpoints.

These models define request/response schemas for creating templates from DOCX files.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================================
# Request Models
# ============================================================================

class PatternsRequest(BaseModel):
    """Request model for pattern detection endpoint."""

    text: str = Field(
        ...,
        description="Text content to analyze for patterns",
        min_length=1
    )


class FieldAnnotation(BaseModel):
    """Represents a field annotation for template creation."""

    field_name: str = Field(
        ...,
        description="Jinja2 field name (snake_case)",
        pattern=r'^[a-z][a-z0-9_]*$',
        examples=["nome_autor", "cpf_reu", "data_fato"]
    )
    start: int = Field(
        ...,
        description="Start position of text to replace",
        ge=0
    )
    end: int = Field(
        ...,
        description="End position of text to replace",
        ge=0
    )
    original_text: str = Field(
        ...,
        description="Original text being replaced",
        min_length=1
    )

    @field_validator('end')
    @classmethod
    def validate_end_after_start(cls, v: int, info) -> int:
        """Ensure end position is after start position."""
        if 'start' in info.data and v <= info.data['start']:
            raise ValueError("end must be greater than start")
        return v


class SaveTemplateRequest(BaseModel):
    """Request model for saving a new template."""

    document_id: str = Field(
        ...,
        description="Document ID from upload endpoint",
        min_length=1
    )
    template_name: str = Field(
        ...,
        description="Human-readable template name",
        min_length=1,
        max_length=200,
        examples=["Petição Inicial - Danos Morais"]
    )
    annotations: List[FieldAnnotation] = Field(
        ...,
        description="List of field replacements to apply",
        min_length=1
    )
    description: str = Field(
        "",
        description="Optional template description",
        max_length=1000
    )


# ============================================================================
# Response Models
# ============================================================================

class UploadResponse(BaseModel):
    """Response model for document upload endpoint."""

    document_id: str = Field(..., description="Unique document identifier")
    text_content: str = Field(..., description="Full text content of document")
    paragraphs: List[str] = Field(..., description="List of paragraphs")
    metadata: Dict[str, Any] = Field(
        ...,
        description="Document metadata (pages, word_count, etc.)"
    )


class PatternMatch(BaseModel):
    """Represents a detected pattern in text."""

    pattern_type: str = Field(
        ...,
        description="Type of pattern detected",
        examples=["cpf", "cnpj", "date_br", "currency_br"]
    )
    start: int = Field(..., description="Start position in text", ge=0)
    end: int = Field(..., description="End position in text", ge=0)
    value: str = Field(..., description="Matched text value")
    suggested_field: str = Field(
        ...,
        description="Suggested Jinja2 field name",
        examples=["cpf", "cnpj", "data_documento"]
    )


class PatternsResponse(BaseModel):
    """Response model for pattern detection endpoint."""

    matches: List[PatternMatch] = Field(
        ...,
        description="List of detected patterns"
    )
    pattern_types_found: List[str] = Field(
        ...,
        description="Unique pattern types found in text"
    )


class TemplateBuilderInfo(BaseModel):
    """Information about a saved builder template."""

    id: str = Field(..., description="Template UUID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    field_count: int = Field(..., description="Number of fields in template", ge=0)
    fields: List[str] = Field(..., description="List of field names")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    file_path: str = Field(..., description="Relative path to template file")


class SaveTemplateResponse(BaseModel):
    """Response model for save template endpoint."""

    id: str = Field(..., description="Generated template UUID")
    name: str = Field(..., description="Template name")
    file_path: str = Field(..., description="Path to saved template file")
    field_count: int = Field(..., description="Number of fields", ge=0)
    fields: List[str] = Field(..., description="List of field names")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class TemplateListResponse(BaseModel):
    """Response model for list templates endpoint."""

    templates: List[TemplateBuilderInfo] = Field(
        ...,
        description="List of builder templates"
    )
    count: int = Field(..., description="Total number of templates", ge=0)


class TemplateDetailResponse(BaseModel):
    """Response model for template detail endpoint."""

    template: TemplateBuilderInfo = Field(..., description="Template information")
    metadata: Dict[str, Any] = Field(
        ...,
        description="Full template metadata"
    )


class DuplicateTemplateResponse(BaseModel):
    """Response model for duplicate template endpoint."""

    id: str = Field(..., description="New template UUID")
    name: str = Field(..., description="New template name")
    original_id: str = Field(..., description="Original template UUID")
    file_path: str = Field(..., description="Path to duplicated template file")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")

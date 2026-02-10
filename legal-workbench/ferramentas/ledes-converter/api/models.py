from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class LedesConfig(BaseModel):
    """Configuration for LEDES conversion with required firm/client/matter identifiers."""
    # Firm info
    law_firm_id: str = Field(..., min_length=1, max_length=50, description="Law firm identifier")
    law_firm_name: str = Field(..., min_length=1, max_length=100, description="Law firm name")
    # Client info
    client_id: str = Field(..., min_length=1, max_length=50, description="Client identifier")
    client_name: Optional[str] = Field(None, max_length=100, description="Client name (optional)")
    # Matter info
    matter_id: str = Field(..., min_length=1, max_length=50, description="Matter identifier (LAW_FIRM_MATTER_ID)")
    matter_name: Optional[str] = Field(None, max_length=200, description="Matter name (optional)")
    client_matter_id: Optional[str] = Field(None, max_length=50, description="Client matter ID (field 24, optional)")
    # Timekeeper info
    timekeeper_id: Optional[str] = Field(None, max_length=20, description="Timekeeper ID")
    timekeeper_name: Optional[str] = Field(None, max_length=50, description="Timekeeper name (SURNAME, FIRST)")
    timekeeper_classification: Optional[str] = Field(None, max_length=10, description="PARTNR, ASSOC, LGPRMG, etc")
    unit_cost: Optional[float] = Field(None, ge=0, description="Hourly rate")
    # Billing period
    billing_start_date: Optional[str] = Field(None, max_length=8, description="YYYYMMDD")
    billing_end_date: Optional[str] = Field(None, max_length=8, description="YYYYMMDD")

    @field_validator('law_firm_id', 'law_firm_name', 'client_id', 'matter_id')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Required field cannot be empty")
        return v.strip()


class LineItem(BaseModel):
    """Represents a single line item in an invoice."""
    description: str = Field(..., max_length=500, description="Line item description")
    amount: float = Field(..., ge=0, description="Line item amount (must be non-negative)")
    task_code: str = Field(default="", max_length=10, description="UTBMS task code")
    activity_code: str = Field(default="", max_length=10, description="UTBMS activity code")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Description cannot be empty")
        return v.strip()


class LedesData(BaseModel):
    """Extracted invoice data ready for LEDES conversion."""
    invoice_date: str = Field(..., description="Invoice date in YYYYMMDD format")
    invoice_number: str = Field(..., max_length=50, description="Invoice number")
    client_id: str = Field(..., max_length=100, description="Client identifier")
    matter_id: str = Field(..., max_length=100, description="Matter identifier")
    invoice_total: float = Field(..., ge=0, description="Total invoice amount")
    line_items: List[LineItem] = Field(..., min_length=1, description="Invoice line items")

    @field_validator('invoice_date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if v and len(v) != 8:
            raise ValueError("Invoice date must be in YYYYMMDD format")
        return v


class ConversionResponse(BaseModel):
    """API response for successful conversion."""
    filename: str = Field(..., description="Original filename")
    status: str = Field(default="success", description="Conversion status")
    extracted_data: LedesData = Field(..., description="Extracted invoice data")
    ledes_content: str = Field(..., description="LEDES 1998B formatted content")


class ErrorResponse(BaseModel):
    """API response for errors."""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="ok", description="Service health status")
    service: str = Field(default="ledes-converter", description="Service name")


class MatterRequest(BaseModel):
    """Request body for creating/updating a Matter."""
    matter_name: str = Field(..., min_length=1, max_length=200)
    matter_id: str = Field(..., min_length=1, max_length=50)
    client_matter_id: str = Field(default="", max_length=50)
    client_id: str = Field(..., min_length=1, max_length=100)
    client_name: str = Field(default="", max_length=100)
    law_firm_id: str = Field(..., min_length=1, max_length=50)
    law_firm_name: str = Field(default="", max_length=100)
    timekeeper_id: str = Field(default="", max_length=20)
    timekeeper_name: str = Field(default="", max_length=50)
    timekeeper_classification: str = Field(default="", max_length=10)
    unit_cost: float = Field(default=0.0, ge=0)
    default_task_code: str = Field(default="", max_length=10)
    default_activity_code: str = Field(default="", max_length=10)


class MatterResponse(BaseModel):
    """Response body for a Matter."""
    matter_name: str
    matter_id: str
    client_matter_id: str
    client_id: str
    client_name: str
    law_firm_id: str
    law_firm_name: str
    timekeeper_id: str
    timekeeper_name: str
    timekeeper_classification: str
    unit_cost: float
    default_task_code: str
    default_activity_code: str
    created_at: str
    updated_at: str


class ValidationIssueResponse(BaseModel):
    """Single validation issue."""
    line: int
    field: int
    field_name: str
    severity: str
    message: str


class ValidationResponse(BaseModel):
    """Response from LEDES validation."""
    valid: bool
    error_count: int
    warning_count: int
    issues: List[ValidationIssueResponse]


class BatchResultItem(BaseModel):
    """Result for a single file in batch conversion."""
    filename: str
    status: str
    ledes_content: Optional[str] = None
    extracted_data: Optional[LedesData] = None
    error: Optional[str] = None
    validation_issues: List[ValidationIssueResponse] = []


class BatchConversionResponse(BaseModel):
    """Response for batch conversion."""
    total: int
    successful: int
    failed: int
    results: List[BatchResultItem]

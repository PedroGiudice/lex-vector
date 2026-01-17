"""Pydantic models for Text Extractor API."""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class EngineType(str, Enum):
    """PDF extraction engine types."""
    MARKER = "marker"
    PDFPLUMBER = "pdfplumber"


class JobStatus(str, Enum):
    """Job processing status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionRequest(BaseModel):
    """Request model for PDF extraction."""
    engine: EngineType = Field(
        default=EngineType.MARKER,
        description="Extraction engine to use"
    )
    use_gemini: bool = Field(
        default=False,
        description="Use Gemini for post-processing"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Engine-specific options"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "engine": "marker",
                "use_gemini": False,
                "options": {
                    "low_memory_mode": True
                }
            }
        }


class ExtractionResponse(BaseModel):
    """Response model for extraction job submission."""
    job_id: str = Field(description="Unique job identifier")
    status: JobStatus = Field(description="Initial job status")
    created_at: datetime = Field(description="Job creation timestamp")
    estimated_completion: Optional[int] = Field(
        default=None,
        description="Estimated completion time in seconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "queued",
                "created_at": "2025-12-11T10:30:00Z",
                "estimated_completion": 300
            }
        }


class JobStatusResponse(BaseModel):
    """Response model for job status query."""
    job_id: str = Field(description="Job identifier")
    status: JobStatus = Field(description="Current job status")
    progress: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Progress percentage (0-100)"
    )
    result_url: Optional[str] = Field(
        default=None,
        description="URL to fetch results when completed"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    created_at: datetime = Field(description="Job creation timestamp")
    started_at: Optional[datetime] = Field(
        default=None,
        description="Processing start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Completion timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 45.5,
                "result_url": None,
                "error_message": None,
                "created_at": "2025-12-11T10:30:00Z",
                "started_at": "2025-12-11T10:30:15Z",
                "completed_at": None
            }
        }


class ExtractionResult(BaseModel):
    """Result model for completed extraction."""
    job_id: str = Field(description="Job identifier")
    text: str = Field(description="Extracted text content")
    pages_processed: int = Field(description="Number of pages processed")
    execution_time_seconds: float = Field(description="Total execution time")
    engine_used: EngineType = Field(description="Engine that performed extraction")
    gemini_enhanced: bool = Field(
        default=False,
        description="Whether Gemini post-processing was applied"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional extraction metadata"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "text": "Extracted document content...",
                "pages_processed": 25,
                "execution_time_seconds": 287.5,
                "engine_used": "marker",
                "gemini_enhanced": False,
                "metadata": {
                    "file_size_bytes": 2048576,
                    "ocr_applied": True
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    service: str = Field(default="text-extractor")
    version: str = Field(default="1.0.0")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Dict[str, str] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "text-extractor",
                "version": "1.0.0",
                "timestamp": "2025-12-11T10:30:00Z",
                "dependencies": {
                    "redis": "connected",
                    "celery": "running"
                }
            }
        }


class LogEntry(BaseModel):
    """Individual log entry."""
    timestamp: datetime
    level: str
    message: str


class JobLogsResponse(BaseModel):
    """Response model for job logs query."""
    job_id: str = Field(description="Job identifier")
    logs: List[LogEntry] = Field(description="List of log entries")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "logs": [
                    {
                        "timestamp": "2025-12-11T10:30:15Z",
                        "level": "INFO",
                        "message": "Job started with engine: marker"
                    }
                ]
            }
        }

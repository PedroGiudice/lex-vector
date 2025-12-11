"""
Pydantic models for API request/response schemas.

Extends the base Trello models with API-specific schemas for HTTP endpoints.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Request Schemas
# ============================================================================

class CreateCardRequest(BaseModel):
    """Request schema for creating a Trello card."""
    list_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        description="The ID of the list to create the card in",
        json_schema_extra={"example": "5f1234567890abcdef123456"}
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=16384,
        description="Card title",
        json_schema_extra={"example": "Implement user authentication"}
    )
    desc: Optional[str] = Field(
        default="",
        max_length=16384,
        description="Card description in Markdown format",
        json_schema_extra={"example": "## Requirements\n- JWT tokens\n- OAuth2 flow"}
    )
    due: Optional[str] = Field(
        default=None,
        description="Due date in ISO 8601 format",
        json_schema_extra={"example": "2025-12-31T23:59:59Z"}
    )


class MoveCardRequest(BaseModel):
    """Request schema for moving a card to a different list."""
    card_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        description="The ID of the card to move",
        json_schema_extra={"example": "5f9876543210fedcba987654"}
    )
    target_list_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        description="The ID of the destination list",
        json_schema_extra={"example": "5f1234567890abcdef123456"}
    )


class BatchCardsRequest(BaseModel):
    """Request schema for batch fetching multiple cards."""
    card_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of card IDs to fetch (maximum 10 per batch)",
        json_schema_extra={"example": ["5f1111111111111111111111", "5f2222222222222222222222"]}
    )
    include_custom_fields: bool = Field(
        default=False,
        description="Include custom field values in response"
    )
    fields: str = Field(
        default="id,name,desc,idList,url,labels,due,dueComplete,idMembers",
        description="Comma-separated list of fields to return"
    )


class SearchCardsRequest(BaseModel):
    """Request schema for searching/filtering cards on a board."""
    board_id: str = Field(
        ...,
        min_length=8,
        description="Board ID to search within",
        json_schema_extra={"example": "5f3333333333333333333333"}
    )
    labels: Optional[list[str]] = Field(
        default=None,
        description="Filter by label names (case-insensitive)",
        json_schema_extra={"example": ["Bug", "Priority"]}
    )
    member_ids: Optional[list[str]] = Field(
        default=None,
        description="Filter by assigned member IDs"
    )
    due_date_start: Optional[str] = Field(
        default=None,
        description="Filter cards due on or after this date (ISO 8601)",
        json_schema_extra={"example": "2025-11-23T00:00:00Z"}
    )
    due_date_end: Optional[str] = Field(
        default=None,
        description="Filter cards due on or before this date (ISO 8601)",
        json_schema_extra={"example": "2025-12-31T23:59:59Z"}
    )
    card_status: str = Field(
        default="open",
        description="Card status filter: 'open', 'closed', or 'all'"
    )
    include_custom_fields: bool = Field(
        default=False,
        description="Include custom field values in results"
    )


class MCPToolCallRequest(BaseModel):
    """Request schema for calling an MCP tool."""
    tool_name: str = Field(
        ...,
        description="Name of the MCP tool to call",
        json_schema_extra={"example": "trello_get_board_structure"}
    )
    arguments: dict[str, Any] = Field(
        ...,
        description="Tool-specific arguments",
        json_schema_extra={"example": {"board_id": "5f3333333333333333333333"}}
    )


# ============================================================================
# Response Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    version: str = Field(default="1.0.0")
    trello_api_connected: bool = Field(
        ...,
        description="Whether Trello API is accessible"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )


class CardResponse(BaseModel):
    """Response schema for a single Trello card."""
    id: str
    name: str
    desc: str
    id_list: str = Field(..., alias="idList")
    url: str
    labels: list[dict[str, Any]] = []
    due: Optional[str] = None
    due_complete: bool = Field(default=False, alias="dueComplete")
    id_members: list[str] = Field(default=[], alias="idMembers")
    custom_field_items: list[dict[str, Any]] = Field(
        default=[],
        alias="customFieldItems"
    )

    model_config = {
        "populate_by_name": True,
    }


class BoardResponse(BaseModel):
    """Response schema for a Trello board."""
    id: str
    name: str
    desc: str
    closed: bool
    url: str
    lists: list[dict[str, Any]] = []
    cards: list[dict[str, Any]] = []


class BoardStructureResponse(BaseModel):
    """Response schema for complete board structure."""
    board: dict[str, Any]
    lists: list[dict[str, Any]]
    cards: list[dict[str, Any]]


class MCPToolsListResponse(BaseModel):
    """Response schema for listing MCP tools."""
    tools: list[dict[str, Any]] = Field(
        ...,
        description="List of available MCP tools with their schemas"
    )


class MCPToolCallResponse(BaseModel):
    """Response schema for MCP tool call result."""
    success: bool = Field(..., description="Whether the tool call succeeded")
    result: Optional[dict[str, Any]] = Field(
        default=None,
        description="Tool execution result"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )

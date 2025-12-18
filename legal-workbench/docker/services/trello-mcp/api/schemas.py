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


# ============================================================================
# NEW Request Schemas - Cards CRUD
# ============================================================================


class UpdateCardRequest(BaseModel):
    """Request schema for updating a Trello card."""
    name: Optional[str] = Field(
        default=None,
        max_length=16384,
        description="New card title"
    )
    desc: Optional[str] = Field(
        default=None,
        max_length=16384,
        description="New card description in Markdown format"
    )
    due: Optional[str] = Field(
        default=None,
        description="Due date in ISO 8601 format"
    )
    id_members: Optional[list[str]] = Field(
        default=None,
        alias="idMembers",
        description="List of member IDs to assign"
    )
    id_labels: Optional[list[str]] = Field(
        default=None,
        alias="idLabels",
        description="List of label IDs to apply"
    )
    closed: Optional[bool] = Field(
        default=None,
        description="Set to true to archive, false to unarchive"
    )

    model_config = {
        "populate_by_name": True,
    }


class ArchiveCardRequest(BaseModel):
    """Request schema for archiving/unarchiving a card."""
    closed: bool = Field(
        ...,
        description="True to archive, False to unarchive"
    )


# ============================================================================
# NEW Request Schemas - Checklists
# ============================================================================


class CreateChecklistRequest(BaseModel):
    """Request schema for creating a checklist on a card."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=16384,
        description="Checklist name"
    )
    pos: Optional[str] = Field(
        default="bottom",
        description="Position: 'top', 'bottom', or a positive number"
    )


class AddCheckItemRequest(BaseModel):
    """Request schema for adding an item to a checklist."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=16384,
        description="Check item name"
    )
    checked: bool = Field(
        default=False,
        description="Initial state (checked or not)"
    )
    pos: Optional[str] = Field(
        default="bottom",
        description="Position: 'top', 'bottom', or a positive number"
    )


class UpdateCheckItemRequest(BaseModel):
    """Request schema for updating a check item state."""
    state: Optional[str] = Field(
        default=None,
        description="State: 'complete' or 'incomplete'"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=16384,
        description="New name for the check item"
    )


# ============================================================================
# NEW Request Schemas - Attachments
# ============================================================================


class AddAttachmentRequest(BaseModel):
    """Request schema for adding an attachment to a card."""
    url: Optional[str] = Field(
        default=None,
        description="URL to attach"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=256,
        description="Name for the attachment"
    )
    set_cover: bool = Field(
        default=False,
        alias="setCover",
        description="Set this attachment as the card cover"
    )

    model_config = {
        "populate_by_name": True,
    }


# ============================================================================
# NEW Request Schemas - Comments
# ============================================================================


class AddCommentRequest(BaseModel):
    """Request schema for adding a comment to a card."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=16384,
        description="Comment text (supports Markdown)"
    )


class UpdateCommentRequest(BaseModel):
    """Request schema for editing a comment."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=16384,
        description="New comment text"
    )


# ============================================================================
# NEW Request Schemas - Custom Fields
# ============================================================================


class UpdateCustomFieldRequest(BaseModel):
    """
    Request schema for updating a custom field value on a card.

    Value format depends on field type:
    - text: {"text": "some value"}
    - number: {"number": "42"}
    - date: {"date": "2025-12-31T00:00:00.000Z"}
    - checkbox: {"checked": "true"}
    - dropdown: use idValue instead of value
    """
    value: Optional[dict] = Field(
        default=None,
        description="Value object for text/number/date/checkbox types"
    )
    id_value: Optional[str] = Field(
        default=None,
        alias="idValue",
        description="Option ID for dropdown type fields"
    )

    model_config = {
        "populate_by_name": True,
    }


# ============================================================================
# NEW Request Schemas - Advanced Search
# ============================================================================


class AdvancedSearchRequest(BaseModel):
    """
    Request schema for server-side advanced search using Trello operators.

    Operators:
    - @member or member:name - Cards assigned to member
    - board:name - Cards in specific board
    - list:name - Cards in specific list
    - #label or label:name - Cards with label
    - due:day|week|month - Cards by due date
    - created:N - Cards created in last N days
    - has:attachments|members - Cards with specific features
    - is:open|archived - Card status
    - -operator - Negation
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query with operators (e.g., '@me #urgent due:week')"
    )
    model_types: str = Field(
        default="cards",
        description="Types to search: 'cards', 'boards', 'organizations'"
    )
    cards_limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum number of cards to return"
    )
    partial: bool = Field(
        default=True,
        description="Return partial matches"
    )


# ============================================================================
# NEW Response Schemas
# ============================================================================


class ChecklistResponse(BaseModel):
    """Response schema for a Trello checklist."""
    id: str
    name: str
    id_card: str = Field(..., alias="idCard")
    pos: float
    check_items: list[dict[str, Any]] = Field(default=[], alias="checkItems")

    model_config = {
        "populate_by_name": True,
    }


class CheckItemResponse(BaseModel):
    """Response schema for a Trello check item."""
    id: str
    name: str
    state: str  # 'complete' or 'incomplete'
    id_checklist: str = Field(..., alias="idChecklist")
    pos: float

    model_config = {
        "populate_by_name": True,
    }


class AttachmentResponse(BaseModel):
    """Response schema for a Trello attachment."""
    id: str
    name: str
    url: str
    bytes: Optional[int] = None
    date: str
    is_upload: bool = Field(default=False, alias="isUpload")
    mime_type: Optional[str] = Field(default=None, alias="mimeType")

    model_config = {
        "populate_by_name": True,
    }


class CommentResponse(BaseModel):
    """Response schema for a Trello comment (action)."""
    id: str
    type: str = "commentCard"
    date: str
    member_creator: Optional[dict] = Field(default=None, alias="memberCreator")
    data: dict  # Contains text in data.text

    model_config = {
        "populate_by_name": True,
    }


class DeleteResponse(BaseModel):
    """Response schema for delete operations."""
    success: bool = True
    message: str = Field(..., description="Confirmation message")

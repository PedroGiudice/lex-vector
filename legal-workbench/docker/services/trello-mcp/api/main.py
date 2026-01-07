"""
FastAPI application for Trello MCP service.

Production-grade REST API with rate limiting, retry logic, and comprehensive
error handling. Exposes Trello functionality via HTTP endpoints.
"""

import os
import re
import sys

# Add shared module path for logging and Sentry
sys.path.insert(0, '/app')

# Initialize Sentry BEFORE importing FastAPI for proper instrumentation
try:
    from shared.sentry_config import init_sentry
    init_sentry("trello-mcp")
except ImportError:
    pass  # Sentry not available, continue without it

# Configure structured JSON logging
import logging
from shared.logging_config import setup_logging
from shared.middleware import RequestIDMiddleware

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
logger = setup_logging("trello-mcp", level=log_level)

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import from the trello-mcp codebase
# In Docker: copied to /app/trello_src/ (PYTHONPATH includes /app)
# Locally: at ferramentas/trello-mcp/src/
if os.path.exists("/app/trello_src"):
    # Running in Docker
    from trello_src.models import (
        AddAttachmentInput,
        AddCheckItemInput,
        AddCommentInput,
        AdvancedSearchInput,
        ArchiveCardInput,
        BatchCardsInput,
        CreateCardInput,
        CreateChecklistInput,
        DeleteAttachmentInput,
        DeleteCardInput,
        DeleteCheckItemInput,
        DeleteChecklistInput,
        DeleteCommentInput,
        EnvironmentSettings,
        MoveCardInput,
        SearchCardsInput,
        UpdateCardInput,
        UpdateCheckItemInput,
        UpdateCommentInput,
        UpdateCustomFieldInput,
    )
    from trello_src.trello_client import (
        TrelloAPIError,
        TrelloAuthError,
        TrelloClient,
        TrelloRateLimitError,
    )
else:
    # Running locally - add path for development
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../ferramentas/trello-mcp/src"))
    from models import (
        AddAttachmentInput,
        AddCheckItemInput,
        AddCommentInput,
        AdvancedSearchInput,
        ArchiveCardInput,
        BatchCardsInput,
        CreateCardInput,
        CreateChecklistInput,
        DeleteAttachmentInput,
        DeleteCardInput,
        DeleteCheckItemInput,
        DeleteChecklistInput,
        DeleteCommentInput,
        EnvironmentSettings,
        MoveCardInput,
        SearchCardsInput,
        UpdateCardInput,
        UpdateCheckItemInput,
        UpdateCommentInput,
        UpdateCustomFieldInput,
    )
    from trello_client import (
        TrelloAPIError,
        TrelloAuthError,
        TrelloClient,
        TrelloRateLimitError,
    )

# Import API-specific schemas (renamed to avoid conflict with trello_src.models)
from .schemas import (
    AddAttachmentRequest,
    AddCheckItemRequest,
    AddCommentRequest,
    AdvancedSearchRequest,
    ArchiveCardRequest,
    AttachmentResponse,
    BatchCardsRequest,
    BoardResponse,
    BoardStructureResponse,
    CardResponse,
    CheckItemResponse,
    ChecklistResponse,
    CommentResponse,
    CreateCardRequest,
    CreateChecklistRequest,
    DeleteResponse,
    ErrorResponse,
    HealthResponse,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolsListResponse,
    MoveCardRequest,
    SearchCardsRequest,
    UpdateCardRequest,
    UpdateCheckItemRequest,
    UpdateCommentRequest,
    UpdateCustomFieldRequest,
)

# ============================================================================
# Application Setup
# ============================================================================

# Rate limiter: 100 requests per minute per IP
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Global Trello client (initialized on startup)
trello_client: TrelloClient | None = None
settings: EnvironmentSettings | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Initializes Trello client on startup and cleans up on shutdown.
    """
    global trello_client, settings

    # Startup: Initialize Trello client
    logger.info("Service starting", extra={"event": "startup"})
    try:
        settings = EnvironmentSettings()
        logger.info("Environment validated", extra={"event": "env_validated"})
    except ValidationError as e:
        logger.error("Environment validation failed", extra={"error": str(e)})
        raise

    async with TrelloClient(settings) as client:
        trello_client = client

        # Validate credentials on startup
        try:
            user_info = await client.validate_credentials()
            logger.info("Connected to Trello", extra={
                "event": "trello_connected",
                "user": user_info.get('fullName')
            })
        except TrelloAuthError as e:
            logger.error("Trello authentication failed", extra={"error": str(e)})
            raise

        logger.info("Application ready", extra={"event": "ready"})

        yield

        # Shutdown: Cleanup
        logger.info("Service shutting down", extra={"event": "shutdown"})
        trello_client = None


app = FastAPI(
    title="Trello MCP API",
    description="Production-grade REST API for Trello integration with rate limiting and retry logic",
    version="1.0.0",
    lifespan=lifespan,
)

# Add rate limiter middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Request ID middleware for request tracing
app.add_middleware(RequestIDMiddleware)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Helper Functions
# ============================================================================

def sanitize_error_message(error_msg: str) -> str:
    """Remove credentials from error messages."""
    error_msg = re.sub(r'key=[a-f0-9]+', 'key=***', error_msg, flags=re.IGNORECASE)
    error_msg = re.sub(r'token=[a-f0-9]+', 'token=***', error_msg, flags=re.IGNORECASE)
    return error_msg


def get_client() -> TrelloClient:
    """Get the global Trello client instance."""
    if trello_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Trello client not initialized"
        )
    return trello_client


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(TrelloAuthError)
async def trello_auth_error_handler(request: Request, exc: TrelloAuthError):
    """Handle Trello authentication errors."""
    error_msg = sanitize_error_message(str(exc))
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "authentication_failed",
            "message": f"Trello authentication failed: {error_msg}",
            "details": {
                "hint": "Check TRELLO_API_KEY and TRELLO_API_TOKEN environment variables"
            }
        }
    )


@app.exception_handler(TrelloRateLimitError)
async def trello_rate_limit_error_handler(request: Request, exc: TrelloRateLimitError):
    """Handle Trello API rate limit errors."""
    error_msg = sanitize_error_message(str(exc))
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": f"Trello API rate limit exceeded: {error_msg}",
            "details": {
                "retry_after": "10s",
                "hint": "Trello API allows 100 requests per 10 seconds per token"
            }
        }
    )


@app.exception_handler(TrelloAPIError)
async def trello_api_error_handler(request: Request, exc: TrelloAPIError):
    """Handle generic Trello API errors."""
    error_msg = sanitize_error_message(str(exc))
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "trello_api_error",
            "message": error_msg,
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Invalid request parameters",
            "details": exc.errors()
        }
    )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check"
)
@limiter.exempt
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns service status and Trello API connectivity.
    """
    trello_connected = False

    try:
        client = get_client()
        # Quick connectivity test
        await client.validate_credentials()
        trello_connected = True
    except Exception:
        pass

    return HealthResponse(
        status="healthy" if trello_connected else "degraded",
        version="1.0.0",
        trello_api_connected=trello_connected
    )


# ============================================================================
# Card Endpoints
# ============================================================================

@app.post(
    "/api/v1/cards",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Cards"],
    summary="Create a new card"
)
@limiter.limit("100/minute")
async def create_card(request: Request, card: CreateCardRequest) -> CardResponse:
    """
    Create a new Trello card.

    **Prerequisites**: You must have the exact list_id (24-character string).
    Use GET /api/v1/boards/{board_id} to discover list IDs.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    # Convert API request to internal model
    input_data = CreateCardInput(
        list_id=card.list_id,
        name=card.name,
        desc=card.desc,
        due=card.due
    )

    trello_card = await client.create_card(input_data)

    # Convert to API response
    return CardResponse(
        id=trello_card.id,
        name=trello_card.name,
        desc=trello_card.desc,
        idList=trello_card.id_list,
        url=trello_card.url,
        labels=[lbl.model_dump() for lbl in trello_card.labels],
        due=trello_card.due,
        dueComplete=trello_card.due_complete,
        idMembers=trello_card.id_members,
        customFieldItems=[item.model_dump() for item in trello_card.custom_field_items]
    )


@app.put(
    "/api/v1/cards/{card_id}/move",
    response_model=CardResponse,
    tags=["Cards"],
    summary="Move a card to a different list"
)
@limiter.limit("100/minute")
async def move_card(
    request: Request,
    card_id: str,
    move_request: MoveCardRequest
) -> CardResponse:
    """
    Move a card to a different list.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = MoveCardInput(
        card_id=card_id,
        target_list_id=move_request.target_list_id
    )

    trello_card = await client.move_card(input_data)

    return CardResponse(
        id=trello_card.id,
        name=trello_card.name,
        desc=trello_card.desc,
        idList=trello_card.id_list,
        url=trello_card.url,
        labels=[lbl.model_dump() for lbl in trello_card.labels],
        due=trello_card.due,
        dueComplete=trello_card.due_complete,
        idMembers=trello_card.id_members,
        customFieldItems=[item.model_dump() for item in trello_card.custom_field_items]
    )


@app.post(
    "/api/v1/cards/batch",
    response_model=list[CardResponse],
    tags=["Cards"],
    summary="Batch fetch multiple cards"
)
@limiter.limit("100/minute")
async def batch_get_cards(
    request: Request,
    batch_request: BatchCardsRequest
) -> list[CardResponse]:
    """
    Fetch multiple cards (up to 10) in a single efficient API call.

    **Performance**: Uses Trello's Batch API - counts as 1 request instead of N.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = BatchCardsInput(
        card_ids=batch_request.card_ids,
        include_custom_fields=batch_request.include_custom_fields,
        fields=batch_request.fields
    )

    cards = await client.batch_get_cards(input_data)

    return [
        CardResponse(
            id=card.id,
            name=card.name,
            desc=card.desc,
            idList=card.id_list,
            url=card.url,
            labels=[lbl.model_dump() for lbl in card.labels],
            due=card.due,
            dueComplete=card.due_complete,
            idMembers=card.id_members,
            customFieldItems=[item.model_dump() for item in card.custom_field_items]
        )
        for card in cards
    ]


@app.post(
    "/api/v1/cards/search",
    response_model=list[CardResponse],
    tags=["Cards"],
    summary="Search and filter cards"
)
@limiter.limit("100/minute")
async def search_cards(
    request: Request,
    search_request: SearchCardsRequest
) -> list[CardResponse]:
    """
    Search and filter cards on a board by multiple criteria.

    **Available filters**:
    - labels: Filter by label names (case-insensitive)
    - member_ids: Filter by assigned member IDs
    - due_date_start/end: Filter cards due within date range
    - card_status: 'open' (default), 'closed', or 'all'

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = SearchCardsInput(
        board_id=search_request.board_id,
        labels=search_request.labels,
        member_ids=search_request.member_ids,
        due_date_start=search_request.due_date_start,
        due_date_end=search_request.due_date_end,
        card_status=search_request.card_status,
        include_custom_fields=search_request.include_custom_fields
    )

    cards = await client.search_cards(input_data)

    return [
        CardResponse(
            id=card.id,
            name=card.name,
            desc=card.desc,
            idList=card.id_list,
            url=card.url,
            labels=[lbl.model_dump() for lbl in card.labels],
            due=card.due,
            dueComplete=card.due_complete,
            idMembers=card.id_members,
            customFieldItems=[item.model_dump() for item in card.custom_field_items]
        )
        for card in cards
    ]


# ============================================================================
# NEW Card Endpoints - CRUD Operations
# ============================================================================


@app.get(
    "/api/v1/cards/{card_id}",
    response_model=CardResponse,
    tags=["Cards"],
    summary="Get a single card"
)
@limiter.limit("100/minute")
async def get_card(request: Request, card_id: str) -> CardResponse:
    """
    Get a single card by ID with all details.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()
    card = await client.get_card(card_id)

    return CardResponse(
        id=card.id,
        name=card.name,
        desc=card.desc,
        idList=card.id_list,
        url=card.url,
        labels=[lbl.model_dump() for lbl in card.labels],
        due=card.due,
        dueComplete=card.due_complete,
        idMembers=card.id_members,
        customFieldItems=[item.model_dump() for item in card.custom_field_items]
    )


@app.put(
    "/api/v1/cards/{card_id}",
    response_model=CardResponse,
    tags=["Cards"],
    summary="Update a card"
)
@limiter.limit("100/minute")
async def update_card(
    request: Request,
    card_id: str,
    update_request: UpdateCardRequest
) -> CardResponse:
    """
    Update an existing card's properties.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = UpdateCardInput(
        card_id=card_id,
        name=update_request.name,
        desc=update_request.desc,
        due=update_request.due,
        id_members=update_request.id_members,
        id_labels=update_request.id_labels,
        closed=update_request.closed
    )

    card = await client.update_card(input_data)

    return CardResponse(
        id=card.id,
        name=card.name,
        desc=card.desc,
        idList=card.id_list,
        url=card.url,
        labels=[lbl.model_dump() for lbl in card.labels],
        due=card.due,
        dueComplete=card.due_complete,
        idMembers=card.id_members,
        customFieldItems=[item.model_dump() for item in card.custom_field_items]
    )


@app.put(
    "/api/v1/cards/{card_id}/archive",
    response_model=CardResponse,
    tags=["Cards"],
    summary="Archive or unarchive a card"
)
@limiter.limit("100/minute")
async def archive_card(
    request: Request,
    card_id: str,
    archive_request: ArchiveCardRequest
) -> CardResponse:
    """
    Archive (closed=true) or unarchive (closed=false) a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = ArchiveCardInput(
        card_id=card_id,
        closed=archive_request.closed
    )

    card = await client.archive_card(input_data)

    return CardResponse(
        id=card.id,
        name=card.name,
        desc=card.desc,
        idList=card.id_list,
        url=card.url,
        labels=[lbl.model_dump() for lbl in card.labels],
        due=card.due,
        dueComplete=card.due_complete,
        idMembers=card.id_members,
        customFieldItems=[item.model_dump() for item in card.custom_field_items]
    )


@app.delete(
    "/api/v1/cards/{card_id}",
    response_model=DeleteResponse,
    tags=["Cards"],
    summary="Permanently delete a card"
)
@limiter.limit("100/minute")
async def delete_card(request: Request, card_id: str) -> DeleteResponse:
    """
    Permanently delete a card. THIS CANNOT BE UNDONE!

    Use archive endpoint instead for safe removal.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = DeleteCardInput(card_id=card_id)
    await client.delete_card(input_data)

    return DeleteResponse(
        success=True,
        message=f"Card {card_id} permanently deleted"
    )


# ============================================================================
# Checklist Endpoints
# ============================================================================


@app.get(
    "/api/v1/cards/{card_id}/checklists",
    response_model=list[ChecklistResponse],
    tags=["Checklists"],
    summary="Get all checklists for a card"
)
@limiter.limit("100/minute")
async def get_card_checklists(request: Request, card_id: str) -> list[ChecklistResponse]:
    """
    Get all checklists and their items for a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()
    checklists = await client.get_card_checklists(card_id)

    return [
        ChecklistResponse(
            id=cl.id,
            name=cl.name,
            idCard=cl.id_card,
            pos=cl.pos,
            checkItems=[item.model_dump() for item in cl.check_items]
        )
        for cl in checklists
    ]


@app.post(
    "/api/v1/cards/{card_id}/checklists",
    response_model=ChecklistResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Checklists"],
    summary="Create a checklist on a card"
)
@limiter.limit("100/minute")
async def create_checklist(
    request: Request,
    card_id: str,
    checklist_request: CreateChecklistRequest
) -> ChecklistResponse:
    """
    Create a new checklist on a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = CreateChecklistInput(
        card_id=card_id,
        name=checklist_request.name,
        pos=checklist_request.pos
    )

    checklist = await client.create_checklist(input_data)

    return ChecklistResponse(
        id=checklist.id,
        name=checklist.name,
        idCard=checklist.id_card,
        pos=checklist.pos,
        checkItems=[item.model_dump() for item in checklist.check_items]
    )


@app.delete(
    "/api/v1/checklists/{checklist_id}",
    response_model=DeleteResponse,
    tags=["Checklists"],
    summary="Delete a checklist"
)
@limiter.limit("100/minute")
async def delete_checklist(request: Request, checklist_id: str) -> DeleteResponse:
    """
    Delete a checklist and all its items.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = DeleteChecklistInput(checklist_id=checklist_id)
    await client.delete_checklist(input_data)

    return DeleteResponse(
        success=True,
        message=f"Checklist {checklist_id} deleted"
    )


@app.post(
    "/api/v1/checklists/{checklist_id}/checkItems",
    response_model=CheckItemResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Checklists"],
    summary="Add an item to a checklist"
)
@limiter.limit("100/minute")
async def add_check_item(
    request: Request,
    checklist_id: str,
    item_request: AddCheckItemRequest
) -> CheckItemResponse:
    """
    Add a new item to a checklist.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = AddCheckItemInput(
        checklist_id=checklist_id,
        name=item_request.name,
        checked=item_request.checked,
        pos=item_request.pos
    )

    item = await client.add_check_item(input_data)

    return CheckItemResponse(
        id=item.id,
        name=item.name,
        state=item.state,
        idChecklist=item.id_checklist,
        pos=item.pos
    )


@app.put(
    "/api/v1/cards/{card_id}/checkItem/{check_item_id}",
    response_model=CheckItemResponse,
    tags=["Checklists"],
    summary="Update a check item"
)
@limiter.limit("100/minute")
async def update_check_item(
    request: Request,
    card_id: str,
    check_item_id: str,
    item_request: UpdateCheckItemRequest
) -> CheckItemResponse:
    """
    Update a check item (mark complete/incomplete or rename).

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = UpdateCheckItemInput(
        card_id=card_id,
        check_item_id=check_item_id,
        state=item_request.state,
        name=item_request.name
    )

    item = await client.update_check_item(input_data)

    return CheckItemResponse(
        id=item.id,
        name=item.name,
        state=item.state,
        idChecklist=item.id_checklist,
        pos=item.pos
    )


@app.delete(
    "/api/v1/checklists/{checklist_id}/checkItems/{check_item_id}",
    response_model=DeleteResponse,
    tags=["Checklists"],
    summary="Delete a check item"
)
@limiter.limit("100/minute")
async def delete_check_item(
    request: Request,
    checklist_id: str,
    check_item_id: str
) -> DeleteResponse:
    """
    Delete a check item from a checklist.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = DeleteCheckItemInput(
        checklist_id=checklist_id,
        check_item_id=check_item_id
    )
    await client.delete_check_item(input_data)

    return DeleteResponse(
        success=True,
        message=f"Check item {check_item_id} deleted"
    )


# ============================================================================
# Attachment Endpoints
# ============================================================================


@app.get(
    "/api/v1/cards/{card_id}/attachments",
    response_model=list[AttachmentResponse],
    tags=["Attachments"],
    summary="Get all attachments for a card"
)
@limiter.limit("100/minute")
async def get_card_attachments(request: Request, card_id: str) -> list[AttachmentResponse]:
    """
    Get all attachments for a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()
    attachments = await client.get_card_attachments(card_id)

    return [
        AttachmentResponse(
            id=att.id,
            name=att.name,
            url=att.url,
            bytes=att.bytes,
            date=att.date,
            isUpload=att.is_upload,
            mimeType=att.mime_type
        )
        for att in attachments
    ]


@app.post(
    "/api/v1/cards/{card_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Attachments"],
    summary="Add an attachment to a card"
)
@limiter.limit("100/minute")
async def add_attachment(
    request: Request,
    card_id: str,
    attachment_request: AddAttachmentRequest
) -> AttachmentResponse:
    """
    Add a URL attachment to a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = AddAttachmentInput(
        card_id=card_id,
        url=attachment_request.url,
        name=attachment_request.name,
        set_cover=attachment_request.set_cover
    )

    attachment = await client.add_attachment(input_data)

    return AttachmentResponse(
        id=attachment.id,
        name=attachment.name,
        url=attachment.url,
        bytes=attachment.bytes,
        date=attachment.date,
        isUpload=attachment.is_upload,
        mimeType=attachment.mime_type
    )


@app.delete(
    "/api/v1/cards/{card_id}/attachments/{attachment_id}",
    response_model=DeleteResponse,
    tags=["Attachments"],
    summary="Remove an attachment from a card"
)
@limiter.limit("100/minute")
async def delete_attachment(
    request: Request,
    card_id: str,
    attachment_id: str
) -> DeleteResponse:
    """
    Remove an attachment from a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = DeleteAttachmentInput(
        card_id=card_id,
        attachment_id=attachment_id
    )
    await client.delete_attachment(input_data)

    return DeleteResponse(
        success=True,
        message=f"Attachment {attachment_id} deleted"
    )


# ============================================================================
# Comment Endpoints
# ============================================================================


@app.post(
    "/api/v1/cards/{card_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Comments"],
    summary="Add a comment to a card"
)
@limiter.limit("100/minute")
async def add_comment(
    request: Request,
    card_id: str,
    comment_request: AddCommentRequest
) -> CommentResponse:
    """
    Add a comment to a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = AddCommentInput(
        card_id=card_id,
        text=comment_request.text
    )

    comment = await client.add_comment(input_data)

    return CommentResponse(
        id=comment.id,
        type=comment.type,
        date=comment.date,
        memberCreator=comment.member_creator,
        data=comment.data
    )


@app.put(
    "/api/v1/comments/{action_id}",
    response_model=CommentResponse,
    tags=["Comments"],
    summary="Edit a comment"
)
@limiter.limit("100/minute")
async def update_comment(
    request: Request,
    action_id: str,
    comment_request: UpdateCommentRequest
) -> CommentResponse:
    """
    Edit an existing comment.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = UpdateCommentInput(
        action_id=action_id,
        text=comment_request.text
    )

    comment = await client.update_comment(input_data)

    return CommentResponse(
        id=comment.id,
        type=comment.type,
        date=comment.date,
        memberCreator=comment.member_creator,
        data=comment.data
    )


@app.delete(
    "/api/v1/cards/{card_id}/comments/{action_id}",
    response_model=DeleteResponse,
    tags=["Comments"],
    summary="Delete a comment"
)
@limiter.limit("100/minute")
async def delete_comment(
    request: Request,
    card_id: str,
    action_id: str
) -> DeleteResponse:
    """
    Delete a comment from a card.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = DeleteCommentInput(
        card_id=card_id,
        action_id=action_id
    )
    await client.delete_comment(input_data)

    return DeleteResponse(
        success=True,
        message=f"Comment {action_id} deleted"
    )


# ============================================================================
# Custom Field Endpoints
# ============================================================================


@app.put(
    "/api/v1/cards/{card_id}/customField/{custom_field_id}",
    tags=["Custom Fields"],
    summary="Update a custom field value on a card"
)
@limiter.limit("100/minute")
async def update_custom_field(
    request: Request,
    card_id: str,
    custom_field_id: str,
    field_request: UpdateCustomFieldRequest
):
    """
    Update a custom field value on a card.

    Value format depends on field type:
    - text: {"value": {"text": "some value"}}
    - number: {"value": {"number": "42"}}
    - date: {"value": {"date": "2025-12-31T00:00:00.000Z"}}
    - checkbox: {"value": {"checked": "true"}}
    - dropdown: {"idValue": "option_id"}

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = UpdateCustomFieldInput(
        card_id=card_id,
        custom_field_id=custom_field_id,
        value=field_request.value,
        id_value=field_request.id_value
    )

    result = await client.update_custom_field(input_data)
    return result


# ============================================================================
# Advanced Search Endpoints
# ============================================================================


@app.post(
    "/api/v1/search/advanced",
    response_model=list[CardResponse],
    tags=["Search"],
    summary="Advanced search with Trello operators"
)
@limiter.limit("100/minute")
async def advanced_search(
    request: Request,
    search_request: AdvancedSearchRequest
) -> list[CardResponse]:
    """
    Server-side search using Trello operators.

    **Operators**:
    - @me or @username - Cards assigned to member
    - #label - Cards with label
    - due:day|week|month - Cards by due date
    - created:N - Cards created in last N days
    - has:attachments - Cards with attachments
    - is:open|archived - Card status
    - board:name - Search in specific board
    - list:name - Search in specific list

    **Examples**:
    - `@me #urgent due:week` - My urgent cards due this week
    - `board:Projetos is:open` - Open cards in Projetos board
    - `-has:members due:day` - Unassigned cards due today

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()

    input_data = AdvancedSearchInput(
        query=search_request.query,
        model_types=search_request.model_types,
        cards_limit=search_request.cards_limit,
        partial=search_request.partial
    )

    cards = await client.advanced_search(input_data)

    return [
        CardResponse(
            id=card.id,
            name=card.name,
            desc=card.desc,
            idList=card.id_list,
            url=card.url,
            labels=[lbl.model_dump() for lbl in card.labels],
            due=card.due,
            dueComplete=card.due_complete,
            idMembers=card.id_members,
            customFieldItems=[item.model_dump() for item in card.custom_field_items]
        )
        for card in cards
    ]


# ============================================================================
# Board Endpoints
# ============================================================================

@app.get(
    "/api/v1/boards",
    response_model=list[BoardResponse],
    tags=["Boards"],
    summary="List all boards"
)
@limiter.limit("100/minute")
async def list_boards(request: Request) -> list[BoardResponse]:
    """
    List all Trello boards accessible to the authenticated user.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()
    boards = await client.get_all_boards()

    return [
        BoardResponse(
            id=board.id,
            name=board.name,
            desc=board.desc,
            closed=board.closed,
            url=board.url,
            lists=[],  # Lists not included in list view
            cards=[]   # Cards not included in list view
        )
        for board in boards
    ]


@app.get(
    "/api/v1/boards/{board_id}",
    response_model=BoardStructureResponse,
    tags=["Boards"],
    summary="Get complete board structure"
)
@limiter.limit("100/minute")
async def get_board_structure(request: Request, board_id: str) -> BoardStructureResponse:
    """
    Get complete structure of a Trello board including all lists and cards.

    **Critical**: Call this endpoint BEFORE creating/moving cards to discover list IDs.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()
    structure = await client.get_board_structure(board_id)

    return BoardStructureResponse(
        board={
            "id": structure.board.id,
            "name": structure.board.name,
            "desc": structure.board.desc,
            "closed": structure.board.closed,
            "url": structure.board.url
        },
        lists=[
            {
                "id": lst.id,
                "name": lst.name,
                "closed": lst.closed,
                "idBoard": lst.id_board
            }
            for lst in structure.lists
        ],
        cards=[
            {
                "id": card.id,
                "name": card.name,
                "desc": card.desc,
                "idList": card.id_list,
                "url": card.url,
                "labels": [lbl.model_dump() for lbl in card.labels],
                "due": card.due,
                "dueComplete": card.due_complete,
                "idMembers": card.id_members
            }
            for card in structure.cards
        ]
    )


# ============================================================================
# MCP Tools Endpoints
# ============================================================================

@app.get(
    "/api/v1/mcp/tools/list",
    response_model=MCPToolsListResponse,
    tags=["MCP"],
    summary="List available MCP tools"
)
@limiter.limit("100/minute")
async def list_mcp_tools(request: Request) -> MCPToolsListResponse:
    """
    List all available MCP tools with their schemas.

    **Rate limit**: 100 requests per minute per IP.
    """
    tools = [
        {
            "name": "trello_get_board_structure",
            "description": "Get complete structure of a Trello board",
            "schema": {
                "board_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "trello_create_card",
            "description": "Create a new card in a Trello list",
            "schema": {
                "list_id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "desc": {"type": "string", "required": False},
                "due": {"type": "string", "required": False}
            }
        },
        {
            "name": "trello_move_card",
            "description": "Move a card to a different list",
            "schema": {
                "card_id": {"type": "string", "required": True},
                "target_list_id": {"type": "string", "required": True}
            }
        },
        {
            "name": "trello_list_boards",
            "description": "List all accessible Trello boards",
            "schema": {}
        },
        {
            "name": "trello_batch_get_cards",
            "description": "Fetch multiple cards in a single API call",
            "schema": {
                "card_ids": {"type": "array", "required": True},
                "include_custom_fields": {"type": "boolean", "required": False},
                "fields": {"type": "string", "required": False}
            }
        },
        {
            "name": "trello_search_cards",
            "description": "Search and filter cards on a board",
            "schema": {
                "board_id": {"type": "string", "required": True},
                "labels": {"type": "array", "required": False},
                "member_ids": {"type": "array", "required": False},
                "due_date_start": {"type": "string", "required": False},
                "due_date_end": {"type": "string", "required": False},
                "card_status": {"type": "string", "required": False},
                "include_custom_fields": {"type": "boolean", "required": False}
            }
        }
    ]

    return MCPToolsListResponse(tools=tools)


@app.post(
    "/api/v1/mcp/tools/call",
    response_model=MCPToolCallResponse,
    tags=["MCP"],
    summary="Call an MCP tool"
)
@limiter.limit("100/minute")
async def call_mcp_tool(
    request: Request,
    tool_request: MCPToolCallRequest
) -> MCPToolCallResponse:
    """
    Execute an MCP tool with the provided arguments.

    This endpoint provides a generic interface for calling any MCP tool.
    For production use, prefer the dedicated REST endpoints for better
    type safety and OpenAPI documentation.

    **Rate limit**: 100 requests per minute per IP.
    """
    client = get_client()
    tool_name = tool_request.tool_name
    arguments = tool_request.arguments

    try:
        if tool_name == "trello_get_board_structure":
            board_id = arguments.get("board_id")
            if not board_id:
                raise ValueError("Missing required argument: board_id")

            structure = await client.get_board_structure(board_id)
            return MCPToolCallResponse(
                success=True,
                result={
                    "board": structure.board.model_dump(),
                    "lists": [lst.model_dump() for lst in structure.lists],
                    "cards": [card.model_dump() for card in structure.cards]
                }
            )

        elif tool_name == "trello_create_card":
            input_data = CreateCardInput(**arguments)
            card = await client.create_card(input_data)
            return MCPToolCallResponse(
                success=True,
                result=card.model_dump()
            )

        elif tool_name == "trello_move_card":
            input_data = MoveCardInput(**arguments)
            card = await client.move_card(input_data)
            return MCPToolCallResponse(
                success=True,
                result=card.model_dump()
            )

        elif tool_name == "trello_list_boards":
            boards = await client.get_all_boards()
            return MCPToolCallResponse(
                success=True,
                result={"boards": [board.model_dump() for board in boards]}
            )

        elif tool_name == "trello_batch_get_cards":
            input_data = BatchCardsInput(**arguments)
            cards = await client.batch_get_cards(input_data)
            return MCPToolCallResponse(
                success=True,
                result={"cards": [card.model_dump() for card in cards]}
            )

        elif tool_name == "trello_search_cards":
            input_data = SearchCardsInput(**arguments)
            cards = await client.search_cards(input_data)
            return MCPToolCallResponse(
                success=True,
                result={"cards": [card.model_dump() for card in cards]}
            )

        else:
            return MCPToolCallResponse(
                success=False,
                error=f"Unknown tool: {tool_name}"
            )

    except Exception as e:
        error_msg = sanitize_error_message(str(e))
        return MCPToolCallResponse(
            success=False,
            error=error_msg
        )


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["System"])
@limiter.exempt
async def root():
    """API root endpoint with basic info."""
    return {
        "service": "Trello MCP API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/debug/sentry", tags=["Debug"])
@limiter.exempt
async def debug_sentry():
    """
    Test Sentry integration by triggering a test exception.

    This endpoint is for debugging purposes only.
    In production, this should be disabled or protected.
    """
    raise Exception("Sentry test exception from trello-mcp")

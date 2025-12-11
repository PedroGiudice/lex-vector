"""
FastAPI application for Trello MCP service.

Production-grade REST API with rate limiting, retry logic, and comprehensive
error handling. Exposes Trello functionality via HTTP endpoints.
"""

import os
import re
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import from the existing trello-mcp codebase
# We'll copy these files into the Docker image
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../ferramentas/trello-mcp/src"))

from models import (
    BatchCardsInput,
    CreateCardInput,
    EnvironmentSettings,
    MoveCardInput,
    SearchCardsInput,
)
from trello_client import (
    TrelloAPIError,
    TrelloAuthError,
    TrelloClient,
    TrelloRateLimitError,
)

# Import API-specific models
from .models import (
    BatchCardsRequest,
    BoardResponse,
    BoardStructureResponse,
    CardResponse,
    CreateCardRequest,
    ErrorResponse,
    HealthResponse,
    MCPToolCallRequest,
    MCPToolCallResponse,
    MCPToolsListResponse,
    MoveCardRequest,
    SearchCardsRequest,
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
    try:
        settings = EnvironmentSettings()
        print("[FastAPI] ✓ Environment validated", file=sys.stderr)
    except ValidationError as e:
        print(f"[FastAPI] ✗ Environment validation failed:\n{e}", file=sys.stderr)
        raise

    async with TrelloClient(settings) as client:
        trello_client = client

        # Validate credentials on startup
        try:
            user_info = await client.validate_credentials()
            print(
                f"[FastAPI] ✓ Connected to Trello as {user_info.get('fullName')}",
                file=sys.stderr
            )
        except TrelloAuthError as e:
            print(f"[FastAPI] ✗ Trello authentication failed: {e}", file=sys.stderr)
            raise

        print("[FastAPI] ✓ Application ready", file=sys.stderr)

        yield

        # Shutdown: Cleanup
        print("[FastAPI] Shutting down...", file=sys.stderr)
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

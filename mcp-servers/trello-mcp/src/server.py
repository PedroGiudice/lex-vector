"""
Trello MCP Server implementation.

This server provides Claude with full read/write access to Trello boards
via the Model Context Protocol.

CRITICAL: All logging goes to stderr. stdout is reserved for MCP protocol.
"""

import re
import sys
import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
    CallToolResult,
    GetPromptResult,
    PromptMessage,
)
from pydantic import ValidationError

from .models import (
    CreateCardInput,
    EnvironmentSettings,
    MoveCardInput,
)
from .trello_client import (
    TrelloAuthError,
    TrelloAPIError,
    TrelloClient,
)


# ============================================================================
# Helper Functions
# ============================================================================

def sanitize_error_message(error_msg: str) -> str:
    """Remove credentials from error messages."""
    error_msg = re.sub(r'key=[a-f0-9]+', 'key=***', error_msg, flags=re.IGNORECASE)
    error_msg = re.sub(r'token=[a-f0-9]+', 'token=***', error_msg, flags=re.IGNORECASE)
    return error_msg


# ============================================================================
# Tool Definitions (JSON Schema for MCP)
# ============================================================================

TOOL_GET_BOARD_STRUCTURE = Tool(
    name="trello_get_board_structure",
    description="""
    Get complete structure of a Trello board including all lists and cards.

    **CRITICAL**: You MUST call this tool BEFORE creating or moving cards to
    discover the correct list IDs. Trello requires 24-character list IDs, not names.

    This tool returns:
    - Board metadata (name, description, URL)
    - All lists with their IDs and names
    - All cards currently on the board

    Example workflow:
    1. Call trello_get_board_structure with board_id
    2. Find the target list in the response (e.g., "Backlog" → id: "abc123...")
    3. Use that list_id to create a card with trello_create_card

    Returns structured JSON with full board context.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "board_id": {
                "type": "string",
                "description": "Trello board ID or short link (e.g., 'aBc12DeF' or full ID)",
                "minLength": 8,
            }
        },
        "required": ["board_id"],
    },
)

TOOL_CREATE_CARD = Tool(
    name="trello_create_card",
    description="""
    Create a new card in a Trello list.

    **PREREQUISITES**:
    1. You MUST have the exact list_id (24-character alphanumeric string)
    2. If you don't have it, call trello_get_board_structure first
    3. Do NOT attempt to guess or construct list IDs

    The card will be created at the top of the specified list.

    Supports:
    - Title (required, max 16,384 characters)
    - Description in Markdown format (optional)
    - Due date in ISO 8601 format (optional)

    Returns the created card with its ID and URL.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "list_id": {
                "type": "string",
                "description": "Target list ID (24 characters). Get from trello_get_board_structure.",
                "minLength": 24,
                "maxLength": 24,
                "pattern": "^[a-f0-9]{24}$",
            },
            "name": {
                "type": "string",
                "description": "Card title",
                "minLength": 1,
                "maxLength": 16384,
            },
            "desc": {
                "type": "string",
                "description": "Card description (supports Markdown)",
                "maxLength": 16384,
            },
            "due": {
                "type": "string",
                "description": "Due date (ISO 8601: '2025-12-31T23:59:59Z')",
                "format": "date-time",
            },
        },
        "required": ["list_id", "name"],
    },
)

TOOL_MOVE_CARD = Tool(
    name="trello_move_card",
    description="""
    Move an existing card to a different list.

    **PREREQUISITES**:
    1. You MUST have the card_id (from trello_get_board_structure or card creation)
    2. You MUST have the target_list_id (call trello_get_board_structure if needed)

    Common use cases:
    - Move card from "To Do" → "In Progress"
    - Move card from "In Progress" → "Done"
    - Move card to "Backlog"

    Returns the updated card with new list information.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "card_id": {
                "type": "string",
                "description": "ID of the card to move (24 characters)",
                "minLength": 24,
                "maxLength": 24,
                "pattern": "^[a-f0-9]{24}$",
            },
            "target_list_id": {
                "type": "string",
                "description": "ID of destination list (24 characters)",
                "minLength": 24,
                "maxLength": 24,
                "pattern": "^[a-f0-9]{24}$",
            },
        },
        "required": ["card_id", "target_list_id"],
    },
)


# ============================================================================
# MCP Server Implementation
# ============================================================================

class TrelloMCPServer:
    """MCP Server for Trello integration."""

    def __init__(self) -> None:
        """Initialize server with environment validation."""
        # Validate environment on startup (fail-fast)
        try:
            self.settings = EnvironmentSettings()
            print(
                f"[TrelloMCPServer] ✓ Environment validated",
                file=sys.stderr
            )
        except ValidationError as e:
            print(
                f"[TrelloMCPServer] ✗ Environment validation failed:\n{e}",
                file=sys.stderr
            )
            sys.exit(1)

        self.server = Server("trello-mcp")
        self.trello_client: TrelloClient | None = None

        # Register handlers
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register MCP protocol handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                TOOL_GET_BOARD_STRUCTURE,
                TOOL_CREATE_CARD,
                TOOL_MOVE_CARD,
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
            """
            Handle tool calls.

            All errors are returned inside CallToolResult with isError=True,
            not as protocol-level errors (per MCP spec).
            """
            if not self.trello_client:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text="Server not initialized. This is an internal error."
                        )
                    ],
                    isError=True,
                )

            try:
                if name == "trello_get_board_structure":
                    return await self._handle_get_board_structure(arguments)
                elif name == "trello_create_card":
                    return await self._handle_create_card(arguments)
                elif name == "trello_move_card":
                    return await self._handle_move_card(arguments)
                else:
                    return CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text=f"Unknown tool: {name}"
                            )
                        ],
                        isError=True,
                    )

            except TrelloAuthError as e:
                error_msg = sanitize_error_message(str(e))
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Authentication failed: {error_msg}\n\n"
                                 f"Please verify your TRELLO_API_KEY and TRELLO_API_TOKEN "
                                 f"in the .env file."
                        )
                    ],
                    isError=True,
                )

            except TrelloAPIError as e:
                error_msg = sanitize_error_message(str(e))
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Trello API error: {error_msg}"
                        )
                    ],
                    isError=True,
                )

            except ValidationError as e:
                error_msg = sanitize_error_message(str(e))
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Invalid input parameters:\n{error_msg}"
                        )
                    ],
                    isError=True,
                )

            except Exception as e:
                error_msg = sanitize_error_message(str(e))
                print(f"[TrelloMCPServer] Unexpected error: {error_msg}", file=sys.stderr)
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Unexpected error: {error_msg}"
                        )
                    ],
                    isError=True,
                )

    async def _handle_get_board_structure(
        self,
        arguments: dict[str, Any]
    ) -> CallToolResult:
        """Handle get_board_structure tool call."""
        board_id = arguments.get("board_id")
        if not board_id:
            return CallToolResult(
                content=[TextContent(type="text", text="Missing board_id parameter")],
                isError=True,
            )

        assert self.trello_client is not None
        structure = await self.trello_client.get_board_structure(board_id)

        # Format response as human-readable text
        lists_text = "\n".join(
            f"  - {lst.name} (ID: {lst.id})"
            for lst in structure.lists
            if not lst.closed
        )

        cards_summary = f"\n\nTotal cards: {len(structure.cards)}"
        if structure.cards:
            cards_sample = "\n".join(
                f"  - {card.name} (List: {card.id_list})"
                for card in structure.cards[:5]
            )
            cards_text = f"{cards_summary}\nSample cards:\n{cards_sample}"
            if len(structure.cards) > 5:
                cards_text += f"\n  ... and {len(structure.cards) - 5} more"
        else:
            cards_text = cards_summary

        response_text = f"""Board: {structure.board.name}
URL: {structure.board.url}
Description: {structure.board.desc or '(no description)'}

Lists ({len(structure.lists)}):
{lists_text}
{cards_text}

💡 Use the list IDs above to create or move cards.
"""

        return CallToolResult(
            content=[TextContent(type="text", text=response_text)],
            isError=False,
        )

    async def _handle_create_card(
        self,
        arguments: dict[str, Any]
    ) -> CallToolResult:
        """Handle create_card tool call."""
        # Validate input with Pydantic
        input_data = CreateCardInput(**arguments)

        assert self.trello_client is not None
        card = await self.trello_client.create_card(input_data)

        response_text = f"""✓ Card created successfully!

Title: {card.name}
URL: {card.url}
List ID: {card.id_list}
Card ID: {card.id}
"""
        if card.desc:
            response_text += f"\nDescription: {card.desc[:100]}..."

        return CallToolResult(
            content=[TextContent(type="text", text=response_text)],
            isError=False,
        )

    async def _handle_move_card(
        self,
        arguments: dict[str, Any]
    ) -> CallToolResult:
        """Handle move_card tool call."""
        # Validate input with Pydantic
        input_data = MoveCardInput(**arguments)

        assert self.trello_client is not None
        card = await self.trello_client.move_card(input_data)

        response_text = f"""✓ Card moved successfully!

Card: {card.name}
New List ID: {card.id_list}
URL: {card.url}
"""

        return CallToolResult(
            content=[TextContent(type="text", text=response_text)],
            isError=False,
        )

    async def run(self) -> None:
        """
        Run the MCP server.

        Uses stdio transport (stdin/stdout) for communication with Claude.
        """
        print("[TrelloMCPServer] Starting server...", file=sys.stderr)

        # Initialize Trello client
        async with TrelloClient(self.settings) as client:
            self.trello_client = client

            # Validate credentials on startup
            try:
                user_info = await client.validate_credentials()
                print(
                    f"[TrelloMCPServer] ✓ Connected as {user_info.get('fullName')}",
                    file=sys.stderr
                )
            except TrelloAuthError as e:
                print(
                    f"[TrelloMCPServer] ✗ Authentication failed: {e}",
                    file=sys.stderr
                )
                print(
                    f"[TrelloMCPServer] Check your .env file credentials",
                    file=sys.stderr
                )
                sys.exit(1)

            # Run MCP server
            print("[TrelloMCPServer] ✓ Server ready", file=sys.stderr)
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )


# ============================================================================
# Entry Point
# ============================================================================

def main() -> None:
    """Main entry point."""
    server = TrelloMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

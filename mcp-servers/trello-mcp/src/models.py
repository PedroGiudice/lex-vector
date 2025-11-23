"""
Pydantic models for Trello MCP Server.

All data structures are strictly validated to ensure type safety and prevent
silent failures in the MCP protocol.
"""

import asyncio
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class EnvironmentSettings(BaseSettings):
    """
    Environment configuration with strict validation.

    Raises ValidationError on startup if required credentials are missing,
    implementing fail-fast principle.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown env vars
    )

    trello_api_key: str = Field(
        ...,
        min_length=32,
        description="Trello API Key from https://trello.com/power-ups/admin"
    )

    trello_api_token: str = Field(
        ...,
        min_length=64,
        description="Trello API Token with read/write permissions"
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )

    rate_limit_per_10_seconds: int = Field(
        default=90,
        ge=1,
        le=100,
        description="Max requests per 10 seconds (conservative default: 90)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()


class TrelloLabel(BaseModel):
    """Trello card label."""
    id: str
    name: str
    color: str

    model_config = {
        "strict": True,
        "extra": "forbid",
    }


class TrelloCard(BaseModel):
    """Trello card model with essential fields."""
    id: str
    name: str
    desc: str = ""
    id_list: str = Field(..., alias="idList")
    url: str
    labels: list[TrelloLabel] = []
    due: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "strict": True,
        "extra": "forbid",
    }


class TrelloList(BaseModel):
    """Trello list model."""
    id: str
    name: str
    closed: bool = False
    id_board: str = Field(..., alias="idBoard")

    model_config = {
        "populate_by_name": True,
        "strict": True,
        "extra": "forbid",
    }


class TrelloBoard(BaseModel):
    """Trello board model."""
    id: str
    name: str
    desc: str = ""
    closed: bool = False
    url: str

    # Optional nested resources (populated by specific endpoints)
    lists: list[TrelloList] = []
    cards: list[TrelloCard] = []

    model_config = {
        "strict": True,
        "extra": "forbid",
    }


class BoardStructure(BaseModel):
    """
    Complete board structure for context discovery.

    This model is used by the get_board_structure tool to provide
    Claude with the necessary list IDs before creating cards.
    """
    board: TrelloBoard
    lists: list[TrelloList]
    cards: list[TrelloCard]

    model_config = {
        "strict": True,
        "extra": "forbid",
    }

    def get_list_by_name(self, name: str) -> Optional[TrelloList]:
        """Find a list by name (case-insensitive)."""
        for lst in self.lists:
            if lst.name.lower() == name.lower():
                return lst
        return None


class CreateCardInput(BaseModel):
    """
    Input schema for creating a Trello card.

    IMPORTANT: Users must obtain the list_id first by calling
    get_board_structure to discover available lists.
    """
    list_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        description="The ID of the list to create the card in. "
                    "MUST be obtained from get_board_structure first."
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=16384,
        description="Card title (required)"
    )
    desc: Optional[str] = Field(
        default="",
        max_length=16384,
        description="Card description in Markdown format"
    )
    due: Optional[str] = Field(
        default=None,
        description="Due date in ISO 8601 format (e.g., '2025-12-31T23:59:59Z')"
    )


class MoveCardInput(BaseModel):
    """Input schema for moving a card to a different list."""
    card_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        description="The ID of the card to move"
    )
    target_list_id: str = Field(
        ...,
        min_length=24,
        max_length=24,
        description="The ID of the destination list"
    )


class RateLimitState(BaseModel):
    """
    Rate limit state tracking.

    Monitors API usage to preemptively throttle before hitting
    Trello's 429 errors.
    """
    requests_made: int = 0
    window_start: float = Field(default_factory=lambda: 0.0)
    max_requests: int = 90
    window_seconds: int = 10
    _lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True)

    async def can_make_request(self, current_time: float) -> bool:
        """Thread-safe rate limit check."""
        async with self._lock:
            # Reset window if expired
            if current_time - self.window_start >= self.window_seconds:
                self.requests_made = 0
                self.window_start = current_time

            return self.requests_made < self.max_requests

    async def record_request(self, current_time: float) -> None:
        """Thread-safe request recording."""
        async with self._lock:
            if current_time - self.window_start >= self.window_seconds:
                self.requests_made = 1
                self.window_start = current_time
            else:
                self.requests_made += 1

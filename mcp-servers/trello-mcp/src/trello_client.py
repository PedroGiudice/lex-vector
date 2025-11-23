"""
Trello API client with async httpx, exponential backoff, and rate limiting.

This module implements production-grade error handling and follows Trello's
rate limit best practices (100 req/10s per token).
"""

import asyncio
import sys
import time
from typing import Any, Optional

import backoff
import httpx
from pydantic import ValidationError

from .models import (
    BoardStructure,
    CreateCardInput,
    EnvironmentSettings,
    MoveCardInput,
    RateLimitState,
    TrelloBoard,
    TrelloCard,
    TrelloList,
)


class TrelloAPIError(Exception):
    """Base exception for Trello API errors."""
    pass


class TrelloAuthError(TrelloAPIError):
    """Authentication failed - do not retry."""
    pass


class TrelloRateLimitError(TrelloAPIError):
    """Rate limit exceeded - retry with backoff."""
    pass


class TrelloClient:
    """
    Production-grade Trello API client.

    Features:
    - Async httpx for non-blocking I/O
    - Exponential backoff with jitter for 429 errors
    - Proactive rate limit monitoring
    - Strict error categorization (auth vs network vs rate limit)
    """

    BASE_URL = "https://api.trello.com/1"

    def __init__(self, settings: EnvironmentSettings) -> None:
        """
        Initialize Trello client.

        Args:
            settings: Validated environment configuration
        """
        self.settings = settings
        self.rate_limit = RateLimitState(max_requests=settings.rate_limit_per_10_seconds)
        self._client: Optional[httpx.AsyncClient] = None

        # Log to stderr (stdout reserved for MCP protocol)
        print(
            f"[TrelloClient] Initialized with rate limit: "
            f"{settings.rate_limit_per_10_seconds} req/10s",
            file=sys.stderr
        )

    async def __aenter__(self) -> "TrelloClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL with authentication."""
        url = f"{self.BASE_URL}{endpoint}"
        separator = "&" if "?" in endpoint else "?"
        return (
            f"{url}{separator}"
            f"key={self.settings.trello_api_key}&"
            f"token={self.settings.trello_api_token}"
        )

    @staticmethod
    def _should_retry(exception: Exception) -> bool:
        """Determine if exception is retryable (used by backoff decorator)."""
        if isinstance(exception, httpx.HTTPStatusError):
            status = exception.response.status_code
            # Don't retry auth errors
            if status in {401, 403}:
                return False
            # Retry rate limits and server errors
            if status in {429, 500, 502, 503, 504}:
                return True
            # Don't retry other 4xx client errors
            if 400 <= status < 500:
                return False
        # Retry network errors
        if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException)):
            return True
        return False

    @backoff.on_exception(
        backoff.expo,
        (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException),
        max_tries=5,
        jitter=backoff.full_jitter,
        giveup=lambda e: not TrelloClient._should_retry(e),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any
    ) -> dict[str, Any]:
        """
        Make authenticated request with automatic retry and rate limiting.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/boards/abc123")
            **kwargs: Additional httpx request parameters

        Returns:
            Parsed JSON response

        Raises:
            TrelloAuthError: Authentication failed (401, 403)
            TrelloRateLimitError: Rate limit exceeded after retries
            TrelloAPIError: Other API errors
        """
        if not self._client:
            raise RuntimeError("Client not initialized - use async context manager")

        # Proactive rate limit check
        current_time = time.time()
        if not await self.rate_limit.can_make_request(current_time):
            wait_time = self.rate_limit.window_seconds - (
                current_time - self.rate_limit.window_start
            )
            print(
                f"[TrelloClient] Rate limit reached, waiting {wait_time:.2f}s",
                file=sys.stderr
            )
            raise TrelloRateLimitError(
                f"Rate limit of {self.rate_limit.max_requests} req/10s reached"
            )

        url = self._build_url(endpoint)

        try:
            response = await self._client.request(method, url, **kwargs)
            response.raise_for_status()

            # Record successful request for rate limiting
            await self.rate_limit.record_request(time.time())

            return response.json()

        except httpx.HTTPStatusError as e:
            status = e.response.status_code

            # Log response headers for debugging (to stderr)
            if "X-Rate-Limit-Remaining" in e.response.headers:
                print(
                    f"[TrelloClient] Rate limit remaining: "
                    f"{e.response.headers['X-Rate-Limit-Remaining']}",
                    file=sys.stderr
                )

            # Categorize errors
            if status in {401, 403}:
                raise TrelloAuthError(
                    f"Authentication failed: {e.response.text}"
                ) from e
            if status == 429:
                raise TrelloRateLimitError(
                    f"Rate limit exceeded: {e.response.text}"
                ) from e
            if status == 404:
                raise TrelloAPIError(
                    f"Resource not found: {endpoint}"
                ) from e

            # Generic API error
            raise TrelloAPIError(
                f"API error ({status}): {e.response.text}"
            ) from e

        except httpx.RequestError as e:
            raise TrelloAPIError(f"Network error: {str(e)}") from e

    # -------------------------------------------------------------------------
    # Public API Methods
    # -------------------------------------------------------------------------

    async def get_board_structure(self, board_id: str) -> BoardStructure:
        """
        Get complete board structure (board + lists + cards).

        Uses nested resources to minimize API calls (2 requests instead of N+1).

        Args:
            board_id: Trello board ID or short link

        Returns:
            BoardStructure with all lists and cards

        Raises:
            TrelloAPIError: If board doesn't exist or access denied
        """
        print(f"[TrelloClient] Fetching structure for board {board_id}", file=sys.stderr)

        # Fetch board info, lists, and cards in parallel (optimized with asyncio.gather)
        board_data, lists_data, cards_data = await asyncio.gather(
            self._request("GET", f"/boards/{board_id}"),
            self._request("GET", f"/boards/{board_id}/lists"),
            self._request("GET", f"/boards/{board_id}/cards"),
        )

        try:
            board = TrelloBoard(**board_data)
            lists = [TrelloList(**lst) for lst in lists_data]
            cards = [TrelloCard(**card) for card in cards_data]

            return BoardStructure(board=board, lists=lists, cards=cards)

        except ValidationError as e:
            print(f"[TrelloClient] Validation error: {e}", file=sys.stderr)
            raise TrelloAPIError(f"Invalid data from Trello API: {e}") from e

    async def create_card(self, input_data: CreateCardInput) -> TrelloCard:
        """
        Create a new card in a Trello list.

        Args:
            input_data: Validated card creation parameters

        Returns:
            Created TrelloCard

        Raises:
            TrelloAPIError: If list doesn't exist or creation fails
        """
        print(
            f"[TrelloClient] Creating card '{input_data.name}' "
            f"in list {input_data.list_id}",
            file=sys.stderr
        )

        params = {
            "idList": input_data.list_id,
            "name": input_data.name,
            "desc": input_data.desc or "",
        }

        if input_data.due:
            params["due"] = input_data.due

        card_data = await self._request("POST", "/cards", params=params)

        try:
            return TrelloCard(**card_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid card data: {e}") from e

    async def move_card(self, input_data: MoveCardInput) -> TrelloCard:
        """
        Move a card to a different list.

        Args:
            input_data: Validated move parameters

        Returns:
            Updated TrelloCard

        Raises:
            TrelloAPIError: If card or list doesn't exist
        """
        print(
            f"[TrelloClient] Moving card {input_data.card_id} "
            f"to list {input_data.target_list_id}",
            file=sys.stderr
        )

        card_data = await self._request(
            "PUT",
            f"/cards/{input_data.card_id}",
            params={"idList": input_data.target_list_id}
        )

        try:
            return TrelloCard(**card_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid card data: {e}") from e

    async def validate_credentials(self) -> dict[str, str]:
        """
        Validate API credentials by fetching current user.

        Returns:
            User info (id, username, fullName)

        Raises:
            TrelloAuthError: If credentials are invalid
        """
        print("[TrelloClient] Validating credentials...", file=sys.stderr)

        try:
            user_data = await self._request("GET", "/members/me?fields=id,username,fullName")
            print(
                f"[TrelloClient] ✓ Authenticated as {user_data.get('fullName')}",
                file=sys.stderr
            )
            return user_data
        except TrelloAuthError:
            print("[TrelloClient] ✗ Authentication failed", file=sys.stderr)
            raise

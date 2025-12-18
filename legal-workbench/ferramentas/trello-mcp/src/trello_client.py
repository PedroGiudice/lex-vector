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

from models import (
    AddAttachmentInput,
    AddCheckItemInput,
    AddCommentInput,
    AdvancedSearchInput,
    ArchiveCardInput,
    BatchCardsInput,
    BoardStructure,
    CreateCardInput,
    CreateChecklistInput,
    CustomFieldItem,
    DeleteAttachmentInput,
    DeleteCardInput,
    DeleteCheckItemInput,
    DeleteChecklistInput,
    DeleteCommentInput,
    EnvironmentSettings,
    MoveCardInput,
    RateLimitState,
    SearchCardsInput,
    TrelloAttachment,
    TrelloBoard,
    TrelloCard,
    TrelloChecklist,
    TrelloCheckItem,
    TrelloComment,
    TrelloList,
    UpdateCardInput,
    UpdateCheckItemInput,
    UpdateCommentInput,
    UpdateCustomFieldInput,
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

    async def get_all_boards(self) -> list[TrelloBoard]:
        """
        Get all boards for the authenticated user.

        Returns:
            List of TrelloBoard objects

        Raises:
            TrelloAPIError: If fetching boards fails
        """
        print("[TrelloClient] Fetching all boards for user", file=sys.stderr)

        boards_data = await self._request(
            "GET",
            "/members/me/boards",
            params={
                "fields": "id,name,desc,closed,url,shortUrl,prefs"
            }
        )

        try:
            boards = [TrelloBoard(**board) for board in boards_data]
            print(f"[TrelloClient] ✓ Found {len(boards)} boards", file=sys.stderr)
            return boards
        except ValidationError as e:
            print(f"[TrelloClient] Validation error: {e}", file=sys.stderr)
            raise TrelloAPIError(f"Invalid board data from Trello API: {e}") from e

    async def get_board_cards_with_custom_fields(
        self,
        board_id: str,
        card_status: str = "open"
    ) -> list[TrelloCard]:
        """
        Get all cards on a board with custom field values included.

        This method is optimized for data extraction scenarios where you need
        both description text and structured custom field values.

        Args:
            board_id: Trello board ID or short link
            card_status: Filter by status ('open', 'closed', or 'all')

        Returns:
            List of TrelloCard objects with custom field items populated

        Raises:
            TrelloAPIError: If board doesn't exist or access denied
        """
        print(
            f"[TrelloClient] Fetching {card_status} cards with custom fields "
            f"from board {board_id}",
            file=sys.stderr
        )

        cards_data = await self._request(
            "GET",
            f"/boards/{board_id}/cards",
            params={
                "filter": card_status,
                "fields": "id,name,desc,idList,url,labels,due,dueComplete,idMembers",
                "customFieldItems": "true"
            }
        )

        try:
            cards = [TrelloCard(**card) for card in cards_data]
            custom_fields_count = sum(
                len(card.custom_field_items) for card in cards
            )
            print(
                f"[TrelloClient] ✓ Found {len(cards)} cards with "
                f"{custom_fields_count} total custom field values",
                file=sys.stderr
            )
            return cards
        except ValidationError as e:
            print(f"[TrelloClient] Validation error: {e}", file=sys.stderr)
            raise TrelloAPIError(f"Invalid card data from Trello API: {e}") from e

    async def search_cards(self, input_data: SearchCardsInput) -> list[TrelloCard]:
        """
        Search and filter cards on a board.

        Note: Trello API has limited server-side filtering. Most filtering
        is performed client-side after fetching all cards from the board.

        Supported filters:
        - labels: Match cards with any of the specified label names
        - member_ids: Match cards assigned to any of the specified members
        - due_date_start/end: Match cards due within the date range

        Args:
            input_data: Validated search parameters

        Returns:
            Filtered list of TrelloCard objects

        Raises:
            TrelloAPIError: If board doesn't exist or access denied
        """
        from datetime import datetime

        print(
            f"[TrelloClient] Searching cards on board {input_data.board_id} "
            f"with filters: labels={input_data.labels}, "
            f"members={input_data.member_ids}, "
            f"due_range=({input_data.due_date_start}, {input_data.due_date_end})",
            file=sys.stderr
        )

        # Fetch all cards from board
        params = {
            "filter": input_data.card_status,
            "fields": "id,name,desc,idList,url,labels,due,dueComplete,idMembers"
        }

        if input_data.include_custom_fields:
            params["customFieldItems"] = "true"

        cards_data = await self._request(
            "GET",
            f"/boards/{input_data.board_id}/cards",
            params=params
        )

        # Parse cards
        try:
            cards = [TrelloCard(**card) for card in cards_data]
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid card data from Trello API: {e}") from e

        # Apply client-side filters
        filtered_cards = cards

        # Filter by labels (case-insensitive)
        if input_data.labels:
            label_set = {lbl.lower() for lbl in input_data.labels}
            filtered_cards = [
                card for card in filtered_cards
                if any(lbl.name.lower() in label_set for lbl in card.labels)
            ]
            print(
                f"[TrelloClient] After label filter: {len(filtered_cards)} cards",
                file=sys.stderr
            )

        # Filter by assigned members
        if input_data.member_ids:
            member_set = set(input_data.member_ids)
            filtered_cards = [
                card for card in filtered_cards
                if any(mid in member_set for mid in card.id_members)
            ]
            print(
                f"[TrelloClient] After member filter: {len(filtered_cards)} cards",
                file=sys.stderr
            )

        # Filter by due date range
        if input_data.due_date_start or input_data.due_date_end:
            def is_in_range(due_str: str) -> bool:
                if not due_str:
                    return False

                due_date = datetime.fromisoformat(due_str.replace('Z', '+00:00'))

                if input_data.due_date_start:
                    start = datetime.fromisoformat(
                        input_data.due_date_start.replace('Z', '+00:00')
                    )
                    if due_date < start:
                        return False

                if input_data.due_date_end:
                    end = datetime.fromisoformat(
                        input_data.due_date_end.replace('Z', '+00:00')
                    )
                    if due_date > end:
                        return False

                return True

            filtered_cards = [
                card for card in filtered_cards
                if card.due and is_in_range(card.due)
            ]
            print(
                f"[TrelloClient] After due date filter: {len(filtered_cards)} cards",
                file=sys.stderr
            )

        print(
            f"[TrelloClient] ✓ Search complete: {len(filtered_cards)} cards matched",
            file=sys.stderr
        )
        return filtered_cards

    async def batch_get_cards(self, input_data: BatchCardsInput) -> list[TrelloCard]:
        """
        Fetch multiple cards in a single batch request.

        This method uses Trello's Batch API to fetch up to 10 cards with a
        single API call, significantly reducing rate limit consumption and
        improving performance for bulk operations.

        IMPORTANT: The Batch API counts as 1 request toward rate limits,
        regardless of how many cards are fetched (up to 10).

        Args:
            input_data: Validated batch request parameters

        Returns:
            List of TrelloCard objects

        Raises:
            TrelloAPIError: If batch request fails
            ValidationError: If card data is invalid
        """
        print(
            f"[TrelloClient] Batch fetching {len(input_data.card_ids)} cards",
            file=sys.stderr
        )

        # Build individual card URLs for batch request
        # Format: /cards/{id}?fields=field1&fields=field2&...
        urls = []
        for card_id in input_data.card_ids:
            # Start with base URL
            url_parts = [f"/cards/{card_id}"]

            # Add fields as repeated query parameters
            field_params = [f"fields={field.strip()}" for field in input_data.fields.split(',')]
            url_parts.append("?" + "&".join(field_params))

            # Add custom fields if requested
            if input_data.include_custom_fields:
                url_parts.append("&customFieldItems=true")

            urls.append("".join(url_parts))

        # Join URLs with comma for batch request
        batch_urls = ",".join(urls)

        print(
            f"[TrelloClient] Batch URL preview (first 200 chars): {batch_urls[:200]}",
            file=sys.stderr
        )

        # Make batch request
        # Note: The /batch endpoint returns an array where each element
        # corresponds to one batched request, with status code as key
        try:
            batch_response = await self._request("GET", f"/batch?urls={batch_urls}")
        except TrelloAPIError as e:
            print(f"[TrelloClient] Batch request failed: {e}", file=sys.stderr)
            raise

        # Parse batch responses
        # Expected format: [{"200": {...card_data...}}, {"200": {...card_data...}}, ...]
        all_cards = []
        errors = []

        for i, response_obj in enumerate(batch_response):
            # Each response_obj is a dict with status code as key
            for status_code, card_data in response_obj.items():
                if status_code == "200":
                    try:
                        card = TrelloCard(**card_data)
                        all_cards.append(card)
                    except ValidationError as e:
                        errors.append(f"Card {i}: {e}")
                        print(
                            f"[TrelloClient] ⚠ Validation error for card {i}: {e}",
                            file=sys.stderr
                        )
                else:
                    errors.append(f"Card {i}: HTTP {status_code}")
                    print(
                        f"[TrelloClient] ⚠ Card {i} returned status {status_code}",
                        file=sys.stderr
                    )

        if errors and not all_cards:
            # All cards failed - this is a hard error
            raise TrelloAPIError(
                f"Batch request failed for all cards: {'; '.join(errors)}"
            )

        if errors:
            # Some cards failed - log warning but return successful ones
            print(
                f"[TrelloClient] ⚠ {len(errors)} cards failed in batch: {errors}",
                file=sys.stderr
            )

        print(
            f"[TrelloClient] ✓ Batch fetch complete: "
            f"{len(all_cards)}/{len(input_data.card_ids)} cards retrieved",
            file=sys.stderr
        )

        return all_cards

    # =========================================================================
    # NEW METHODS - Cards CRUD
    # =========================================================================

    async def get_card(self, card_id: str) -> TrelloCard:
        """
        Get a single card by ID.

        Args:
            card_id: Trello card ID

        Returns:
            TrelloCard object

        Raises:
            TrelloAPIError: If card doesn't exist
        """
        print(f"[TrelloClient] Fetching card {card_id}", file=sys.stderr)

        card_data = await self._request(
            "GET",
            f"/cards/{card_id}",
            params={
                "fields": "id,name,desc,idList,url,labels,due,dueComplete,idMembers,closed",
                "customFieldItems": "true"
            }
        )

        try:
            return TrelloCard(**card_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid card data: {e}") from e

    async def update_card(self, input_data: UpdateCardInput) -> TrelloCard:
        """
        Update an existing card.

        Args:
            input_data: Validated update parameters

        Returns:
            Updated TrelloCard

        Raises:
            TrelloAPIError: If card doesn't exist or update fails
        """
        print(
            f"[TrelloClient] Updating card {input_data.card_id}",
            file=sys.stderr
        )

        params = {}
        if input_data.name is not None:
            params["name"] = input_data.name
        if input_data.desc is not None:
            params["desc"] = input_data.desc
        if input_data.due is not None:
            params["due"] = input_data.due
        if input_data.id_members is not None:
            params["idMembers"] = ",".join(input_data.id_members)
        if input_data.id_labels is not None:
            params["idLabels"] = ",".join(input_data.id_labels)
        if input_data.closed is not None:
            params["closed"] = str(input_data.closed).lower()

        card_data = await self._request(
            "PUT",
            f"/cards/{input_data.card_id}",
            params=params
        )

        try:
            return TrelloCard(**card_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid card data: {e}") from e

    async def archive_card(self, input_data: ArchiveCardInput) -> TrelloCard:
        """
        Archive or unarchive a card.

        Args:
            input_data: Card ID and closed state

        Returns:
            Updated TrelloCard

        Raises:
            TrelloAPIError: If card doesn't exist
        """
        action = "Archiving" if input_data.closed else "Unarchiving"
        print(
            f"[TrelloClient] {action} card {input_data.card_id}",
            file=sys.stderr
        )

        card_data = await self._request(
            "PUT",
            f"/cards/{input_data.card_id}",
            params={"closed": str(input_data.closed).lower()}
        )

        try:
            return TrelloCard(**card_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid card data: {e}") from e

    async def delete_card(self, input_data: DeleteCardInput) -> bool:
        """
        Permanently delete a card. THIS CANNOT BE UNDONE!

        Args:
            input_data: Card ID to delete

        Returns:
            True if deletion was successful

        Raises:
            TrelloAPIError: If card doesn't exist or deletion fails
        """
        print(
            f"[TrelloClient] ⚠️ PERMANENTLY DELETING card {input_data.card_id}",
            file=sys.stderr
        )

        await self._request("DELETE", f"/cards/{input_data.card_id}")
        print(f"[TrelloClient] ✓ Card deleted", file=sys.stderr)
        return True

    # =========================================================================
    # NEW METHODS - Checklists
    # =========================================================================

    async def create_checklist(self, input_data: CreateChecklistInput) -> TrelloChecklist:
        """
        Create a new checklist on a card.

        Args:
            input_data: Checklist creation parameters

        Returns:
            Created TrelloChecklist

        Raises:
            TrelloAPIError: If card doesn't exist
        """
        print(
            f"[TrelloClient] Creating checklist '{input_data.name}' on card {input_data.card_id}",
            file=sys.stderr
        )

        params = {
            "idCard": input_data.card_id,
            "name": input_data.name,
        }
        if input_data.pos:
            params["pos"] = input_data.pos

        checklist_data = await self._request("POST", "/checklists", params=params)

        try:
            return TrelloChecklist(**checklist_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid checklist data: {e}") from e

    async def add_check_item(self, input_data: AddCheckItemInput) -> TrelloCheckItem:
        """
        Add an item to a checklist.

        Args:
            input_data: Check item parameters

        Returns:
            Created TrelloCheckItem

        Raises:
            TrelloAPIError: If checklist doesn't exist
        """
        print(
            f"[TrelloClient] Adding item '{input_data.name}' to checklist {input_data.checklist_id}",
            file=sys.stderr
        )

        params = {
            "name": input_data.name,
            "checked": str(input_data.checked).lower(),
        }
        if input_data.pos:
            params["pos"] = input_data.pos

        item_data = await self._request(
            "POST",
            f"/checklists/{input_data.checklist_id}/checkItems",
            params=params
        )

        try:
            return TrelloCheckItem(**item_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid check item data: {e}") from e

    async def update_check_item(self, input_data: UpdateCheckItemInput) -> TrelloCheckItem:
        """
        Update a check item (mark complete/incomplete or rename).

        Args:
            input_data: Update parameters

        Returns:
            Updated TrelloCheckItem

        Raises:
            TrelloAPIError: If card or check item doesn't exist
        """
        print(
            f"[TrelloClient] Updating check item {input_data.check_item_id} on card {input_data.card_id}",
            file=sys.stderr
        )

        params = {}
        if input_data.state is not None:
            params["state"] = input_data.state
        if input_data.name is not None:
            params["name"] = input_data.name

        item_data = await self._request(
            "PUT",
            f"/cards/{input_data.card_id}/checkItem/{input_data.check_item_id}",
            params=params
        )

        try:
            return TrelloCheckItem(**item_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid check item data: {e}") from e

    async def delete_checklist(self, input_data: DeleteChecklistInput) -> bool:
        """
        Delete a checklist.

        Args:
            input_data: Checklist ID to delete

        Returns:
            True if deletion was successful

        Raises:
            TrelloAPIError: If checklist doesn't exist
        """
        print(
            f"[TrelloClient] Deleting checklist {input_data.checklist_id}",
            file=sys.stderr
        )

        await self._request("DELETE", f"/checklists/{input_data.checklist_id}")
        print(f"[TrelloClient] ✓ Checklist deleted", file=sys.stderr)
        return True

    async def delete_check_item(self, input_data: DeleteCheckItemInput) -> bool:
        """
        Delete a check item from a checklist.

        Args:
            input_data: Checklist and check item IDs

        Returns:
            True if deletion was successful

        Raises:
            TrelloAPIError: If checklist or item doesn't exist
        """
        print(
            f"[TrelloClient] Deleting check item {input_data.check_item_id} from checklist {input_data.checklist_id}",
            file=sys.stderr
        )

        await self._request(
            "DELETE",
            f"/checklists/{input_data.checklist_id}/checkItems/{input_data.check_item_id}"
        )
        print(f"[TrelloClient] ✓ Check item deleted", file=sys.stderr)
        return True

    # =========================================================================
    # NEW METHODS - Attachments
    # =========================================================================

    async def get_card_attachments(self, card_id: str) -> list[TrelloAttachment]:
        """
        Get all attachments for a card.

        Args:
            card_id: Trello card ID

        Returns:
            List of TrelloAttachment objects

        Raises:
            TrelloAPIError: If card doesn't exist
        """
        print(f"[TrelloClient] Fetching attachments for card {card_id}", file=sys.stderr)

        attachments_data = await self._request(
            "GET",
            f"/cards/{card_id}/attachments"
        )

        try:
            attachments = [TrelloAttachment(**att) for att in attachments_data]
            print(f"[TrelloClient] ✓ Found {len(attachments)} attachments", file=sys.stderr)
            return attachments
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid attachment data: {e}") from e

    async def add_attachment(self, input_data: AddAttachmentInput) -> TrelloAttachment:
        """
        Add an attachment to a card via URL.

        Args:
            input_data: Attachment parameters (URL-based)

        Returns:
            Created TrelloAttachment

        Raises:
            TrelloAPIError: If card doesn't exist or URL is invalid
        """
        print(
            f"[TrelloClient] Adding attachment to card {input_data.card_id}",
            file=sys.stderr
        )

        params = {}
        if input_data.url:
            params["url"] = input_data.url
        if input_data.name:
            params["name"] = input_data.name
        if input_data.set_cover:
            params["setCover"] = "true"

        attachment_data = await self._request(
            "POST",
            f"/cards/{input_data.card_id}/attachments",
            params=params
        )

        try:
            return TrelloAttachment(**attachment_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid attachment data: {e}") from e

    async def delete_attachment(self, input_data: DeleteAttachmentInput) -> bool:
        """
        Remove an attachment from a card.

        Args:
            input_data: Card and attachment IDs

        Returns:
            True if deletion was successful

        Raises:
            TrelloAPIError: If card or attachment doesn't exist
        """
        print(
            f"[TrelloClient] Deleting attachment {input_data.attachment_id} from card {input_data.card_id}",
            file=sys.stderr
        )

        await self._request(
            "DELETE",
            f"/cards/{input_data.card_id}/attachments/{input_data.attachment_id}"
        )
        print(f"[TrelloClient] ✓ Attachment deleted", file=sys.stderr)
        return True

    # =========================================================================
    # NEW METHODS - Comments
    # =========================================================================

    async def add_comment(self, input_data: AddCommentInput) -> TrelloComment:
        """
        Add a comment to a card.

        Args:
            input_data: Comment text and card ID

        Returns:
            Created TrelloComment (action)

        Raises:
            TrelloAPIError: If card doesn't exist
        """
        print(
            f"[TrelloClient] Adding comment to card {input_data.card_id}",
            file=sys.stderr
        )

        comment_data = await self._request(
            "POST",
            f"/cards/{input_data.card_id}/actions/comments",
            params={"text": input_data.text}
        )

        try:
            return TrelloComment(**comment_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid comment data: {e}") from e

    async def update_comment(self, input_data: UpdateCommentInput) -> TrelloComment:
        """
        Edit an existing comment.

        Args:
            input_data: Action ID and new text

        Returns:
            Updated TrelloComment (action)

        Raises:
            TrelloAPIError: If comment action doesn't exist
        """
        print(
            f"[TrelloClient] Updating comment {input_data.action_id}",
            file=sys.stderr
        )

        comment_data = await self._request(
            "PUT",
            f"/actions/{input_data.action_id}",
            params={"text": input_data.text}
        )

        try:
            return TrelloComment(**comment_data)
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid comment data: {e}") from e

    async def delete_comment(self, input_data: DeleteCommentInput) -> bool:
        """
        Delete a comment from a card.

        Args:
            input_data: Card and action IDs

        Returns:
            True if deletion was successful

        Raises:
            TrelloAPIError: If card or comment doesn't exist
        """
        print(
            f"[TrelloClient] Deleting comment {input_data.action_id} from card {input_data.card_id}",
            file=sys.stderr
        )

        await self._request(
            "DELETE",
            f"/cards/{input_data.card_id}/actions/{input_data.action_id}/comments"
        )
        print(f"[TrelloClient] ✓ Comment deleted", file=sys.stderr)
        return True

    # =========================================================================
    # NEW METHODS - Custom Fields
    # =========================================================================

    async def update_custom_field(self, input_data: UpdateCustomFieldInput) -> dict:
        """
        Update a custom field value on a card.

        Args:
            input_data: Card ID, field ID, and value

        Returns:
            Updated custom field item data

        Raises:
            TrelloAPIError: If card or field doesn't exist
        """
        print(
            f"[TrelloClient] Updating custom field {input_data.custom_field_id} on card {input_data.card_id}",
            file=sys.stderr
        )

        # Build request body based on value type
        json_body = {}
        if input_data.value is not None:
            json_body["value"] = input_data.value
        if input_data.id_value is not None:
            json_body["idValue"] = input_data.id_value

        result = await self._request(
            "PUT",
            f"/cards/{input_data.card_id}/customField/{input_data.custom_field_id}/item",
            json=json_body
        )

        print(f"[TrelloClient] ✓ Custom field updated", file=sys.stderr)
        return result

    # =========================================================================
    # NEW METHODS - Advanced Search
    # =========================================================================

    async def advanced_search(self, input_data: AdvancedSearchInput) -> list[TrelloCard]:
        """
        Server-side search using Trello operators.

        Operators:
        - @me or @username - Cards assigned to member
        - #label - Cards with label
        - due:day|week|month - Cards by due date
        - created:N - Cards created in last N days
        - has:attachments - Cards with attachments
        - is:open|archived - Card status
        - board:name - Search in specific board
        - list:name - Search in specific list

        Args:
            input_data: Search query and options

        Returns:
            List of matching TrelloCard objects

        Raises:
            TrelloAPIError: If search fails
        """
        print(
            f"[TrelloClient] Advanced search: '{input_data.query}'",
            file=sys.stderr
        )

        search_data = await self._request(
            "GET",
            "/search",
            params={
                "query": input_data.query,
                "modelTypes": input_data.model_types,
                "cards_limit": input_data.cards_limit,
                "partial": str(input_data.partial).lower()
            }
        )

        # Parse cards from search results
        cards_data = search_data.get("cards", [])

        try:
            cards = [TrelloCard(**card) for card in cards_data]
            print(
                f"[TrelloClient] ✓ Search found {len(cards)} cards",
                file=sys.stderr
            )
            return cards
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid search result data: {e}") from e

    async def get_card_checklists(self, card_id: str) -> list[TrelloChecklist]:
        """
        Get all checklists for a card.

        Args:
            card_id: Trello card ID

        Returns:
            List of TrelloChecklist objects with check items

        Raises:
            TrelloAPIError: If card doesn't exist
        """
        print(f"[TrelloClient] Fetching checklists for card {card_id}", file=sys.stderr)

        checklists_data = await self._request(
            "GET",
            f"/cards/{card_id}/checklists",
            params={"checkItems": "all"}
        )

        try:
            checklists = [TrelloChecklist(**cl) for cl in checklists_data]
            print(f"[TrelloClient] ✓ Found {len(checklists)} checklists", file=sys.stderr)
            return checklists
        except ValidationError as e:
            raise TrelloAPIError(f"Invalid checklist data: {e}") from e

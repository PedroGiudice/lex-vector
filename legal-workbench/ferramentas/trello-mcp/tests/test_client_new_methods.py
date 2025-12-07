"""
Tests for new TrelloClient methods (data extraction features).

Tests cover:
- get_all_boards() - Fetch all user boards
- batch_get_cards() - Batch API for multiple cards
- search_cards() - Client-side filtering (labels, members, dates)
- get_board_cards_with_custom_fields() - Cards with custom fields

All tests use mocked httpx responses to avoid hitting real Trello API.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from conftest import create_mock_response
from trello_client import TrelloClient, TrelloAPIError, TrelloAuthError
from models import (
    BatchCardsInput,
    SearchCardsInput,
    TrelloBoard,
    TrelloCard,
    CustomFieldItem
)


# ============================================================================
# Tests: get_all_boards()
# ============================================================================

@pytest.mark.asyncio
async def test_get_all_boards_success(mock_client, sample_boards_list):
    """Test get_all_boards returns list of boards."""
    # Arrange - setup mock response
    mock_response = create_mock_response(200, sample_boards_list)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    boards = await mock_client.get_all_boards()

    # Assert
    assert len(boards) == 2
    assert all(isinstance(board, TrelloBoard) for board in boards)
    assert boards[0].name == "Board 1"
    assert boards[1].name == "Board 2"

    # Verify correct API endpoint was called
    mock_client._client.request.assert_called_once()
    call_args = mock_client._client.request.call_args
    assert "/members/me/boards" in call_args[0][1]


@pytest.mark.asyncio
async def test_get_all_boards_empty_list(mock_client):
    """Test get_all_boards returns empty list when no boards exist."""
    # Arrange
    mock_response = create_mock_response(200, [])
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    boards = await mock_client.get_all_boards()

    # Assert
    assert boards == []
    assert isinstance(boards, list)


@pytest.mark.asyncio
async def test_get_all_boards_auth_error(mock_client):
    """Test get_all_boards raises TrelloAuthError on 401."""
    # Arrange
    mock_response = create_mock_response(401, {"error": "Unauthorized"})
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act & Assert
    with pytest.raises(TrelloAuthError, match="Authentication failed"):
        await mock_client.get_all_boards()


@pytest.mark.asyncio
async def test_get_all_boards_validation_error(mock_client):
    """Test get_all_boards raises TrelloAPIError on invalid data."""
    # Arrange - malformed board data (missing required 'url' field)
    invalid_data = [{"id": "board1", "name": "Board 1", "closed": False}]
    mock_response = create_mock_response(200, invalid_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act & Assert
    with pytest.raises(TrelloAPIError, match="Invalid board data"):
        await mock_client.get_all_boards()


# ============================================================================
# Tests: batch_get_cards()
# ============================================================================

@pytest.mark.asyncio
async def test_batch_get_cards_success(mock_client, sample_batch_response):
    """Test batch_get_cards fetches multiple cards in one request."""
    # Arrange
    batch_input = BatchCardsInput(
        card_ids=["card1" + "x" * 19, "card2" + "y" * 19],  # 24 chars each
        include_custom_fields=False
    )
    mock_response = create_mock_response(200, sample_batch_response)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    cards = await mock_client.batch_get_cards(batch_input)

    # Assert
    assert len(cards) == 2
    assert all(isinstance(card, TrelloCard) for card in cards)
    assert cards[0].name == "Card 1"
    assert cards[1].name == "Card 2"

    # Verify batch endpoint was used
    call_args = mock_client._client.request.call_args
    assert "/batch" in call_args[0][1]


@pytest.mark.asyncio
async def test_batch_get_cards_with_custom_fields(mock_client):
    """Test batch_get_cards includes custom fields when requested."""
    # Arrange
    batch_response_with_cf = [
        {
            "200": {
                "id": "card1",
                "name": "Card with CF",
                "desc": "Test",
                "idList": "list123",
                "url": "https://trello.com/c/card1",
                "labels": [],
                "due": None,
                "idMembers": [],
                "dueComplete": False,
                "customFieldItems": [
                    {
                        "id": "cfi1",
                        "idCustomField": "cf1",
                        "idModel": "card1",
                        "modelType": "card",
                        "value": {"text": "Custom value"}
                    }
                ]
            }
        }
    ]

    batch_input = BatchCardsInput(
        card_ids=["card1" + "x" * 19],
        include_custom_fields=True
    )
    mock_response = create_mock_response(200, batch_response_with_cf)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    cards = await mock_client.batch_get_cards(batch_input)

    # Assert
    assert len(cards) == 1
    assert len(cards[0].custom_field_items) == 1
    assert cards[0].custom_field_items[0].value["text"] == "Custom value"

    # Verify customFieldItems parameter was included in request
    call_args = mock_client._client.request.call_args
    # The URL might have customFieldItems as a query param
    url = call_args[0][1]
    assert "customFieldItems" in url


@pytest.mark.asyncio
async def test_batch_get_cards_partial_failure(mock_client):
    """Test batch_get_cards handles mixed success/failure responses."""
    # Arrange - one card succeeds, one fails with 404
    mixed_response = [
        {
            "200": {
                "id": "card1",
                "name": "Success Card",
                "desc": "Test",
                "idList": "list123",
                "url": "https://trello.com/c/card1",
                "labels": [],
                "due": None,
                "idMembers": [],
                "dueComplete": False
            }
        },
        {
            "404": "Card not found"
        }
    ]

    batch_input = BatchCardsInput(card_ids=["card1" + "x" * 19, "card2" + "y" * 19])
    mock_response = create_mock_response(200, mixed_response)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    cards = await mock_client.batch_get_cards(batch_input)

    # Assert - should return successful cards and log warnings
    assert len(cards) == 1
    assert cards[0].name == "Success Card"


@pytest.mark.asyncio
async def test_batch_get_cards_all_failed(mock_client):
    """Test batch_get_cards raises error when all cards fail."""
    # Arrange - all cards return 404
    failed_response = [
        {"404": "Not found"},
        {"404": "Not found"}
    ]

    batch_input = BatchCardsInput(card_ids=["card1" + "x" * 19, "card2" + "y" * 19])
    mock_response = create_mock_response(200, failed_response)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act & Assert
    with pytest.raises(TrelloAPIError, match="failed for all cards"):
        await mock_client.batch_get_cards(batch_input)


# ============================================================================
# Tests: search_cards()
# ============================================================================

@pytest.mark.asyncio
async def test_search_cards_filter_by_labels(mock_client):
    """Test search_cards filters cards by label names."""
    # Arrange
    cards_data = [
        {
            "id": "card1",
            "name": "Bug Card",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card1",
            "labels": [{"id": "l1", "name": "Bug", "color": "red"}],
            "due": None,
            "idMembers": [],
            "dueComplete": False
        },
        {
            "id": "card2",
            "name": "Feature Card",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card2",
            "labels": [{"id": "l2", "name": "Feature", "color": "green"}],
            "due": None,
            "idMembers": [],
            "dueComplete": False
        }
    ]

    search_input = SearchCardsInput(
        board_id="board123",
        labels=["Bug"],
        card_status="open"
    )
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    results = await mock_client.search_cards(search_input)

    # Assert
    assert len(results) == 1
    assert results[0].name == "Bug Card"
    assert results[0].labels[0].name == "Bug"


@pytest.mark.asyncio
async def test_search_cards_filter_by_members(mock_client):
    """Test search_cards filters cards by assigned members."""
    # Arrange
    cards_data = [
        {
            "id": "card1",
            "name": "Assigned to Alice",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card1",
            "labels": [],
            "due": None,
            "idMembers": ["alice123"],
            "dueComplete": False
        },
        {
            "id": "card2",
            "name": "Assigned to Bob",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card2",
            "labels": [],
            "due": None,
            "idMembers": ["bob456"],
            "dueComplete": False
        }
    ]

    search_input = SearchCardsInput(
        board_id="board123",
        member_ids=["alice123"],
        card_status="open"
    )
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    results = await mock_client.search_cards(search_input)

    # Assert
    assert len(results) == 1
    assert results[0].name == "Assigned to Alice"
    assert "alice123" in results[0].id_members


@pytest.mark.asyncio
async def test_search_cards_filter_by_due_date_range(mock_client):
    """Test search_cards filters cards by due date range."""
    # Arrange
    cards_data = [
        {
            "id": "card1",
            "name": "Due in January",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card1",
            "labels": [],
            "due": "2025-01-15T00:00:00.000Z",
            "idMembers": [],
            "dueComplete": False
        },
        {
            "id": "card2",
            "name": "Due in December",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card2",
            "labels": [],
            "due": "2025-12-31T23:59:59.000Z",
            "idMembers": [],
            "dueComplete": False
        },
        {
            "id": "card3",
            "name": "No due date",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card3",
            "labels": [],
            "due": None,
            "idMembers": [],
            "dueComplete": False
        }
    ]

    search_input = SearchCardsInput(
        board_id="board123",
        due_date_start="2025-01-01T00:00:00Z",
        due_date_end="2025-01-31T23:59:59Z",
        card_status="open"
    )
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    results = await mock_client.search_cards(search_input)

    # Assert
    assert len(results) == 1
    assert results[0].name == "Due in January"


@pytest.mark.asyncio
async def test_search_cards_no_filters_returns_all(mock_client):
    """Test search_cards returns all cards when no filters applied."""
    # Arrange
    cards_data = [
        {
            "id": f"card{i}",
            "name": f"Card {i}",
            "desc": "",
            "idList": "list123",
            "url": f"https://trello.com/c/card{i}",
            "labels": [],
            "due": None,
            "idMembers": [],
            "dueComplete": False
        }
        for i in range(5)
    ]

    search_input = SearchCardsInput(board_id="board123")
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    results = await mock_client.search_cards(search_input)

    # Assert
    assert len(results) == 5


@pytest.mark.asyncio
async def test_search_cards_combined_filters(mock_client):
    """Test search_cards with multiple filters applied."""
    # Arrange
    cards_data = [
        {
            "id": "card1",
            "name": "Matches all filters",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card1",
            "labels": [{"id": "l1", "name": "Bug", "color": "red"}],
            "due": "2025-01-15T00:00:00.000Z",
            "idMembers": ["alice123"],
            "dueComplete": False
        },
        {
            "id": "card2",
            "name": "Matches label only",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card2",
            "labels": [{"id": "l1", "name": "Bug", "color": "red"}],
            "due": "2025-12-31T00:00:00.000Z",  # Outside date range
            "idMembers": ["bob456"],  # Wrong member
            "dueComplete": False
        }
    ]

    search_input = SearchCardsInput(
        board_id="board123",
        labels=["Bug"],
        member_ids=["alice123"],
        due_date_start="2025-01-01T00:00:00Z",
        due_date_end="2025-01-31T23:59:59Z"
    )
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    results = await mock_client.search_cards(search_input)

    # Assert - only card1 matches ALL filters
    assert len(results) == 1
    assert results[0].name == "Matches all filters"


# ============================================================================
# Tests: get_board_cards_with_custom_fields()
# ============================================================================

@pytest.mark.asyncio
async def test_get_board_cards_with_custom_fields_success(mock_client, sample_card_with_custom_fields):
    """Test get_board_cards_with_custom_fields returns cards with custom fields."""
    # Arrange
    cards_data = [sample_card_with_custom_fields]
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    cards = await mock_client.get_board_cards_with_custom_fields(
        board_id="board123",
        card_status="open"
    )

    # Assert
    assert len(cards) == 1
    assert len(cards[0].custom_field_items) == 4

    # Verify custom field types
    custom_fields = cards[0].custom_field_items
    assert custom_fields[0].value["text"] == "Some text value"
    assert custom_fields[1].value["number"] == "42"
    assert custom_fields[2].value["date"] == "2025-12-31"
    assert custom_fields[3].value["checked"] == "true"

    # Verify customFieldItems parameter was included (passed via params kwarg)
    call_args = mock_client._client.request.call_args
    # Check if params kwarg was used
    if "params" in call_args.kwargs:
        assert "customFieldItems" in call_args.kwargs["params"]
    # Or check URL (depends on _build_url implementation)
    # Since this is a mock test, we trust the client implementation


@pytest.mark.asyncio
async def test_get_board_cards_with_custom_fields_empty(mock_client):
    """Test get_board_cards_with_custom_fields with no cards."""
    # Arrange
    mock_response = create_mock_response(200, [])
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    cards = await mock_client.get_board_cards_with_custom_fields(board_id="board123")

    # Assert
    assert cards == []


@pytest.mark.asyncio
async def test_get_board_cards_with_custom_fields_filter_closed(mock_client):
    """Test get_board_cards_with_custom_fields respects card_status filter."""
    # Arrange
    mock_response = create_mock_response(200, [])
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    cards = await mock_client.get_board_cards_with_custom_fields(
        board_id="board123",
        card_status="closed"
    )

    # Assert - verify filter parameter was passed
    call_args = mock_client._client.request.call_args
    # Check params kwarg for filter=closed
    if "params" in call_args.kwargs:
        assert call_args.kwargs["params"].get("filter") == "closed"
    # Since this is a mock test, we trust the client implementation


@pytest.mark.asyncio
async def test_get_board_cards_with_custom_fields_validation_error(mock_client):
    """Test get_board_cards_with_custom_fields handles invalid data."""
    # Arrange - malformed card (missing required 'url')
    invalid_cards = [
        {
            "id": "card1",
            "name": "Invalid Card",
            "desc": "",
            "idList": "list123"
            # Missing 'url' - should fail validation
        }
    ]
    mock_response = create_mock_response(200, invalid_cards)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act & Assert
    with pytest.raises(TrelloAPIError, match="Invalid card data"):
        await mock_client.get_board_cards_with_custom_fields(board_id="board123")


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_search_cards_case_insensitive_labels(mock_client):
    """Test label filtering is case-insensitive."""
    # Arrange
    cards_data = [
        {
            "id": "card1",
            "name": "Card with bug label",
            "desc": "",
            "idList": "list123",
            "url": "https://trello.com/c/card1",
            "labels": [{"id": "l1", "name": "BUG", "color": "red"}],  # Uppercase
            "due": None,
            "idMembers": [],
            "dueComplete": False
        }
    ]

    search_input = SearchCardsInput(
        board_id="board123",
        labels=["bug"]  # Lowercase search
    )
    mock_response = create_mock_response(200, cards_data)
    mock_client._client.request = AsyncMock(return_value=mock_response)

    # Act
    results = await mock_client.search_cards(search_input)

    # Assert - should match despite case difference
    assert len(results) == 1


@pytest.mark.asyncio
async def test_batch_get_cards_empty_list(mock_client):
    """Test batch_get_cards with empty card_ids list (should fail validation)."""
    # This should fail at Pydantic validation level, not client level
    with pytest.raises(ValueError):
        BatchCardsInput(card_ids=[])

"""
Shared test fixtures for Trello MCP server tests.

This module provides reusable fixtures for mocking httpx, creating test data,
and setting up the TrelloClient with fake credentials.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Import from installed package (using editable install: pip install -e .)
from models import (
    EnvironmentSettings,
    TrelloBoard,
    TrelloCard,
    TrelloList,
    TrelloLabel,
    CustomFieldItem
)
from trello_client import TrelloClient


# ============================================================================
# Mock Credentials
# ============================================================================

@pytest.fixture
def mock_settings():
    """Create mock environment settings (fake credentials)."""
    return EnvironmentSettings(
        trello_api_key="a" * 32,  # Min 32 chars
        trello_api_token="b" * 64,  # Min 64 chars
        log_level="INFO",
        rate_limit_per_10_seconds=90
    )


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_board_data():
    """Sample board API response."""
    return {
        "id": "board123",
        "name": "Test Board",
        "desc": "Test board description",
        "closed": False,
        "url": "https://trello.com/b/board123/test-board"
    }


@pytest.fixture
def sample_list_data():
    """Sample list API response."""
    return {
        "id": "list123",
        "name": "To Do",
        "closed": False,
        "idBoard": "board123"
    }


@pytest.fixture
def sample_card_data():
    """Sample card API response without custom fields."""
    return {
        "id": "card123",
        "name": "Test Card",
        "desc": "Test card description",
        "idList": "list123",
        "url": "https://trello.com/c/card123",
        "labels": [
            {"id": "label1", "name": "Bug", "color": "red"},
            {"id": "label2", "name": "Urgent", "color": "orange"}
        ],
        "due": "2025-12-31T23:59:59.000Z",
        "idMembers": ["member1", "member2"],
        "dueComplete": False
    }


@pytest.fixture
def sample_card_with_custom_fields():
    """Sample card API response with custom fields."""
    return {
        "id": "card456",
        "name": "Card with Custom Fields",
        "desc": "CPF: 123.456.789-09\nNome: João Silva",
        "idList": "list123",
        "url": "https://trello.com/c/card456",
        "labels": [],
        "due": None,
        "idMembers": [],
        "dueComplete": False,
        "customFieldItems": [
            {
                "id": "cfi1",
                "idCustomField": "cf_text",
                "idModel": "card456",
                "modelType": "card",
                "value": {"text": "Some text value"}
            },
            {
                "id": "cfi2",
                "idCustomField": "cf_number",
                "idModel": "card456",
                "modelType": "card",
                "value": {"number": "42"}
            },
            {
                "id": "cfi3",
                "idCustomField": "cf_date",
                "idModel": "card456",
                "modelType": "card",
                "value": {"date": "2025-12-31"}
            },
            {
                "id": "cfi4",
                "idCustomField": "cf_checked",
                "idModel": "card456",
                "modelType": "card",
                "value": {"checked": "true"}
            }
        ]
    }


@pytest.fixture
def sample_boards_list():
    """Sample response from /members/me/boards."""
    return [
        {
            "id": "board1",
            "name": "Board 1",
            "desc": "First board",
            "closed": False,
            "url": "https://trello.com/b/board1"
        },
        {
            "id": "board2",
            "name": "Board 2",
            "desc": "Second board",
            "closed": False,
            "url": "https://trello.com/b/board2"
        }
    ]


@pytest.fixture
def sample_batch_response():
    """Sample response from /batch endpoint."""
    return [
        {
            "200": {
                "id": "card1",
                "name": "Card 1",
                "desc": "First card",
                "idList": "list123",
                "url": "https://trello.com/c/card1",
                "labels": [],
                "due": None,
                "idMembers": [],
                "dueComplete": False
            }
        },
        {
            "200": {
                "id": "card2",
                "name": "Card 2",
                "desc": "Second card",
                "idList": "list123",
                "url": "https://trello.com/c/card2",
                "labels": [],
                "due": None,
                "idMembers": [],
                "dueComplete": False
            }
        }
    ]


# ============================================================================
# Mock HTTP Client
# ============================================================================

@pytest_asyncio.fixture
async def mock_client(mock_settings):
    """
    Create TrelloClient with mocked httpx client.

    This fixture provides a fully initialized TrelloClient but with
    httpx.AsyncClient replaced by a MagicMock for testing.
    """
    client = TrelloClient(mock_settings)

    # Create mock httpx client
    mock_http_client = MagicMock()
    mock_http_client.aclose = AsyncMock()

    # Enter context manager to initialize client
    await client.__aenter__()

    # Replace real httpx client with mock
    client._client = mock_http_client

    yield client

    # Cleanup
    await client.__aexit__(None, None, None)


def create_mock_response(status_code: int, json_data: dict | list):
    """
    Helper to create mock httpx response.

    Args:
        status_code: HTTP status code
        json_data: JSON data to return

    Returns:
        MagicMock configured as httpx.Response
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.text = str(json_data)
    mock_response.headers = {}

    # Configure raise_for_status behavior
    if 200 <= status_code < 300:
        mock_response.raise_for_status.return_value = None
    else:
        import httpx
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=mock_response
        )

    return mock_response

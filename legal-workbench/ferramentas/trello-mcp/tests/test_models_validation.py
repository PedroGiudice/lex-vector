"""
Tests for Pydantic model validation (new models).

Tests cover:
- CustomFieldItem - All value types (text, number, date, checked, option)
- BatchCardsInput - Max 10 cards, 24-char ID validation
- SearchCardsInput - Date format, card_status enum validation
- TrelloCard - Updated fields (custom_field_items, id_members, due_complete)

Focuses on validation logic, not API behavior.
"""

import pytest
from pydantic import ValidationError

from models import (
    CustomFieldItem,
    BatchCardsInput,
    SearchCardsInput,
    TrelloCard,
    TrelloLabel
)


# ============================================================================
# Tests: CustomFieldItem
# ============================================================================

def test_custom_field_item_text_value():
    """Test CustomFieldItem with text value type."""
    # Arrange & Act
    item = CustomFieldItem(
        id="cfi123",
        idCustomField="cf456",
        idModel="card789",
        modelType="card",
        value={"text": "Sample text value"}
    )

    # Assert
    assert item.id == "cfi123"
    assert item.id_custom_field == "cf456"
    assert item.value["text"] == "Sample text value"


def test_custom_field_item_number_value():
    """Test CustomFieldItem with number value type."""
    # Arrange & Act
    item = CustomFieldItem(
        id="cfi123",
        idCustomField="cf456",
        idModel="card789",
        value={"number": "42.5"}
    )

    # Assert
    assert item.value["number"] == "42.5"


def test_custom_field_item_date_value():
    """Test CustomFieldItem with date value type."""
    # Arrange & Act
    item = CustomFieldItem(
        id="cfi123",
        idCustomField="cf456",
        idModel="card789",
        value={"date": "2025-12-31"}
    )

    # Assert
    assert item.value["date"] == "2025-12-31"


def test_custom_field_item_checked_value():
    """Test CustomFieldItem with checkbox value type."""
    # Arrange & Act
    item = CustomFieldItem(
        id="cfi123",
        idCustomField="cf456",
        idModel="card789",
        value={"checked": "true"}
    )

    # Assert
    assert item.value["checked"] == "true"


def test_custom_field_item_option_value():
    """Test CustomFieldItem with dropdown option value type."""
    # Arrange & Act
    item = CustomFieldItem(
        id="cfi123",
        idCustomField="cf456",
        idModel="card789",
        value={"option": "option_id_123"}
    )

    # Assert
    assert item.value["option"] == "option_id_123"


def test_custom_field_item_missing_required_fields():
    """Test CustomFieldItem fails validation when required fields missing."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        CustomFieldItem(
            id="cfi123",
            # Missing idCustomField
            idModel="card789",
            value={"text": "value"}
        )

    errors = exc_info.value.errors()
    assert any(e["loc"] == ("idCustomField",) for e in errors)


def test_custom_field_item_forbids_extra_fields():
    """Test CustomFieldItem rejects extra fields (strict mode)."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        CustomFieldItem(
            id="cfi123",
            idCustomField="cf456",
            idModel="card789",
            value={"text": "value"},
            extraField="should fail"  # Extra field
        )

    errors = exc_info.value.errors()
    assert any(e["type"] == "extra_forbidden" for e in errors)


def test_custom_field_item_populate_by_name():
    """Test CustomFieldItem accepts both snake_case and camelCase."""
    # Using camelCase (API format)
    item1 = CustomFieldItem(
        id="cfi123",
        idCustomField="cf456",
        idModel="card789",
        modelType="card",
        value={"text": "value"}
    )

    # Using snake_case (Python format)
    item2 = CustomFieldItem(
        id="cfi123",
        id_custom_field="cf456",
        id_model="card789",
        model_type="card",
        value={"text": "value"}
    )

    # Assert - both should work
    assert item1.id_custom_field == "cf456"
    assert item2.id_custom_field == "cf456"


# ============================================================================
# Tests: BatchCardsInput
# ============================================================================

def test_batch_cards_input_valid():
    """Test BatchCardsInput with valid data."""
    # Arrange & Act
    batch = BatchCardsInput(
        card_ids=["a" * 24, "b" * 24, "c" * 24],
        include_custom_fields=True,
        fields="id,name,desc"
    )

    # Assert
    assert len(batch.card_ids) == 3
    assert batch.include_custom_fields is True
    assert batch.fields == "id,name,desc"


def test_batch_cards_input_max_10_cards():
    """Test BatchCardsInput enforces maximum 10 cards."""
    # Act & Assert - 10 cards should be OK
    batch = BatchCardsInput(card_ids=["x" * 24 for _ in range(10)])
    assert len(batch.card_ids) == 10

    # 11 cards should fail
    with pytest.raises(ValidationError) as exc_info:
        BatchCardsInput(card_ids=["x" * 24 for _ in range(11)])

    errors = exc_info.value.errors()
    assert any("max_length" in str(e) for e in errors)


def test_batch_cards_input_min_1_card():
    """Test BatchCardsInput requires at least 1 card."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        BatchCardsInput(card_ids=[])

    errors = exc_info.value.errors()
    assert any("min_length" in str(e) for e in errors)


def test_batch_cards_input_validates_24_char_ids():
    """Test BatchCardsInput validates card IDs are exactly 24 characters."""
    # Valid IDs (24 chars)
    batch = BatchCardsInput(card_ids=["a" * 24])
    assert len(batch.card_ids[0]) == 24

    # Invalid ID - too short
    with pytest.raises(ValidationError, match="must be 24 characters"):
        BatchCardsInput(card_ids=["short"])

    # Invalid ID - too long
    with pytest.raises(ValidationError, match="must be 24 characters"):
        BatchCardsInput(card_ids=["a" * 25])


def test_batch_cards_input_default_values():
    """Test BatchCardsInput uses correct default values."""
    # Arrange & Act - minimal input
    batch = BatchCardsInput(card_ids=["a" * 24])

    # Assert - check defaults
    assert batch.include_custom_fields is False
    assert batch.fields == "id,name,desc,idList,url,labels,due,dueComplete,idMembers"


# ============================================================================
# Tests: SearchCardsInput
# ============================================================================

def test_search_cards_input_valid():
    """Test SearchCardsInput with valid data."""
    # Arrange & Act
    search = SearchCardsInput(
        board_id="board123",
        labels=["Bug", "Urgent"],
        member_ids=["member1", "member2"],
        due_date_start="2025-01-01T00:00:00Z",
        due_date_end="2025-12-31T23:59:59Z",
        card_status="open",
        include_custom_fields=True
    )

    # Assert
    assert search.board_id == "board123"
    assert search.labels == ["Bug", "Urgent"]
    assert search.member_ids == ["member1", "member2"]
    assert search.card_status == "open"
    assert search.include_custom_fields is True


def test_search_cards_input_minimal():
    """Test SearchCardsInput with only required fields."""
    # Arrange & Act
    search = SearchCardsInput(board_id="board123")

    # Assert - check defaults
    assert search.board_id == "board123"
    assert search.labels is None
    assert search.member_ids is None
    assert search.due_date_start is None
    assert search.due_date_end is None
    assert search.card_status == "open"  # Default
    assert search.include_custom_fields is False  # Default


def test_search_cards_input_validates_card_status():
    """Test SearchCardsInput validates card_status enum."""
    # Valid statuses
    for status in ["open", "closed", "all"]:
        search = SearchCardsInput(board_id="board123", card_status=status)
        assert search.card_status == status

    # Invalid status
    with pytest.raises(ValidationError, match="card_status must be one of"):
        SearchCardsInput(board_id="board123", card_status="invalid")


def test_search_cards_input_board_id_min_length():
    """Test SearchCardsInput enforces minimum board_id length."""
    # Valid - 8+ chars
    search = SearchCardsInput(board_id="board123")
    assert len(search.board_id) >= 8

    # Invalid - too short
    with pytest.raises(ValidationError):
        SearchCardsInput(board_id="short")


def test_search_cards_input_optional_filters():
    """Test SearchCardsInput allows None for optional filters."""
    # Arrange & Act - explicitly set to None
    search = SearchCardsInput(
        board_id="board123",
        labels=None,
        member_ids=None,
        due_date_start=None,
        due_date_end=None
    )

    # Assert
    assert search.labels is None
    assert search.member_ids is None
    assert search.due_date_start is None
    assert search.due_date_end is None


# ============================================================================
# Tests: TrelloCard (Updated Fields)
# ============================================================================

def test_trello_card_with_custom_fields():
    """Test TrelloCard includes custom_field_items."""
    # Arrange & Act
    card = TrelloCard(
        id="card123",
        name="Test Card",
        desc="Description",
        idList="list123",
        url="https://trello.com/c/card123",
        customFieldItems=[
            {
                "id": "cfi1",
                "idCustomField": "cf1",
                "idModel": "card123",
                "value": {"text": "value"}
            }
        ]
    )

    # Assert
    assert len(card.custom_field_items) == 1
    assert card.custom_field_items[0].id == "cfi1"


def test_trello_card_with_members():
    """Test TrelloCard includes id_members list."""
    # Arrange & Act
    card = TrelloCard(
        id="card123",
        name="Test Card",
        idList="list123",
        url="https://trello.com/c/card123",
        idMembers=["member1", "member2"]
    )

    # Assert
    assert len(card.id_members) == 2
    assert "member1" in card.id_members
    assert "member2" in card.id_members


def test_trello_card_due_complete_field():
    """Test TrelloCard includes due_complete boolean."""
    # Arrange & Act - completed
    card1 = TrelloCard(
        id="card123",
        name="Completed Card",
        idList="list123",
        url="https://trello.com/c/card123",
        due="2025-12-31T23:59:59Z",
        dueComplete=True
    )

    # Not completed
    card2 = TrelloCard(
        id="card456",
        name="Incomplete Card",
        idList="list123",
        url="https://trello.com/c/card456",
        due="2025-12-31T23:59:59Z",
        dueComplete=False
    )

    # Assert
    assert card1.due_complete is True
    assert card2.due_complete is False


def test_trello_card_default_values():
    """Test TrelloCard uses correct default values."""
    # Arrange & Act - minimal card
    card = TrelloCard(
        id="card123",
        name="Minimal Card",
        idList="list123",
        url="https://trello.com/c/card123"
    )

    # Assert defaults
    assert card.desc == ""
    assert card.labels == []
    assert card.due is None
    assert card.custom_field_items == []
    assert card.id_members == []
    assert card.due_complete is False


def test_trello_card_with_labels():
    """Test TrelloCard includes labels list."""
    # Arrange & Act
    card = TrelloCard(
        id="card123",
        name="Card with labels",
        idList="list123",
        url="https://trello.com/c/card123",
        labels=[
            {"id": "label1", "name": "Bug", "color": "red"},
            {"id": "label2", "name": "Urgent", "color": "orange"}
        ]
    )

    # Assert
    assert len(card.labels) == 2
    assert isinstance(card.labels[0], TrelloLabel)
    assert card.labels[0].name == "Bug"
    assert card.labels[1].name == "Urgent"


def test_trello_card_forbids_extra_fields():
    """Test TrelloCard rejects extra fields (strict mode)."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        TrelloCard(
            id="card123",
            name="Card",
            idList="list123",
            url="https://trello.com/c/card123",
            extraField="should fail"
        )

    errors = exc_info.value.errors()
    assert any(e["type"] == "extra_forbidden" for e in errors)


def test_trello_card_populate_by_name():
    """Test TrelloCard accepts both snake_case and camelCase field names."""
    # Using camelCase (API format)
    card1 = TrelloCard(
        id="card123",
        name="Card",
        idList="list123",
        url="https://trello.com/c/card123",
        idMembers=["member1"],
        dueComplete=True,
        customFieldItems=[]
    )

    # Using snake_case (Python format)
    card2 = TrelloCard(
        id="card123",
        name="Card",
        id_list="list123",
        url="https://trello.com/c/card123",
        id_members=["member1"],
        due_complete=True,
        custom_field_items=[]
    )

    # Assert - both should work
    assert card1.id_list == "list123"
    assert card2.id_list == "list123"
    assert card1.id_members == ["member1"]
    assert card2.id_members == ["member1"]


# ============================================================================
# Integration Tests: Complex Nested Structures
# ============================================================================

def test_trello_card_complex_nested_structure():
    """Test TrelloCard with all nested structures populated."""
    # Arrange & Act
    card = TrelloCard(
        id="card123",
        name="Complex Card",
        desc="Description with **markdown**",
        idList="list123",
        url="https://trello.com/c/card123",
        labels=[
            {"id": "l1", "name": "Bug", "color": "red"},
            {"id": "l2", "name": "High Priority", "color": "orange"}
        ],
        due="2025-12-31T23:59:59.000Z",
        dueComplete=False,
        idMembers=["member1", "member2", "member3"],
        customFieldItems=[
            {
                "id": "cfi1",
                "idCustomField": "cf_text",
                "idModel": "card123",
                "value": {"text": "Text value"}
            },
            {
                "id": "cfi2",
                "idCustomField": "cf_number",
                "idModel": "card123",
                "value": {"number": "42"}
            },
            {
                "id": "cfi3",
                "idCustomField": "cf_checked",
                "idModel": "card123",
                "value": {"checked": "true"}
            }
        ]
    )

    # Assert
    assert card.name == "Complex Card"
    assert len(card.labels) == 2
    assert len(card.id_members) == 3
    assert len(card.custom_field_items) == 3
    assert card.due_complete is False

    # Verify nested objects are properly typed
    assert isinstance(card.labels[0], TrelloLabel)
    assert isinstance(card.custom_field_items[0], CustomFieldItem)


def test_validation_error_provides_clear_message():
    """Test validation errors provide helpful messages."""
    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        TrelloCard(
            id="card123",
            name="Card",
            # Missing required 'idList'
            url="https://trello.com/c/card123"
        )

    # Check error message is informative
    errors = exc_info.value.errors()
    assert len(errors) > 0
    assert any(e["loc"] == ("idList",) for e in errors)
    assert any(e["type"] == "missing" for e in errors)

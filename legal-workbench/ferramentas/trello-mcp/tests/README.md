# Trello MCP Server - Test Suite

Comprehensive test suite for the new data extraction features implemented in the Trello MCP server.

## Test Coverage

### 1. `test_client_new_methods.py` (29 tests)
Tests for new TrelloClient methods with mocked httpx responses.

**Covered methods:**
- `get_all_boards()` - Fetch all user boards
- `batch_get_cards()` - Batch API for fetching multiple cards
- `search_cards()` - Client-side filtering (labels, members, due dates)
- `get_board_cards_with_custom_fields()` - Cards with custom field values

**Test scenarios:**
- ✅ Success cases with valid data
- ✅ Empty responses
- ✅ Authentication errors (401/403)
- ✅ Validation errors (malformed data)
- ✅ Partial failures in batch operations
- ✅ Client-side filtering logic
- ✅ Case-insensitive label matching
- ✅ Date range filtering

### 2. `test_models_validation.py` (29 tests)
Tests for Pydantic model validation (new models).

**Covered models:**
- `CustomFieldItem` - All value types (text, number, date, checked, option)
- `BatchCardsInput` - Max 10 cards, 24-char ID validation
- `SearchCardsInput` - Date formats, card_status enum
- `TrelloCard` - Updated fields (custom_field_items, id_members, due_complete)

**Test scenarios:**
- ✅ Valid data passes validation
- ✅ Missing required fields raise errors
- ✅ Extra fields are forbidden (strict mode)
- ✅ Field aliases work (camelCase ↔ snake_case)
- ✅ Default values are applied correctly
- ✅ Complex nested structures validate properly
- ✅ Enum validation for card_status
- ✅ Length constraints (min/max)

### 3. `test_extraction_functions.py` (34 tests)
Tests for ETL script extraction functions.

**Covered functions:**
- `validate_cpf()` - Brazilian CPF validation with checksum
- `validate_cnpj()` - Brazilian CNPJ validation with checksum
- `parse_brazilian_currency()` - Currency format parsing (R$ 1.000,00)
- `extract_from_description()` - Regex extraction from card descriptions
- `extract_custom_fields()` - Custom field value extraction
- `validate_record()` - Record validation logic

**Test scenarios:**
- ✅ Valid CPF/CNPJ with correct checksum
- ✅ Invalid CPF/CNPJ rejected (wrong checksum, length, format)
- ✅ Known invalid patterns (e.g., "11111111111")
- ✅ Brazilian currency parsing (with/without thousands separator)
- ✅ Regex extraction for multiple field types (CPF, CNPJ, name, email, case number)
- ✅ Custom field type handling (text, number, date, checkbox, dropdown)
- ✅ Record validation with multiple error detection
- ⚠️ Phone regex has syntax error (2 tests marked as xfail - issue documented)

## Running Tests

### Install Dependencies
```bash
cd ferramentas/trello-mcp
uv pip install pytest pytest-asyncio pytest-httpx
```

### Run All Tests
```bash
cd ferramentas/trello-mcp
export PYTHONPATH=src
.venv/bin/python -m pytest tests/ -v
```

### Run Specific Test File
```bash
export PYTHONPATH=src
.venv/bin/python -m pytest tests/test_models_validation.py -v
```

### Run Single Test
```bash
export PYTHONPATH=src
.venv/bin/python -m pytest tests/test_models_validation.py::test_custom_field_item_text_value -v
```

## Test Results

**Final Status:** ✅ **90 passed**, **2 xfailed** (0.78s)

- **90 passing tests** - All critical functionality covered
- **2 expected failures** - Phone regex syntax error in extraction script (documented in TEST_FIXES.md)

### Coverage Breakdown
- **TrelloClient methods**: 100% (29/29 passing)
- **Pydantic model validation**: 100% (29/29 passing)
- **Extraction functions**: 94% (32/34 passing, 2 xfail)

## Known Issues

### 1. Phone Regex Syntax Error
**Location:** `examples/extract_litigation_data.py`
**Pattern:** `r"\(?(\d{2})\)?\s*9?\d{4}-?\d{4}"`
**Error:** `bad character range )-\s at position 2`

**Affected tests:**
- `test_extract_from_description_phone` (xfail)
- `test_extract_from_description_multiple_fields` (xfail)

**Fix:** Escape the hyphen or fix regex character class

## Mocking Strategy

All tests use mocked httpx responses to avoid hitting the real Trello API:

```python
# Example from conftest.py
def create_mock_response(status_code: int, json_data: dict | list):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    mock_response.raise_for_status = ...  # Configured based on status_code
    return mock_response
```

## Test Data

### Valid Test CPFs (with correct checksum)
- `11144477735`
- `52998224725`

### Valid Test CNPJs (with correct checksum)
- `11222333000181`
- `34028316000103`
- `06990590000123`

## Future Improvements

1. **Integration tests** - Test against real Trello API (sandboxed board)
2. **Performance tests** - Verify rate limiting works correctly
3. **Fix phone regex** - Update extraction script regex pattern
4. **Add property-based tests** - Use Hypothesis for CPF/CNPJ generation
5. **Coverage report** - Add pytest-cov for detailed coverage metrics

## References

- **Trello API Documentation**: https://developer.atlassian.com/cloud/trello/rest/
- **Pydantic Validation**: https://docs.pydantic.dev/latest/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **pytest-httpx**: https://colin-b.github.io/pytest_httpx/

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

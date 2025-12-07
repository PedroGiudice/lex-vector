# Litigation Data Extraction Script

Production-ready ETL script for extracting structured litigation data from Trello cards.

## Features

### Data Extraction
- **Brazilian Identifiers**: CPF and CNPJ with full checksum validation
- **Personal Data**: Names, phone numbers, email addresses
- **Financial Values**: Brazilian currency format (R$ 1.000,00) with proper parsing
- **Legal Data**: Case numbers (CNJ format), custom fields
- **Metadata**: Labels, due dates, card URLs

### Validation
- ✅ **CPF Validation**: Full checksum algorithm (not just length)
- ✅ **CNPJ Validation**: Full checksum algorithm (not just length)
- ✅ **Format Validation**: Email, phone, currency parsing
- ✅ **Required Fields**: Ensures at least one identifier + name

### Error Handling
- Graceful parsing failures (preserves raw values)
- Detailed error messages in separate output file
- Continues processing even if individual cards fail
- Exception handling at extraction and custom field levels

### Output
- `litigation_dataset_clean.json` - Valid records only
- `litigation_dataset_errors.json` - Invalid/failed records with error details
- Progress indicators with percentage completion
- Comprehensive extraction summary

## Usage

### Basic Usage
```bash
python3 examples/extract_litigation_data.py "Board Name"
```

### Filter by List
```bash
python3 examples/extract_litigation_data.py "Board Name" --list "Processos Ativos"
```

### Custom Output Directory
```bash
python3 examples/extract_litigation_data.py "Board Name" --output custom_output/
```

## Output Format

### Valid Records (`litigation_dataset_clean.json`)
```json
[
  {
    "card_id": "abc123",
    "card_name": "Processo João Silva",
    "card_url": "https://trello.com/c/abc123",
    "list_id": "list123",
    "labels": ["Urgente", "Civil"],
    "due_date": "2025-12-31T23:59:59.000Z",
    "description_data": {
      "cpf": "11144477735",
      "name": "João Silva",
      "email": "joao@example.com",
      "phone": "11987654321",
      "claim_value": 50000.0,
      "case_number": "1234567-89.2024.8.26.0100"
    },
    "custom_fields": {
      "field_id_1": "text_value",
      "field_id_2": 12345.67,
      "field_id_3": true
    },
    "extracted_at": "2025-11-23T10:30:00.123456"
  }
]
```

### Error Records (`litigation_dataset_errors.json`)
```json
[
  {
    "card_id": "def456",
    "card_name": "Processo Incompleto",
    "card_url": "https://trello.com/c/def456",
    "list_id": "list123",
    "labels": [],
    "due_date": null,
    "description_data": {
      "cpf": "12345678901"
    },
    "custom_fields": {},
    "extracted_at": "2025-11-23T10:30:00.456789",
    "validation_errors": [
      "Missing name field",
      "Invalid CPF checksum: 12345678901"
    ]
  }
]
```

## Regex Patterns

### CPF (Brazilian Tax ID - Individual)
- Format: `123.456.789-00` or `12345678900`
- Validation: Full checksum algorithm
- Pattern: `\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b`

### CNPJ (Brazilian Tax ID - Company)
- Format: `12.345.678/0001-90` or `12345678000190`
- Validation: Full checksum algorithm
- Pattern: `\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b`

### Currency (Brazilian Real)
- Format: `R$ 1.000,00` (dot as thousands, comma as decimal)
- Also handles: `R$ 1000,00`, `R$ 1.000`, `R$ 1000`
- Pattern: `R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?|[0-9]+(?:,[0-9]{2})?)`

### Names
- Extracts after keywords: `Nome:`, `Réu:`, `Autor:`, `Cliente:`
- Pattern: `(?:Nome|Réu|Autor|Cliente):\s*(.+?)(?:\n|$)`

### Phone Numbers
- Format: `(11) 98765-4321` or `11987654321`
- Validates: 10-11 digits (with area code)
- Pattern: `\(?(\d{2})\)?\s*9?\d{4}-?\d{4}`

### Case Numbers (CNJ Format)
- Format: `1234567-89.2024.8.26.0100`
- Pattern: `\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}`

## Validation Logic

### CPF Checksum Algorithm
1. First 9 digits used to calculate digit 10
2. First 10 digits used to calculate digit 11
3. Rejects all-same-digit patterns (e.g., `11111111111`)

### CNPJ Checksum Algorithm
1. First 12 digits used to calculate digit 13
2. First 13 digits used to calculate digit 14
3. Uses specific weight sequences for validation

## Testing

Standalone validation tests (no dependencies):
```bash
python3 examples/test_validation_standalone.py
```

Tests include:
- ✅ Valid CPF checksums
- ✅ Invalid CPF checksums
- ✅ Valid CNPJ checksums
- ✅ Invalid CNPJ checksums
- ✅ Brazilian currency parsing

## Production Improvements

### From Draft to Production

1. **Regex Fixes**
   - Fixed currency regex to properly handle Brazilian format (comma as decimal)
   - Added support for values without thousands separators

2. **Validation Enhancements**
   - Added full CPF/CNPJ checksum validation (not just length)
   - Added email format validation
   - Added phone number length validation
   - Improved error messages with specific details

3. **Error Handling**
   - Wrapped all extraction operations in try-except blocks
   - Graceful handling of regex failures
   - Preserves raw values when parsing fails
   - Continues processing even if individual cards fail

4. **Custom Field Safety**
   - Added type conversion for numeric fields (ensures float)
   - Try-except around each custom field extraction
   - Logs warnings for failed extractions

5. **Progress Indicators**
   - Shows card number and percentage completion
   - Groups output every 10 cards for readability
   - Clear status indicators (✓ VALID, ⚠ INVALID, ✗ ERROR)

6. **Output Improvements**
   - Creates output directory with `parents=True`
   - Better formatted summary with separators
   - Includes extraction timestamp in stats
   - Shows both count and percentage in summary

## Edge Cases Handled

1. **Empty Descriptions**: Returns empty dict (no crash)
2. **Malformed Currency**: Preserves raw value in `claim_value_raw`
3. **Invalid Regex Matches**: Logs warning and continues
4. **Custom Field Errors**: Logs warning and skips field
5. **Missing Custom Fields**: Empty dict (not None)
6. **Valid Checksum but Wrong CNPJ**: Caught by length validation first

## Requirements

- Python 3.10+
- Dependencies: `httpx`, `backoff`, `pydantic`, `pydantic-settings`
- Environment: `.env` file with `TRELLO_API_KEY` and `TRELLO_API_TOKEN`

## Performance Notes

- Uses async httpx for non-blocking I/O
- Rate limiting: 90 requests per 10 seconds (configurable)
- Exponential backoff on 429 errors
- Parallel board structure fetching with `asyncio.gather()`

## Security Notes

- No hardcoded credentials (uses `.env` file)
- Input validation via Pydantic models
- Proper error categorization (auth vs network vs rate limit)
- UTF-8 encoding for Brazilian Portuguese text

## Next Steps

If you need to extend the script:

1. **Add More Patterns**: Edit `REGEX_PATTERNS` dict
2. **Add Validation Rules**: Extend `validate_record()` function
3. **Add Custom Field Types**: Extend `extract_custom_fields()` function
4. **Change Output Format**: Modify record assembly in main pipeline

## License

Part of the Trello MCP Server project.

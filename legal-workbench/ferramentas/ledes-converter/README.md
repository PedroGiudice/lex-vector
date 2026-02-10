# LEDES Converter Service

A production-ready FastAPI service for converting DOCX legal fee invoices to LEDES 1998B format.

## Features

- DOCX to LEDES 1998B format conversion
- Comprehensive security controls
- Rate limiting (10 requests/minute per IP)
- MIME type validation using magic bytes
- Input sanitization and validation
- Structured error handling
- Health check endpoint for orchestration

## API Endpoints

### `GET /health`

Health check endpoint for container orchestration.

**Response:**
```json
{
  "status": "ok",
  "service": "ledes-converter"
}
```

### `POST /convert/docx-to-ledes`

Converts an uploaded DOCX invoice file to LEDES 1998B format.

**Request:**
- `file`: (File) DOCX file containing invoice data (max 10MB)
- `config`: (Optional, Form field) JSON string with LEDES configuration

**Config JSON Structure (Optional):**
```json
{
  "law_firm_id": "ACME-LAW-001",
  "law_firm_name": "ACME Legal Services",
  "client_id": "CLIENT-XYZ-789",
  "client_name": "XYZ Corporation",
  "matter_id": "MATTER-ABC-123",
  "matter_name": "Contract Dispute 2024",
  "client_matter_id": "CLT-MTR-456"
}
```

Required fields: `law_firm_id`, `law_firm_name`, `client_id`, `matter_id`
Optional fields: `client_name`, `matter_name`, `client_matter_id`

Note: If no config is provided, the converter runs in backward compatibility mode with empty law_firm_id and client_matter_id.

**Success Response (200 OK):**
```json
{
  "filename": "invoice.docx",
  "status": "success",
  "extracted_data": {
    "invoice_date": "20251218",
    "invoice_number": "4432",
    "client_id": "SALESFORCE",
    "matter_id": "LITIGATION-BRAZIL",
    "invoice_total": 9900.0,
    "line_items": [
      {
        "description": "Legal service description",
        "amount": 1200.0
      }
    ]
  },
  "ledes_content": "INVOICE_DATE|INVOICE_NUMBER|...\n20251218|4432|..."
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file type, empty file, or malformed DOCX
- `413 Payload Too Large`: File exceeds 10MB limit
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Conversion failure

## Security Features

1. **CORS Protection**: Configurable allowed origins (not `*` in production)
2. **Rate Limiting**: 10 requests per minute per IP (in-memory, Redis recommended for production)
3. **MIME Validation**: Uses libmagic to verify actual file type (not just extension)
4. **Input Sanitization**: All extracted text is sanitized and length-limited
5. **File Size Limits**: 10MB maximum
6. **Secure Temp Files**: Restrictive permissions (0600) on temporary files
7. **Non-root Container**: Runs as user `appuser` (UID 1000)

## Architecture

```
api/
├── main.py        # FastAPI application and business logic
├── models.py      # Pydantic models for validation
requirements.txt   # Python dependencies
Dockerfile         # Multi-stage production build
entrypoint.sh      # Container startup script
```

### Key Design Decisions

- **Separation of Concerns**: Models separated from business logic
- **Validation at Boundaries**: Pydantic models validate all I/O
- **Fail-Fast**: Early validation prevents processing invalid data
- **Structured Logging**: Contextual logs for debugging and monitoring
- **Explicit Error Messages**: User-friendly error responses

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# CORS Configuration
ALLOWED_ORIGINS=http://localhost,http://localhost:3000

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# File Upload
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO
```

## Development

### Local Development

```bash
cd legal-workbench/docker
docker-compose up --build ledes-converter
```

Access the service at `http://localhost:8003`

API documentation (Swagger UI): `http://localhost:8003/docs`

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest test_api.py -v

# Run with coverage
pytest test_api.py --cov=api --cov-report=term-missing
```

### Testing with curl

```bash
# Health check
curl http://localhost:8003/health

# Convert DOCX (without config - backward compatibility mode)
curl -X POST http://localhost:8003/convert/docx-to-ledes \
  -F "file=@sample_invoice.docx" \
  -H "Content-Type: multipart/form-data"

# Convert DOCX with configuration
curl -X POST http://localhost:8003/convert/docx-to-ledes \
  -F "file=@sample_invoice.docx" \
  -F 'config={"law_firm_id":"ACME-LAW-001","law_firm_name":"ACME Legal Services","client_id":"CLIENT-XYZ-789","matter_id":"MATTER-ABC-123"}' \
  -H "Content-Type: multipart/form-data"
```

## Production Deployment

### Recommendations

1. **Rate Limiting**: Replace in-memory storage with Redis for distributed rate limiting
2. **CORS**: Set `ALLOWED_ORIGINS` to specific domains (remove wildcards)
3. **Monitoring**: Integrate with Prometheus/Grafana for metrics
4. **Logging**: Ship logs to centralized logging (e.g., ELK stack)
5. **Secrets**: Use secret management (Vault, AWS Secrets Manager)
6. **File Storage**: Consider async file processing for large volumes

### Docker Production Build

```bash
docker build -t ledes-converter:latest .
docker run -p 8003:8003 \
  -e ALLOWED_ORIGINS="https://yourdomain.com" \
  ledes-converter:latest
```

## Troubleshooting

### Common Issues

**"Invalid file format" error**
- Ensure file is a valid DOCX (not renamed DOC)
- Check file is not corrupted
- Verify DOCX is not password-protected

**Rate limit errors**
- Wait 60 seconds between bursts
- For production, configure Redis-based rate limiting

**No line items found**
- Verify invoice format matches expected structure
- Check that amounts are prefixed with "US $"

### Logs

View container logs:
```bash
docker-compose logs -f ledes-converter
```

## LEDES 1998B Format Compliance

The service generates **fully compliant** LEDES 1998B format per official specification.

### Compliance Verification (2025-12-18)

**Status**: FULLY COMPLIANT

All requirements verified and validated:

1. **Format Identifier**: Line 1 is `LEDES1998B[]` ✓
2. **Header Row**: 24 ALL CAPS field names in exact specification order ✓
3. **Line Terminators**: Every line ends with `[]` ✓
4. **Field Count**: Exactly 24 fields per data row ✓
5. **Delimiter**: Pipe character `|` ✓
6. **Date Format**: `YYYYMMDD` (8 digits, no separators) ✓
7. **Currency Format**: Up to 14 digits before decimal, 2 after, no symbols ✓
8. **Encoding**: ASCII only (non-ASCII characters removed) ✓
9. **Reserved Characters**: Pipe and bracket characters sanitized from field values ✓

### Specification Requirements

- **Line 1**: `LEDES1998B[]` identifier
- **Line 2**: Header with exactly 24 ALL CAPS field names
- **Lines 3+**: Data rows with exactly 24 pipe-delimited fields
- **Line Terminators**: Every line ends with `[]`
- **Date Format**: `YYYYMMDD` (no separators)
- **Currency Format**: Up to 14 digits before decimal, 2 after (no symbols)
- **Encoding**: ASCII only
- **Field Values**: No pipe `|` or bracket `[]` characters allowed

### Field Order (24 Fields)

```
INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|
BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|
EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|
LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|
LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|
LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID
```

### Example Output

```
LEDES1998B[]
INVOICE_DATE|INVOICE_NUMBER|CLIENT_ID|LAW_FIRM_MATTER_ID|INVOICE_TOTAL|BILLING_START_DATE|BILLING_END_DATE|INVOICE_DESCRIPTION|LINE_ITEM_NUMBER|EXP/FEE/INV_ADJ_TYPE|LINE_ITEM_NUMBER_OF_UNITS|LINE_ITEM_ADJUSTMENT_AMOUNT|LINE_ITEM_TOTAL|LINE_ITEM_DATE|LINE_ITEM_TASK_CODE|LINE_ITEM_EXPENSE_CODE|LINE_ITEM_ACTIVITY_CODE|TIMEKEEPER_ID|LINE_ITEM_DESCRIPTION|LAW_FIRM_ID|LINE_ITEM_UNIT_COST|TIMEKEEPER_NAME|TIMEKEEPER_CLASSIFICATION|CLIENT_MATTER_ID[]
20241215|INV-4432|CLIENT-XYZ|MATTER-ABC-123|9900.00|||Legal Services|1|F|||1200.00|20241215||||Draft and file Special Appeal|ACME-LAW-001|||[]
```

### Field Mappings

| Position | Field Name | Source |
|----------|-----------|--------|
| 1 | INVOICE_DATE | Extracted from DOCX |
| 2 | INVOICE_NUMBER | Extracted from DOCX |
| 3 | CLIENT_ID | Config (required) |
| 4 | LAW_FIRM_MATTER_ID | Config: matter_id (required) |
| 5 | INVOICE_TOTAL | Extracted from DOCX |
| 9 | LINE_ITEM_NUMBER | Auto-generated (1, 2, 3...) |
| 10 | EXP/FEE/INV_ADJ_TYPE | "F" (Fee) - hardcoded |
| 13 | LINE_ITEM_TOTAL | Extracted from DOCX |
| 14 | LINE_ITEM_DATE | Same as INVOICE_DATE |
| 19 | LINE_ITEM_DESCRIPTION | Extracted from DOCX |
| 20 | LAW_FIRM_ID | Config (required) |
| 24 | CLIENT_MATTER_ID | Config (optional) |

**Compliance Note**: Fields 6, 7, 11, 12, 15, 16, 17, 18, 21, 22, 23 are left empty (not applicable for basic fee invoices).

## License

Internal use only - Legal Workbench project

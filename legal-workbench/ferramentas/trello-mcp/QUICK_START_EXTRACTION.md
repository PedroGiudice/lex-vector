# Quick Start: Data Extraction (Without Claude)

This guide shows how to extract data from Trello **without needing Claude**, using the standalone script.

## Prerequisites

1. **Python 3.10+** installed
2. **Trello API credentials** (get from https://trello.com/power-ups/admin)

## Setup (One-Time)

```bash
cd ferramentas/trello-mcp

# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your credentials
nano .env  # or vim, code, etc.
```

Add to `.env`:
```env
TRELLO_API_KEY=your_api_key_from_trello
TRELLO_API_TOKEN=your_token_from_trello
```

## Usage

### Interactive Mode (Easiest)

```bash
./run_extraction.sh
```

The script will:
1. ✓ Check prerequisites (Python, uv)
2. ✓ Validate credentials
3. ✓ Install dependencies automatically
4. 📋 Show your Trello boards
5. ❓ Ask which board to extract from
6. ❓ Ask if you want to filter by list (optional)
7. 🚀 Run extraction

### Direct Mode (Faster)

If you know the board name:

```bash
./run_extraction.sh "Litigation Cases"
```

With list filter:

```bash
./run_extraction.sh "Litigation Cases" "To Process"
```

## Output

After extraction completes, you'll find:

- **`output/litigation_dataset_clean.json`** - Valid records with:
  - CPF/CNPJ (validated with checksums)
  - Names, emails, phones
  - Claim values (Brazilian currency format)
  - Custom field data
  - Card metadata (URL, labels, due dates)

- **`output/litigation_dataset_errors.json`** - Records with validation errors:
  - Missing required fields
  - Invalid CPF/CNPJ checksums
  - Parsing errors
  - Detailed error messages for fixing

## Example Output

**Clean record:**
```json
{
  "card_id": "abc123...",
  "card_name": "Caso João Silva",
  "card_url": "https://trello.com/c/abc123",
  "description_data": {
    "cpf": "12345678900",
    "name": "João Silva",
    "claim_value": 10000.50,
    "email": "joao@example.com",
    "phone": "11987654321"
  },
  "custom_fields": {
    "field_abc": "Procedente",
    "field_def": 42
  },
  "extracted_at": "2025-11-23T10:30:00Z"
}
```

**Error record:**
```json
{
  "card_id": "def456...",
  "card_name": "Caso Maria Santos",
  "validation_errors": [
    "Invalid CPF checksum: 11111111111",
    "Missing name field"
  ]
}
```

## What Gets Extracted

### From Card Description (Regex)

- **CPF**: `123.456.789-00` or `12345678900` → Validated with checksum
- **CNPJ**: `12.345.678/0001-90` or `12345678000190` → Validated with checksum
- **Names**: After "Nome:", "Réu:", "Autor:", "Cliente:"
- **Currency**: `R$ 1.000,00` or `R$ 1000,00` → Converted to float
- **Phone**: `(11) 98765-4321` or `11987654321`
- **Email**: `user@example.com`
- **Case Number**: CNJ format `1234567-12.2025.1.01.0001`

### From Custom Fields (Structured)

- Text fields
- Number fields
- Date fields
- Checkbox fields (true/false)
- Dropdown options

## Common Issues

### "TRELLO_API_KEY not set"

**Solution:** Edit `.env` file and add your credentials:
```bash
nano .env
```

### "Board 'XYZ' not found"

**Solution:** Run in interactive mode to see available boards:
```bash
./run_extraction.sh
```

### "Invalid CPF checksum"

**Issue:** Card has invalid CPF in description
**Solution:** Fix the CPF in Trello card and re-run extraction

### "Permission denied: ./run_extraction.sh"

**Solution:** Make script executable:
```bash
chmod +x run_extraction.sh
```

## Advanced Usage

### Custom Output Directory

```bash
./run_extraction.sh "Board Name" --output ./my-data
```

### Filter by Multiple Criteria

Edit `examples/extract_litigation_data.py` to add filters:
- Labels
- Due date ranges
- Assigned members

### Modify Regex Patterns

Edit `REGEX_PATTERNS` in `examples/extract_litigation_data.py` to match your data format.

## Processing Extracted Data

After extraction, you can:

1. **Import to database:**
   ```python
   import json
   with open('output/litigation_dataset_clean.json') as f:
       records = json.load(f)
       # Insert into your database
   ```

2. **Generate reports:**
   ```python
   import pandas as pd
   df = pd.read_json('output/litigation_dataset_clean.json')
   df.groupby('labels').count()
   ```

3. **Fill document templates:**
   ```python
   from docxtpl import DocxTemplate

   doc = DocxTemplate('petition_template.docx')
   doc.render(records[0]['description_data'])
   doc.save('petition_filled.docx')
   ```

## Support

For issues or questions:
- Check logs in terminal output
- Review `output/litigation_dataset_errors.json` for validation details
- See full docs in `README.md`

---

**Last updated:** 2025-11-23

# Doc Assembler API

FastAPI-based REST API for generating Brazilian legal documents from templates.

## Architecture

```
legal-workbench/
├── ferramentas/legal-doc-assembler/    # Backend engine
│   └── src/
│       ├── engine.py                   # DocumentEngine class
│       └── normalizers.py              # Text normalization
└── docker/services/doc-assembler/      # API layer
    ├── api/
    │   ├── main.py                     # FastAPI application
    │   ├── models.py                   # Pydantic models
    │   └── __init__.py
    ├── Dockerfile
    ├── requirements.txt
    └── test_api.py                     # API tests
```

## Features

- **Document Generation**: Render .docx documents from templates and JSON data
- **Template Management**: List and inspect available templates
- **Data Validation**: Validate data against template requirements
- **Document Preview**: Preview rendered text without saving
- **Brazilian Formatting**: Built-in filters for CPF, CNPJ, CEP, OAB, etc.
- **Fault-Tolerant**: Undefined variables show as `{{ var_name }}` in output

## Quick Start

### Docker (Recommended)

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker

# Start service
docker-compose up doc-assembler

# Or start all services
docker-compose up
```

### Local Development

```bash
cd /home/user/Claude-Code-Projetos/legal-workbench/docker/services/doc-assembler

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn api.main:app --host 0.0.0.0 --port 8002 --reload
```

### Test API

```bash
# Install requests if needed
pip install requests

# Run test suite
python test_api.py
```

## API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "engine_version": "2.0.0",
  "timestamp": "2025-12-11T10:30:00"
}
```

---

### List Templates

```bash
GET /api/v1/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "templates/petição_inicial",
      "name": "petição_inicial",
      "path": "templates/petição_inicial.docx",
      "filename": "petição_inicial.docx",
      "size_bytes": 45678
    }
  ],
  "count": 1
}
```

---

### Get Template Details

```bash
GET /api/v1/templates/{template_id}
```

**Example:**
```bash
curl http://localhost:8002/api/v1/templates/templates/petição_inicial
```

**Response:**
```json
{
  "template": {
    "id": "templates/petição_inicial",
    "name": "petição_inicial",
    "path": "templates/petição_inicial.docx",
    "filename": "petição_inicial.docx",
    "size_bytes": 45678
  },
  "variables": ["nome", "cpf", "endereco", "valor_causa"],
  "variable_count": 4
}
```

---

### Validate Data

```bash
POST /api/v1/validate
```

**Request:**
```json
{
  "template_path": "templates/petição_inicial.docx",
  "data": {
    "nome": "João da Silva",
    "cpf": "12345678901"
  }
}
```

**Response:**
```json
{
  "result": {
    "valid": false,
    "missing": ["endereco", "valor_causa"],
    "extra": [],
    "warnings": [
      "Missing 2 required fields - they will appear as {{ field_name }} in output"
    ]
  },
  "template_variables": ["nome", "cpf", "endereco", "valor_causa"],
  "data_keys": ["cpf", "nome"]
}
```

---

### Preview Document

```bash
POST /api/v1/preview
```

**Request:**
```json
{
  "template_path": "templates/petição_inicial.docx",
  "data": {
    "nome": "João da Silva",
    "cpf": "123.456.789-01",
    "endereco": "Rua das Flores, 123"
  },
  "field_types": {
    "nome": "name",
    "cpf": "cpf",
    "endereco": "address"
  },
  "auto_normalize": true
}
```

**Response:**
```json
{
  "full_text": "PETIÇÃO INICIAL\n\nNome: JOÃO DA SILVA\nCPF: 123.456.789-01\n...",
  "paragraphs": ["PETIÇÃO INICIAL", "Nome: JOÃO DA SILVA", "CPF: 123.456.789-01"],
  "tables": [],
  "paragraph_count": 15,
  "table_count": 0
}
```

---

### Assemble Document

```bash
POST /api/v1/assemble
```

**Request:**
```json
{
  "template_path": "templates/petição_inicial.docx",
  "data": {
    "nome": "João da Silva",
    "cpf": "123.456.789-01",
    "endereco": "Rua das Flores, 123, São Paulo - SP",
    "valor_causa": "R$ 10.000,00"
  },
  "output_filename": "petição_joão_silva.docx",
  "field_types": {
    "nome": "name",
    "cpf": "cpf",
    "endereco": "address"
  },
  "auto_normalize": true
}
```

**Response:**
```json
{
  "success": true,
  "output_path": "/app/outputs/petição_joão_silva.docx",
  "download_url": "/outputs/petição_joão_silva.docx",
  "filename": "petição_joão_silva.docx",
  "message": "Document generated successfully"
}
```

---

## Field Types for Normalization

Use `field_types` to specify normalization for each field:

| Type | Description | Example Input | Normalized Output |
|------|-------------|---------------|-------------------|
| `name` | Person/organization name | `"joão  da  SILVA"` | `"JOÃO DA SILVA"` |
| `address` | Street address | `"rua   das flores,123"` | `"Rua das Flores, 123"` |
| `cpf` | Brazilian CPF | `"12345678901"` | `"123.456.789-01"` |
| `cnpj` | Brazilian CNPJ | `"12345678000195"` | `"12.345.678/0001-95"` |
| `cep` | Brazilian ZIP code | `"01310100"` | `"01310-100"` |
| `oab` | Lawyer registration | `"OAB/SP123456"` | `"OAB/SP 123.456"` |
| `text` | General text | `"hello   world"` | `"hello world"` |
| `raw` | No normalization | `"  keep   as is  "` | `"  keep   as is  "` |

## Template Syntax

Templates use Jinja2 syntax within .docx files:

```
{{ nome }}                          # Simple variable
{{ cpf|cpf }}                       # Apply CPF filter
{{ nome|nome }}                     # Apply name normalization
{{ endereco|endereco }}             # Apply address normalization

{% if condicao %}                   # Conditional
  Content
{% endif %}

{% for item in lista %}             # Loop
  {{ item }}
{% endfor %}
```

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message",
  "error_type": "ValueError",
  "status_code": 400,
  "timestamp": "2025-12-11T10:30:00"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid data)
- `404` - Not Found (template doesn't exist)
- `422` - Validation Error (malformed request)
- `500` - Internal Server Error

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEMPLATES_DIR` | `/app/templates` | Directory containing .docx templates |
| `OUTPUTS_DIR` | `/app/outputs` | Directory for generated documents |

## Docker Configuration

**Port:** 8002
**Memory Limit:** 1GB
**CPU Limit:** 1 core

**Volumes:**
- `/app/templates` - Template files (read-only)
- `/app/data` - Shared data volume

## Development

### Adding New Endpoints

1. Define Pydantic models in `api/models.py`
2. Add endpoint handler in `api/main.py`
3. Update this README with documentation
4. Add tests to `test_api.py`

### Modifying Backend Logic

Edit files in `/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/legal-doc-assembler/src/`:
- `engine.py` - Core rendering logic
- `normalizers.py` - Text normalization functions

The Docker image automatically copies these files during build.

## Interactive API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8002/docs
- **ReDoc:** http://localhost:8002/redoc

## Monitoring

### Health Check

```bash
curl http://localhost:8002/health
```

### Docker Health

```bash
docker ps --filter name=lw-doc-assembler
```

### Logs

```bash
# Docker
docker logs -f lw-doc-assembler

# Docker Compose
docker-compose logs -f doc-assembler
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs doc-assembler

# Rebuild image
docker-compose build --no-cache doc-assembler
docker-compose up doc-assembler
```

### Template not found

Ensure template exists in mounted volume:
```bash
# Check templates directory
docker exec lw-doc-assembler ls -la /app/templates

# Or locally
ls -la /home/user/Claude-Code-Projetos/legal-workbench/ferramentas/legal-doc-assembler/templates/
```

### Import errors

The API adds backend source to Python path automatically. If issues persist:

```bash
# Check sys.path in container
docker exec lw-doc-assembler python -c "import sys; print('\n'.join(sys.path))"
```

## Related Services

Part of Legal Workbench suite:
- **Text Extractor** - Port 8001
- **Doc Assembler** - Port 8002 (this service)
- **STJ API** - Port 8003
- **Trello MCP** - Port 8004
- **Streamlit Hub** - Port 8501

## License

Part of Claude Code Projetos - Legal Workbench

## Support

For issues or questions, check:
1. `/home/user/Claude-Code-Projetos/legal-workbench/CLAUDE.md` - Project rules
2. `/home/user/Claude-Code-Projetos/ARCHITECTURE.md` - System architecture
3. Container logs: `docker-compose logs doc-assembler`

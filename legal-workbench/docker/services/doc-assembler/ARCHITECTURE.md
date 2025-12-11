# Doc Assembler API - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Legal Workbench                          │
│                     (Docker Compose Stack)                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Streamlit   │        │     Redis    │        │   Nginx      │
│     Hub      │        │   (Queue)    │        │  (Static)    │
│  Port 8501   │        │  Port 6379   │        │              │
└──────────────┘        └──────────────┘        └──────────────┘
        │
        │ HTTP Requests
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend Services                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │Text Extractor│  │ Doc Assembler│  │   STJ API    │         │
│  │  Port 8001   │  │  Port 8002   │  │  Port 8003   │         │
│  │              │  │   ← YOU      │  │              │         │
│  │ (Celery +    │  │   ARE HERE   │  │ (DuckDB)     │         │
│  │  Marker ML)  │  │              │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐                                              │
│  │ Trello MCP   │                                              │
│  │  Port 8004   │                                              │
│  │              │                                              │
│  └──────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Doc Assembler - Internal Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Doc Assembler Service                      │
│                         (Port 8002)                             │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
         ┌───────────────────┐     ┌───────────────────┐
         │   API Layer       │     │   File System     │
         │   (FastAPI)       │     │                   │
         │                   │     │  /app/templates/  │
         │  api/main.py      │────▶│  /app/outputs/    │
         │  api/models.py    │     │                   │
         │  api/__init__.py  │     └───────────────────┘
         └───────────────────┘
                    │
                    │ Imports & Uses
                    ▼
         ┌───────────────────┐
         │  Backend Engine   │
         │                   │
         │  engine.py        │───┐
         │  normalizers.py   │   │
         │  batch_engine.py  │   │
         │  batch_utils.py   │   │
         └───────────────────┘   │
                                 │
         Source Location:        │
         ferramentas/            │
         legal-doc-assembler/    │
         src/                    │
                                 │
                    ┌────────────┘
                    │
                    ▼
         ┌───────────────────┐
         │   Dependencies    │
         │                   │
         │  - docxtpl        │───┐
         │  - jinja2         │   │ Document
         │  - python-docx    │   │ Generation
         │  - pydantic       │   │
         │  - fastapi        │   │
         └───────────────────┘   │
                                 │
                    ┌────────────┘
                    │
                    ▼
         ┌───────────────────┐
         │   Output          │
         │                   │
         │  .docx files      │
         │  (MS Word)        │
         └───────────────────┘
```

## Request Flow

### 1. Document Assembly Request

```
Client
  │
  │ POST /api/v1/assemble
  │ {
  │   "template_path": "template.docx",
  │   "data": {...},
  │   "field_types": {...}
  │ }
  ▼
FastAPI Main (api/main.py)
  │
  │ 1. Validate request (Pydantic)
  │ 2. Resolve template path
  │ 3. Generate output path
  ▼
DocumentEngine (engine.py)
  │
  │ 1. Load template
  │ 2. Preprocess data (normalize)
  │ 3. Apply Jinja2 filters
  │ 4. Render document
  │ 5. Save to output path
  ▼
Response
  │
  │ {
  │   "success": true,
  │   "download_url": "/outputs/doc.docx",
  │   "filename": "doc.docx"
  │ }
  ▼
Client
```

### 2. Template Validation Request

```
Client
  │
  │ POST /api/v1/validate
  │ {
  │   "template_path": "template.docx",
  │   "data": {...}
  │ }
  ▼
FastAPI Main
  │
  │ 1. Validate request
  │ 2. Resolve template path
  ▼
DocumentEngine
  │
  │ 1. Extract template variables
  │ 2. Compare with data keys
  │ 3. Identify missing/extra fields
  ▼
Response
  │
  │ {
  │   "result": {
  │     "valid": true/false,
  │     "missing": [...],
  │     "extra": [...]
  │   }
  │ }
  ▼
Client
```

## Data Flow

```
Template (.docx)          Data (JSON)
    │                         │
    │                         │
    └──────────┬──────────────┘
               │
               ▼
        DocumentEngine
               │
               │ 1. Parse template
               │    (extract {{ variables }})
               │
               │ 2. Normalize data
               │    (apply field_types)
               │
               │ 3. Merge data with template
               │    (Jinja2 rendering)
               │
               ▼
        Rendered Document
               │
               ▼
         Output (.docx)
```

## Component Responsibilities

### API Layer (`api/`)

**Responsibilities:**
- HTTP request/response handling
- Request validation (Pydantic models)
- Path resolution and security
- Error handling and status codes
- CORS configuration
- API documentation generation

**Does NOT:**
- Document rendering logic
- Text normalization
- Template parsing

### Backend Engine (`ferramentas/legal-doc-assembler/src/`)

**Responsibilities:**
- Document rendering (docxtpl + Jinja2)
- Text normalization (Brazilian formats)
- Template variable extraction
- Data validation against templates
- Custom Jinja2 filters

**Does NOT:**
- HTTP handling
- Path security checks
- API-specific logic

## Deployment Architecture

### Docker Container Structure

```
Container: lw-doc-assembler
├── /app/
│   ├── api/                          # API layer
│   │   ├── main.py
│   │   ├── models.py
│   │   └── __init__.py
│   │
│   ├── ferramentas/                  # Backend (copied during build)
│   │   └── legal-doc-assembler/
│   │       └── src/
│   │           ├── engine.py
│   │           └── normalizers.py
│   │
│   ├── templates/                    # Mounted volume (read-only)
│   │   └── *.docx
│   │
│   └── outputs/                      # Generated documents
│       └── *.docx
│
├── Python 3.11
├── uvicorn (ASGI server)
└── appuser (non-root)
```

### Volume Mounts

```yaml
volumes:
  # Templates (read-only)
  - ../ferramentas/legal-doc-assembler/templates:/app/templates:ro

  # Shared data volume
  - app-data:/app/data
```

### Environment Variables

```bash
TEMPLATES_DIR=/app/templates   # Template files location
OUTPUT_DIR=/app/output          # Generated documents location
```

## Security Considerations

### Path Traversal Prevention

```python
def resolve_template_path(template_path: str) -> Path:
    # Remove leading slash
    template_path = template_path.lstrip('/')

    # Build absolute path
    abs_path = TEMPLATES_DIR / template_path

    # Validate path is within TEMPLATES_DIR
    try:
        abs_path.resolve().relative_to(TEMPLATES_DIR.resolve())
    except ValueError:
        raise FileNotFoundError("Path outside templates directory")

    return abs_path
```

### Input Validation

All requests validated using Pydantic models:
- Type checking
- Required field enforcement
- Custom validators (e.g., .docx extension)

### Docker Security

- Non-root user (`appuser`)
- Read-only template volume
- Resource limits (1GB RAM, 1 CPU)
- No secrets in environment variables

## Performance Characteristics

### Resource Usage

- **Memory:** ~200MB idle, ~500MB peak (single document)
- **CPU:** Minimal (I/O bound)
- **Disk:** Minimal (documents are small)

### Scaling Strategy

**Current:** Single container, synchronous processing
**Future Options:**
1. Horizontal scaling (multiple containers + load balancer)
2. Async processing (Celery queue, like Text Extractor)
3. Caching (template parsing results)

### Bottlenecks

1. **Template parsing** - First load is slow
2. **Large templates** - >10MB templates take longer
3. **Complex Jinja2** - Nested loops/conditions

## Integration Points

### Upstream (Consumers)

- **Streamlit Hub** - Primary UI
- **Direct API calls** - curl, Python client
- **Future:** Other microservices

### Downstream (Dependencies)

- **File System** - Template/output storage
- **None** - Service is stateless, no database

### Shared Resources

- **app-data volume** - Shared with other services
- **legal-workbench-net** - Docker network

## Error Handling Strategy

### Layers

```
Request
  │
  ▼
Pydantic Validation ──────▶ 422 Unprocessable Entity
  │
  ▼
Custom Validators ─────────▶ 400 Bad Request
  │
  ▼
File Operations ───────────▶ 404 Not Found
  │
  ▼
Template Rendering ────────▶ 400 Bad Request
  │
  ▼
Unexpected Errors ─────────▶ 500 Internal Server Error
  │
  ▼
Response
```

### Error Response Format

```json
{
  "detail": "Human-readable error message",
  "error_type": "ExceptionClassName",
  "status_code": 404,
  "timestamp": "2025-12-11T10:30:00"
}
```

## Monitoring & Observability

### Health Check

```bash
GET /health
```

Returns:
- Service status
- API version
- Engine version
- Timestamp

### Docker Health Check

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Logging

- **uvicorn** - Request/response logs
- **Python logging** - Application logs
- **Rich console** - Colored terminal output (development)

## Development Workflow

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run with auto-reload
uvicorn api.main:app --reload --port 8002

# 3. Access interactive docs
open http://localhost:8002/docs
```

### Testing

```bash
# Unit tests (if implemented)
pytest

# Integration tests
python test_api.py

# Manual testing
./examples/simple_curl_tests.sh
```

### Docker Development

```bash
# Build
docker-compose build doc-assembler

# Run
docker-compose up doc-assembler

# Logs
docker-compose logs -f doc-assembler

# Shell access
docker exec -it lw-doc-assembler bash
```

## Future Enhancements

### Short Term

- [ ] Batch assembly endpoint (multiple documents at once)
- [ ] Template upload/management endpoints
- [ ] Document download endpoint (serve generated files)
- [ ] Webhook notifications (document ready)

### Medium Term

- [ ] Template versioning
- [ ] Document history/audit trail
- [ ] Advanced validation (regex patterns, value ranges)
- [ ] Custom filter registration API

### Long Term

- [ ] Template editor UI
- [ ] Real-time collaboration
- [ ] PDF output support
- [ ] Digital signature integration
- [ ] Analytics (most used templates, error rates)

## Related Documentation

- **API Reference:** `README.md`
- **Quick Start:** `QUICKSTART.md`
- **Backend Engine:** `/home/user/Claude-Code-Projetos/legal-workbench/ferramentas/legal-doc-assembler/README.md`
- **Project Rules:** `/home/user/Claude-Code-Projetos/legal-workbench/CLAUDE.md`
- **System Architecture:** `/home/user/Claude-Code-Projetos/ARCHITECTURE.md`

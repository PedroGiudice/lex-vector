# Backend Proxy Layer

**BFF Pattern - Critical Security Component**

This directory contains the **Backend-for-Frontend (BFF) proxy layer** for communicating with Docker backend services. This is where all API calls are made - the browser NEVER sees tokens or credentials.

## Architecture

```
Browser (HTMX) <-> FastHTML BFF <-> [PROXY LAYER] <-> STJ API (Docker)
                                          ^
                                   Tokens stay HERE
                                   Browser NEVER sees
```

## Files

- `stj_client.py` - Main STJ API client with retry logic
- `__init__.py` - Module exports
- `test_stj_client.py` - Test suite
- `README.md` - This file

## Quick Start

### Basic Usage

```python
from services import STJClient

# Context manager (recommended)
async with STJClient() as client:
    # Search
    results = await client.search(
        termo="responsabilidade civil",
        orgao="TERCEIRA TURMA",
        dias=180
    )

    # Get case details
    case = await client.get_case("abc123")

    # Get statistics
    stats = await client.get_stats()
```

### Convenience Functions

```python
from services import quick_search, quick_health_check

# One-off calls (creates/closes client automatically)
results = await quick_search("dano moral", dias=90)
health = await quick_health_check()
```

### In FastHTML Routes

```python
from fasthtml.common import *
from services import STJClient, STJConnectionError

@rt("/api/search")
async def get(termo: str):
    """HTMX endpoint for search."""
    try:
        async with STJClient() as client:
            results = await client.search(termo=termo)

        # Return results as HTML
        return Div(
            *[Div(r.numero_processo) for r in results.resultados]
        )

    except STJConnectionError as e:
        return Div(
            "Backend unavailable. Please try again.",
            cls="error"
        )
```

## API Methods

### search()
Search STJ jurisprudence with filters.

**Parameters:**
- `termo` (str): Search term (min 3 chars)
- `orgao` (str, optional): Filter by órgão julgador
- `dias` (int): Search last N days (default: 365)
- `limit` (int): Max results (default: 100, max: 1000)
- `offset` (int): Pagination offset (default: 0)
- `campo` (str): "ementa" or "texto_integral" (default: "ementa")

**Returns:** `SearchResponse`

### get_case()
Get full case details by ID.

**Parameters:**
- `case_id` (str): Unique case identifier

**Returns:** `AcordaoDetail`

**Raises:** `STJNotFoundError` if case doesn't exist

### get_stats()
Get database statistics.

**Returns:** `StatsResponse` with counts, sizes, dates

### trigger_sync()
Trigger background data sync (non-blocking).

**Parameters:**
- `orgaos` (List[str], optional): Specific órgãos (None = all)
- `dias` (int): Sync last N days (default: 30)
- `force` (bool): Re-download existing files (default: False)

**Returns:** `SyncStatus` (initial status)

### get_sync_status()
Get current/last sync operation status.

**Returns:** `SyncStatus`

### health_check()
Check API and database health.

**Returns:** `HealthResponse`

## Exception Hierarchy

```
STJClientError (base)
├── STJConnectionError    # Cannot connect to backend
├── STJTimeoutError       # Request timed out
├── STJNotFoundError      # Resource not found (404)
├── STJValidationError    # Invalid request (422)
└── STJServerError        # Backend error (5xx)
```

### Exception Handling

```python
from services import (
    STJClient,
    STJConnectionError,
    STJTimeoutError,
    STJNotFoundError
)

try:
    async with STJClient() as client:
        case = await client.get_case("123")

except STJNotFoundError:
    # Case doesn't exist
    return Div("Case not found", cls="error")

except STJTimeoutError:
    # Backend too slow
    return Div("Request timed out. Try again.", cls="error")

except STJConnectionError:
    # Backend down
    return Div("Backend unavailable", cls="error")
```

## Configuration

Set via environment variables:

- `STJ_API_URL` - Backend URL (default: `http://lw-stj-api:8000`)
- `REQUEST_TIMEOUT` - Timeout in seconds (default: 30)
- `MAX_RETRIES` - Max retry attempts (default: 3)

### Docker Compose

```yaml
fasthtml-bff:
  environment:
    - STJ_API_URL=http://lw-stj-api:8000
    - REQUEST_TIMEOUT=30
    - MAX_RETRIES=3
```

### Local Development

```bash
export STJ_API_URL=http://localhost:8003
export REQUEST_TIMEOUT=60
```

## Testing

Run test suite:

```bash
cd poc-fasthtml-stj
python services/test_stj_client.py
```

Or with pytest:

```bash
pytest services/test_stj_client.py -v
```

**Note:** Tests require Docker containers to be running:

```bash
cd legal-workbench/docker
docker compose ps  # All should be "healthy"
```

## Features

### Automatic Retry
Uses `tenacity` for exponential backoff on connection errors:
- 3 attempts max
- 2s initial wait, up to 10s max
- Only retries on connection/timeout errors

### Timeout Handling
- Default 30s timeout
- Configurable per-client
- Raises `STJTimeoutError` on timeout

### Connection Pooling
- 10 keepalive connections
- 20 max connections
- Automatic cleanup on context exit

### Structured Logging
- All requests logged
- Errors logged with context
- Debug mode available

### Type Hints
- Full type annotations
- IDE autocomplete support
- Runtime validation

## Data Models

All response models mirror the backend API:

- `AcordaoSummary` - Search result item
- `AcordaoDetail` - Full case details
- `SearchResponse` - Paginated search results
- `StatsResponse` - Database statistics
- `SyncStatus` - Sync operation status
- `HealthResponse` - Health check response

Models auto-parse datetime strings from ISO format.

## Best Practices

### 1. Always Use Context Manager

```python
# GOOD
async with STJClient() as client:
    results = await client.search(termo="test")

# BAD - leaks connections
client = STJClient()
results = await client.search(termo="test")
```

### 2. Handle Specific Exceptions

```python
# GOOD - handle each error type
try:
    case = await client.get_case(id)
except STJNotFoundError:
    return Div("Not found")
except STJConnectionError:
    return Div("Backend down")

# BAD - generic catch
try:
    case = await client.get_case(id)
except Exception as e:
    return Div(str(e))
```

### 3. Validate Input Early

```python
# GOOD - check before calling
if len(termo) < 3:
    return Div("Search term too short")

results = await client.search(termo=termo)

# BAD - let backend validate
results = await client.search(termo=termo)  # Fails for short terms
```

### 4. Use Pagination

```python
# GOOD - paginate large results
results = await client.search(termo="test", limit=20, offset=0)

# BAD - fetching too much
results = await client.search(termo="test", limit=1000)
```

## Troubleshooting

### "Connection refused"
Backend not running or wrong URL.

**Fix:**
```bash
cd legal-workbench/docker
docker compose ps  # Check status
docker compose logs lw-stj-api  # Check logs
```

### "Request timed out"
Backend too slow or unresponsive.

**Fix:**
- Increase `REQUEST_TIMEOUT`
- Check backend logs for slow queries
- Optimize database indexes

### "Module not found: tenacity"
Missing dependency.

**Fix:**
```bash
cd poc-fasthtml-stj
source .venv/bin/activate
pip install -r requirements.txt
```

### "Client not initialized"
Forgot to use context manager.

**Fix:**
```python
# Use context manager
async with STJClient() as client:
    # ...
```

## Security Notes

1. **Tokens NEVER in browser** - All credentials stay server-side
2. **No CORS needed** - BFF handles cross-origin
3. **Session-based** - Use FastHTML sessions for user state
4. **Input validation** - Always validate before backend call
5. **Error sanitization** - Don't expose backend errors to users

## Performance Tips

1. **Reuse client** - Use context manager for multiple calls
2. **Adjust limits** - Only fetch what you need
3. **Cache responses** - Use FastHTML caching for read-heavy endpoints
4. **Async all the way** - Keep routes async to avoid blocking
5. **Monitor logs** - Watch for retry patterns

## Future Enhancements

- [ ] Response caching layer
- [ ] Rate limiting
- [ ] Request deduplication
- [ ] Metrics collection
- [ ] Circuit breaker pattern
- [ ] Health check monitoring

---

**Last Updated:** 2025-12-13
**Maintainer:** FastHTML BFF Team
**Pattern:** Backend-for-Frontend (BFF)

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

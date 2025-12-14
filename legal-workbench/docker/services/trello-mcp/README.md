# Trello MCP API

Production-grade FastAPI service for Trello integration with rate limiting, retry logic, and comprehensive error handling.

## Features

- **RESTful API**: OpenAPI-documented endpoints for all Trello operations
- **Rate Limiting**: 100 requests/minute per IP (configurable)
- **Retry Logic**: Exponential backoff with jitter for transient errors
- **Error Handling**: Categorized exceptions (auth, rate limit, network)
- **Docker Support**: Multi-stage build with non-root user
- **Health Checks**: Built-in monitoring endpoints

## Architecture

```
trello-mcp/
├── api/
│   ├── __init__.py
│   ├── main.py      # FastAPI application
│   └── models.py    # API request/response schemas
├── Dockerfile       # Multi-stage production build
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Endpoints

### Health Check
- **GET** `/health` - Service health status
- **GET** `/` - API information

### Boards
- **GET** `/api/v1/boards` - List all accessible boards
- **GET** `/api/v1/boards/{board_id}` - Get complete board structure

### Cards
- **POST** `/api/v1/cards` - Create a new card
- **PUT** `/api/v1/cards/{card_id}/move` - Move card to different list
- **POST** `/api/v1/cards/batch` - Fetch multiple cards (up to 10)
- **POST** `/api/v1/cards/search` - Search/filter cards on a board

### MCP Tools
- **GET** `/api/v1/mcp/tools/list` - List available MCP tools
- **POST** `/api/v1/mcp/tools/call` - Execute MCP tool

## Quick Start

### 1. Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
cp ../../.env.example ../../.env
```

Edit `.env`:
```env
TRELLO_API_KEY=your_trello_api_key
TRELLO_API_TOKEN=your_trello_token
RATE_LIMIT_PER_MINUTE=100
```

### 2. Build and Run with Docker

From `legal-workbench/docker/` directory:

```bash
# Build only trello-mcp
docker-compose build trello-mcp

# Run only trello-mcp
docker-compose up trello-mcp

# Run all services
docker-compose up -d
```

### 3. Access the API

- **API Docs**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc
- **Health Check**: http://localhost:8004/health

## API Usage Examples

### Create a Card

```bash
curl -X POST "http://localhost:8004/api/v1/cards" \
  -H "Content-Type: application/json" \
  -d '{
    "list_id": "5f1234567890abcdef123456",
    "name": "New Task",
    "desc": "Task description",
    "due": "2025-12-31T23:59:59Z"
  }'
```

### List All Boards

```bash
curl "http://localhost:8004/api/v1/boards"
```

### Get Board Structure

```bash
curl "http://localhost:8004/api/v1/boards/5f1234567890abcdef123456"
```

### Search Cards

```bash
curl -X POST "http://localhost:8004/api/v1/cards/search" \
  -H "Content-Type: application/json" \
  -d '{
    "board_id": "5f1234567890abcdef123456",
    "labels": ["Bug", "Priority"],
    "due_date_start": "2025-11-23T00:00:00Z",
    "due_date_end": "2025-12-31T23:59:59Z"
  }'
```

## Rate Limiting

The API implements two layers of rate limiting:

1. **Client-side (slowapi)**: 100 requests/minute per IP
2. **Trello API**: Automatic retry with exponential backoff

Rate limit responses:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Trello API rate limit exceeded",
  "details": {
    "retry_after": "10s",
    "hint": "Trello API allows 100 requests per 10 seconds per token"
  }
}
```

## Error Handling

The API categorizes errors for proper handling:

### Authentication Errors (401)
```json
{
  "error": "authentication_failed",
  "message": "Trello authentication failed",
  "details": {
    "hint": "Check TRELLO_API_KEY and TRELLO_API_TOKEN environment variables"
  }
}
```

### Rate Limit Errors (429)
```json
{
  "error": "rate_limit_exceeded",
  "message": "Trello API rate limit exceeded",
  "details": {
    "retry_after": "10s"
  }
}
```

### API Errors (502)
```json
{
  "error": "trello_api_error",
  "message": "Error description"
}
```

### Validation Errors (422)
```json
{
  "error": "validation_error",
  "message": "Invalid request parameters",
  "details": [...]
}
```

## Development

### Local Development (without Docker)

```bash
# Navigate to trello-mcp directory
cd /home/user/Claude-Code-Projetos/legal-workbench/ferramentas/trello-mcp

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r ../../docker/services/trello-mcp/requirements.txt

# Set environment variables
export TRELLO_API_KEY=your_key
export TRELLO_API_TOKEN=your_token

# Run the API
cd ../../docker/services/trello-mcp
uvicorn api.main:app --reload --host 0.0.0.0 --port 8004
```

### Testing

```bash
# Health check
curl http://localhost:8004/health

# List boards (requires valid credentials)
curl http://localhost:8004/api/v1/boards
```

## Docker Compose Integration

The service integrates with the Legal Workbench ecosystem:

```yaml
services:
  trello-mcp:
    build:
      context: ./services/trello-mcp
      dockerfile: Dockerfile
    container_name: lw-trello-mcp
    ports:
      - "8004:8004"
    environment:
      - TRELLO_API_KEY=${TRELLO_API_KEY}
      - TRELLO_API_TOKEN=${TRELLO_API_TOKEN}
      - RATE_LIMIT_PER_MINUTE=100
    networks:
      - legal-workbench-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

## Security Features

1. **Non-root user**: Runs as `appuser` in container
2. **Credential sanitization**: API keys/tokens removed from error messages
3. **CORS middleware**: Configurable origins (default: all for dev)
4. **Input validation**: Pydantic models with strict validation
5. **Rate limiting**: Prevents abuse and protects Trello API

## Performance Optimization

1. **Multi-stage Docker build**: Smaller image size
2. **Async I/O**: Non-blocking HTTP client (httpx)
3. **Batch API**: Fetch up to 10 cards in single request
4. **Parallel requests**: Uses `asyncio.gather` for concurrent operations
5. **Connection pooling**: Persistent HTTP client per request lifecycle

## Monitoring

### Health Endpoint Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "trello_api_connected": true
}
```

### Logs

All operational logs are sent to stderr for Docker compatibility:

```
[FastAPI] ✓ Environment validated
[TrelloClient] Initialized with rate limit: 90 req/10s
[TrelloClient] ✓ Authenticated as John Doe
[FastAPI] ✓ Application ready
```

## Troubleshooting

### Connection Issues

```bash
# Check if service is running
docker ps | grep trello-mcp

# View logs
docker logs lw-trello-mcp

# Test connectivity
curl http://localhost:8004/health
```

### Authentication Failures

1. Verify API key and token in `.env`
2. Check token has read/write permissions
3. Test credentials directly:
   ```bash
   curl "https://api.trello.com/1/members/me?key=YOUR_KEY&token=YOUR_TOKEN"
   ```

### Rate Limiting Issues

If you hit rate limits frequently:

1. Reduce `RATE_LIMIT_PER_MINUTE` in `.env`
2. Use batch endpoints when possible
3. Implement client-side caching

## API Reference

Full API documentation available at:
- **Swagger UI**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc

## License

See LICENSE file in repository root.

## Support

For issues or questions, refer to:
- Trello API docs: https://developer.atlassian.com/cloud/trello/
- FastAPI docs: https://fastapi.tiangolo.com/
- Project CHANGELOG: `../../ferramentas/trello-mcp/CHANGELOG.md`

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

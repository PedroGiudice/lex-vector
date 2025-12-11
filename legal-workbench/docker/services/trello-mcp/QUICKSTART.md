# Trello MCP API - Quick Start Guide

Get the Trello MCP API running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- Trello API credentials (see below)
- 512MB RAM available

## Step 1: Get Trello API Credentials

1. **Get API Key**:
   - Visit: https://trello.com/power-ups/admin
   - Click "New" → "Create new Power-Up"
   - Copy your API Key

2. **Generate Token**:
   - Click "Token" link (or visit the URL shown)
   - Authorize the application
   - Copy the generated token

## Step 2: Configure Environment

```bash
# Navigate to docker directory
cd /home/user/Claude-Code-Projetos/legal-workbench/docker

# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

Add your credentials:
```env
TRELLO_API_KEY=your_key_here
TRELLO_API_TOKEN=your_token_here
```

## Step 3: Build and Run

### Option A: Using Docker Compose (Recommended)

```bash
# From legal-workbench/docker directory
docker-compose up -d trello-mcp

# View logs
docker-compose logs -f trello-mcp
```

### Option B: Using Makefile

```bash
# From legal-workbench/docker/services/trello-mcp directory
make build  # Build image
make up     # Start service
make logs   # View logs
```

## Step 4: Verify Installation

### Check Health

```bash
curl http://localhost:8004/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "trello_api_connected": true
}
```

### Run Test Suite

```bash
# From legal-workbench/docker/services/trello-mcp directory
./test_api.sh
```

### Open API Documentation

Visit: http://localhost:8004/docs

## Step 5: Test with Real Data

### List Your Boards

```bash
curl http://localhost:8004/api/v1/boards | jq .
```

### Get Board Structure

```bash
# Replace BOARD_ID with an ID from previous response
curl http://localhost:8004/api/v1/boards/BOARD_ID | jq .
```

### Create a Test Card

```bash
# Get a list_id from board structure, then:
curl -X POST http://localhost:8004/api/v1/cards \
  -H "Content-Type: application/json" \
  -d '{
    "list_id": "YOUR_LIST_ID",
    "name": "Test Card from API",
    "desc": "This card was created via the Trello MCP API"
  }' | jq .
```

## Troubleshooting

### Service Won't Start

1. **Check logs**:
   ```bash
   docker logs lw-trello-mcp
   ```

2. **Verify credentials**:
   ```bash
   # Test directly with Trello API
   curl "https://api.trello.com/1/members/me?key=YOUR_KEY&token=YOUR_TOKEN"
   ```

3. **Check port availability**:
   ```bash
   lsof -i :8004
   ```

### Authentication Failed

Error: `authentication_failed`

**Solution**:
- Verify API key and token in `.env`
- Ensure token has read/write permissions
- Regenerate token if necessary

### Rate Limit Errors

Error: `rate_limit_exceeded`

**Solution**:
- Wait 10 seconds and retry
- Reduce request frequency
- Use batch endpoints (`/api/v1/cards/batch`)

### Connection Refused

**Solution**:
```bash
# Restart the service
docker-compose restart trello-mcp

# Or rebuild
docker-compose up -d --build trello-mcp
```

## Next Steps

1. **Explore API**: Visit http://localhost:8004/docs
2. **Read documentation**: See `README.md` for detailed API reference
3. **Integrate**: Use the API in your applications
4. **Monitor**: Check `/health` endpoint regularly

## Common Commands

```bash
# Start service
make up

# Stop service
make stop

# View logs
make logs

# Run tests
make test

# Open API docs
make docs

# Restart service
make restart

# Clean and rebuild
make rebuild
```

## Support

- **Full docs**: See `README.md`
- **API reference**: http://localhost:8004/docs
- **Trello API**: https://developer.atlassian.com/cloud/trello/

## Architecture Overview

```
┌─────────────────┐
│   Client App    │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI (8004) │ ← Rate Limiting (100/min)
│   Trello MCP    │ ← Retry Logic (backoff)
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  Trello API     │
│  api.trello.com │
└─────────────────┘
```

**Features**:
- **Rate Limiting**: 100 requests/minute per IP
- **Retry Logic**: Automatic exponential backoff
- **Error Handling**: Categorized exceptions
- **Monitoring**: Health checks and logs
- **Security**: Non-root container, credential sanitization

## Performance Tips

1. **Use batch endpoints** for fetching multiple cards
2. **Enable caching** in your application layer
3. **Monitor rate limits** via `/health` endpoint
4. **Use filters** in search endpoint to reduce data transfer

---

**Ready in 5 minutes! 🚀**

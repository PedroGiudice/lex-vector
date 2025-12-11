# Text Extractor - Containerization Plan

**Backend:** `/ferramentas/legal-text-extractor/` | **Port:** 8001 + 5555 (Flower)

## File Structure

```
docker/services/text-extractor/
├── Dockerfile           # python:3.11-slim, multi-stage
├── requirements.txt     # marker-pdf (~10GB RAM)
├── api/main.py         # FastAPI + Celery tasks
├── api/models.py       # Pydantic request/response
└── celery_worker.py    # Background processor
```

## Pipeline

**MarkerEngine** → native PDF + auto OCR → **DocumentCleaner** → remove artifacts → **Exporters** → text/markdown/json → **Celery/Redis** async queue

## Dockerfile

- Base: `python:3.11-slim`
- Multi-stage: builder (wheels) → runtime
- Cache: `/app/cache` (volume mount)
- User: appuser (uid 1000, non-root)
- Health: `curl http://localhost:8001/health`

## API Endpoints

| POST | `/api/v1/extract` | Queue extraction job |
| GET | `/api/v1/jobs/{id}` | Get job status/results |
| GET | `/health` | Service health |
| GET | `/docs` | Swagger UI |

## Celery + Redis

- **Broker:** redis://redis:6379/0
- **Concurrency:** MAX_CONCURRENT_JOBS=2 (env var)
- **Timeout:** 600s
- **Monitor:** Flower http://localhost:5555

## RAM Challenge + Solutions

| Issue | RAM | Solution |
|-------|-----|----------|
| Marker model | 8GB | Singleton instance |
| OCR per page | 2GB | Concurrency limit=2 |
| PDF buffer | 1GB | Stream-based |

`low_memory_mode=True` → ignores check, uses OS swap

## Environment Variables

```
GEMINI_API_KEY              # Step 04 (future)
MARKER_CACHE_DIR=/app/cache # Persistent
MAX_CONCURRENT_JOBS=2       # Concurrency
JOB_TIMEOUT_SECONDS=600     # Timeout
CELERY_BROKER_URL           # redis://redis:6379/0
CELERY_RESULT_BACKEND       # redis://redis:6379/0
```

## Implementation Steps

1. `api/main.py` - FastAPI wrapper + health check
2. `celery_worker.py` - Async extraction processor
3. `api/models.py` - ExtractionRequest/Response schemas
4. `requirements.txt` - Dependencies (from `/ferramentas/`)
5. Build & test: `docker-compose up text-extractor`

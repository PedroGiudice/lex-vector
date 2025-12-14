# Text Extractor Service

Microservice for extracting text from PDF documents using Marker and pdfplumber engines.

## Features

- **Dual Engines**: Marker (ML-based with OCR) and pdfplumber (rule-based)
- **Async Processing**: Celery-based job queue with Redis
- **Gemini Enhancement**: Optional AI-powered text post-processing
- **Monitoring**: Celery Flower dashboard
- **API-First**: RESTful API with OpenAPI/Swagger docs

## Architecture

```
FastAPI (8001) ──┐
                 ├──> Redis ──> Celery Worker ──> Marker/pdfplumber
Flower (5555) ───┘                  │
                                    └──> SQLite (jobs.db)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/extract` | Submit extraction job |
| `GET` | `/api/v1/jobs/{id}` | Get job status |
| `GET` | `/api/v1/jobs/{id}/result` | Get extraction result |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

## Usage

### Submit Extraction Job

```bash
curl -X POST http://localhost:8001/api/v1/extract \
  -F "file=@document.pdf" \
  -F "engine=marker" \
  -F "use_gemini=false"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "created_at": "2025-12-11T10:30:00Z",
  "estimated_completion": 300
}
```

### Check Job Status

```bash
curl http://localhost:8001/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "result_url": null,
  "error_message": null,
  "created_at": "2025-12-11T10:30:00Z",
  "started_at": "2025-12-11T10:30:15Z",
  "completed_at": null
}
```

### Get Results

```bash
curl http://localhost:8001/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/result
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Extracted document content...",
  "pages_processed": 25,
  "execution_time_seconds": 287.5,
  "engine_used": "marker",
  "gemini_enhanced": false,
  "metadata": {
    "file_size_bytes": 2048576,
    "ocr_applied": true
  }
}
```

## Engine Comparison

| Feature | Marker | pdfplumber |
|---------|--------|------------|
| Speed | Slower (ML-based) | Faster |
| Accuracy | High (OCR) | Medium |
| Memory | 8-10GB | <1GB |
| Complex PDFs | Excellent | Good |
| Scanned PDFs | Excellent | Poor |

## Development

### Build

```bash
docker build -t text-extractor:latest .
```

### Run Standalone

```bash
docker run -p 8001:8001 -p 5555:5555 \
  -e CELERY_BROKER_URL=redis://localhost:6379/0 \
  -v ./data:/app/data \
  -v ./cache:/app/cache \
  text-extractor:latest
```

### Run with Docker Compose

```bash
cd ../../  # Go to legal-workbench/docker
docker-compose up text-extractor
```

## Monitoring

- **API Docs**: http://localhost:8001/docs
- **Flower Dashboard**: http://localhost:5555 (admin/admin123)

## Configuration

See `.env.example` for all configuration options.

### Key Environment Variables

- `GEMINI_API_KEY`: Google Gemini API key (optional)
- `MAX_CONCURRENT_JOBS`: Maximum parallel extraction jobs (default: 2)
- `JOB_TIMEOUT_SECONDS`: Maximum job execution time (default: 600)

## Memory Optimization

Marker requires ~8-10GB RAM. Strategies used:

1. **Singleton Model**: Load Marker model once per worker
2. **Concurrency Limit**: Max 2 concurrent jobs
3. **Low Memory Mode**: Enable with `{"low_memory_mode": true}` in options
4. **Stream Processing**: Process pages incrementally

## Troubleshooting

### Out of Memory

Reduce `MAX_CONCURRENT_JOBS` to 1 or enable swap:

```yaml
deploy:
  resources:
    limits:
      memory: 10G
```

### Redis Connection Failed

Ensure Redis is running:

```bash
docker-compose up redis
```

### Marker Model Load Timeout

Increase `start_period` in healthcheck:

```yaml
healthcheck:
  start_period: 120s  # 2 minutes
```

## License

Part of Legal Workbench project.

---

## Git

**OBRIGATÓRIO:**

1. **Branch para alterações significativas** — >3 arquivos OU mudança estrutural = criar branch
2. **Pull antes de trabalhar** — `git pull origin main`
3. **Commit ao finalizar** — Nunca deixar trabalho não commitado
4. **Deletar branch após merge** — Local e remota

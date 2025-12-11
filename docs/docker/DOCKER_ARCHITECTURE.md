# Docker Architecture - Legal Workbench

**Version:** 1.0.0
**Last Updated:** 2025-12-11
**Status:** Docker Architecture Design

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Container Specifications](#container-specifications)
4. [Dockerfile Specifications](#dockerfile-specifications)
5. [Docker Compose Structure](#docker-compose-structure)
6. [Build Strategy](#build-strategy)
7. [Networking](#networking)
8. [Volume Management](#volume-management)
9. [Secret Management](#secret-management)
10. [Health Checks](#health-checks)
11. [Scaling Considerations](#scaling-considerations)
12. [Deployment Strategy](#deployment-strategy)

---

## Overview

Legal Workbench is a microservices-based legal automation platform consisting of:
- 1 Frontend Hub (Streamlit)
- 4 Backend Services (legal-text-extractor, legal-doc-assembler, stj-dados-abertos, trello-mcp)
- 1 Shared Library Layer

The architecture is designed for:
- **Isolation**: Each service runs in its own container
- **Scalability**: Services can be scaled independently
- **Resource Optimization**: Heavy services (text-extractor) separated from light services
- **Development Efficiency**: Hot-reload enabled for rapid iteration
- **Reliability**: Multi-stage builds, health checks, proper error handling

---

## WSL2 Configuration (Recommended)

Arquivo: `%UserProfile%\.wslconfig`

```ini
[wsl2]
memory=14GB
processors=3
swap=8GB

[experimental]
autoMemoryReclaim=gradual
networkingMode=mirrored
dnsTunneling=true
firewall=true
sparseVhd=true
```

**Por que esses valores:**
- **memory=14GB**: De 16GB total, deixa 2GB pro Windows
- **processors=3**: Suficiente pra builds e runtime
- **swap=8GB**: Cobre picos do Marker quando carrega modelos
- **autoMemoryReclaim=gradual**: Libera memória não usada automaticamente
- **networkingMode=mirrored**: Simplifica acesso aos containers
- **sparseVhd=true**: Reduz uso de disco do WSL

Após editar, reinicie o WSL: `wsl --shutdown`

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         HOST MACHINE                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Docker Network: lw-network              │  │
│  │                         (bridge)                           │  │
│  │                                                            │  │
│  │  ┌──────────────────────────────────────────────────┐     │  │
│  │  │  lw-hub (Streamlit Frontend)                     │     │  │
│  │  │  - Port: 8501:8501                               │     │  │
│  │  │  - Base: python:3.11-slim                        │     │  │
│  │  │  - Memory: 512MB                                 │     │  │
│  │  │  - CPU: 0.5                                      │     │  │
│  │  └─────────────┬────────────────────────────────────┘     │  │
│  │                │                                           │  │
│  │                │ HTTP/Internal                             │  │
│  │                ├─────────────────────┬─────────────────┐   │  │
│  │                │                     │                 │   │  │
│  │  ┌─────────────▼─────────┐  ┌────────▼──────────┐  ┌──▼───▼──┐
│  │  │ lw-text-extractor     │  │ lw-doc-assembler  │  │ lw-stj  │
│  │  │ - Port: 8001:8001     │  │ - Port: 8002:8002 │  │ 8003    │
│  │  │ - Base: python:3.11   │  │ - Base: 3.11-slim │  │         │
│  │  │ - Memory: 12GB        │  │ - Memory: 1GB     │  │ 1GB     │
│  │  │ - CPU: 4.0            │  │ - CPU: 1.0        │  │ 1.0     │
│  │  │ - GPU: Optional       │  │                   │  │         │
│  │  │ - Marker-PDF (OCR)    │  │ - DOCX Generation │  │ DuckDB  │
│  │  │ - Gemini CLI          │  │ - Jinja2 Templates│  │ Query   │
│  │  └───────────────────────┘  └───────────────────┘  └─────────┘
│  │                │                                           │  │
│  │                │                     ┌─────────────────┐   │  │
│  │                └─────────────────────┤ lw-trello-mcp   │   │  │
│  │                                      │ - Port: 8004    │   │  │
│  │                                      │ - Base: 3.11-sl │   │  │
│  │                                      │ - Memory: 512MB │   │  │
│  │                                      │ - MCP Server    │   │  │
│  │                                      └─────────────────┘   │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  Volumes:                                                         │
│  ├─ lw-data        → /data (juridico-data persistence)           │
│  ├─ lw-cache       → /root/.cache (marker models, pip cache)     │
│  ├─ lw-duckdb      → /db (DuckDB databases)                      │
│  ├─ lw-shared      → /app/shared (shared library code)           │
│  └─ lw-templates   → /templates (DOCX templates)                 │
│                                                                   │
│  Secrets:                                                         │
│  ├─ google_api_key     (Gemini API)                              │
│  ├─ trello_api_key     (Trello Integration)                      │
│  └─ trello_api_token   (Trello Authentication)                   │
└───────────────────────────────────────────────────────────────────┘

External Dependencies:
- Gemini API (via GOOGLE_API_KEY)
- Trello API (via credentials)
- STJ Dados Abertos API (public)
```

---

## Container Specifications

| Container | Base Image | Ports | Memory | CPU | Volume Mounts | Restart Policy |
|-----------|------------|-------|--------|-----|---------------|----------------|
| **lw-hub** | `python:3.11-slim` | `8501:8501` | 512MB | 0.5 | `lw-data`, `lw-shared` | `unless-stopped` |
| **lw-text-extractor** | `python:3.11` | `8001:8001` | 10GB | 4.0 | `lw-data`, `lw-cache`, `lw-shared` | `unless-stopped` |
| **lw-doc-assembler** | `python:3.11-slim` | `8002:8002` | 1GB | 1.0 | `lw-data`, `lw-templates`, `lw-shared` | `unless-stopped` |
| **lw-stj** | `python:3.11-slim` | `8003:8003` | 1GB | 1.0 | `lw-duckdb`, `lw-shared` | `unless-stopped` |
| **lw-trello-mcp** | `python:3.11-slim` | `8004:8004` | 512MB | 0.5 | `lw-shared` | `unless-stopped` |

### Resource Justification

- **lw-text-extractor (10GB)**: Marker-PDF requires ~8-9GB RAM for OCR processing + buffer for Gemini operations
- **lw-hub (512MB)**: Lightweight Streamlit router, minimal state management
- **lw-doc-assembler (1GB)**: DOCX generation can spike during template rendering
- **lw-stj (1GB)**: DuckDB in-memory operations for query optimization
- **lw-trello-mcp (512MB)**: Stateless MCP server, minimal overhead

**Total System RAM**: ~13GB allocated, fits comfortably in 16GB with 3GB headroom for OS and other processes

---

## Dockerfile Specifications

### 1. lw-hub (Streamlit Frontend)

**Path:** `/legal-workbench/Dockerfile.hub`

**Specification:**
```
Multi-stage Build: Yes (2 stages)

Stage 1: builder
- Base: python:3.11-slim
- Install build dependencies: gcc, python3-dev
- Copy requirements.txt
- Install Python dependencies with pip wheel
- Create optimized wheel cache

Stage 2: runtime
- Base: python:3.11-slim
- Copy wheels from builder
- Install runtime dependencies only
- Copy application code (app.py, modules/, config.yaml)
- Create non-root user 'lw-user' (UID 1000)
- Set working directory: /app
- Expose port: 8501
- Health check: curl localhost:8501/_stcore/health
- Entrypoint: streamlit run app.py --server.port=8501 --server.address=0.0.0.0

Environment Variables:
- DATA_PATH_ENV=/data
- PYTHONUNBUFFERED=1
- STREAMLIT_SERVER_HEADLESS=true
- STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

Layer Optimization:
1. System packages (rarely change)
2. Python dependencies (change occasionally)
3. Shared library (change occasionally)
4. Application code (change frequently)
```

### 2. lw-text-extractor (Heavy OCR Backend)

**Path:** `/legal-workbench/ferramentas/legal-text-extractor/Dockerfile`

**Specification:**
```
Multi-stage Build: Yes (3 stages)

Stage 1: marker-builder
- Base: python:3.11 (full, not slim - needs compilation tools)
- Install system dependencies: build-essential, git, poppler-utils, tesseract-ocr
- Install marker-pdf with all dependencies
- Download marker models to /root/.cache/marker
- Create optimized model cache

Stage 2: deps-builder
- Base: python:3.11
- Copy requirements.txt
- Install all Python dependencies with pip wheel
- Separate marker dependencies from app dependencies

Stage 3: runtime
- Base: python:3.11 (needs full version for marker runtime)
- Install runtime system packages: poppler-utils, tesseract-ocr-por
- Copy marker models from marker-builder to /app/.cache/marker
- Copy Python wheels from deps-builder
- Copy application code (main.py, src/)
- Install Gemini CLI binary (if not using API)
- Create non-root user 'extractor' (UID 1001)
- Set working directory: /app
- Expose port: 8001
- Health check: curl localhost:8001/health
- Entrypoint: python main.py --server --port=8001

Environment Variables:
- MARKER_CACHE_DIR=/app/.cache/marker
- DATA_PATH_ENV=/data
- GOOGLE_API_KEY=${GOOGLE_API_KEY}
- PYTHONUNBUFFERED=1
- MALLOC_TRIM_THRESHOLD_=65536  # Memory optimization

GPU Support (Optional):
- Base: nvidia/cuda:12.1.0-runtime-ubuntu22.04 + python3.11
- Runtime: nvidia
- Device requests: gpu=all

Layer Optimization:
1. System packages (20-30 layers)
2. Marker models (1 large layer, cached)
3. Python dependencies (10-15 layers)
4. Application code (5-10 layers)
```

### 3. lw-doc-assembler (DOCX Generator)

**Path:** `/legal-workbench/ferramentas/legal-doc-assembler/Dockerfile`

**Specification:**
```
Multi-stage Build: Yes (2 stages)

Stage 1: builder
- Base: python:3.11-slim
- Install build dependencies
- Copy pyproject.toml
- Install dependencies with pip wheel

Stage 2: runtime
- Base: python:3.11-slim
- Copy wheels from builder
- Copy application code (src/)
- Copy templates from /Word-Templates to /templates
- Create non-root user 'assembler' (UID 1002)
- Set working directory: /app
- Expose port: 8002
- Health check: curl localhost:8002/health
- Entrypoint: python -m src.main --server --port=8002

Environment Variables:
- DATA_PATH_ENV=/data
- TEMPLATE_PATH=/templates
- PYTHONUNBUFFERED=1

Layer Optimization:
1. System packages
2. Python dependencies
3. Templates (rarely change)
4. Application code
```

### 4. lw-stj (STJ Dados Abertos Client)

**Path:** `/legal-workbench/ferramentas/stj-dados-abertos/Dockerfile`

**Specification:**
```
Multi-stage Build: Yes (2 stages)

Stage 1: builder
- Base: python:3.11-slim
- Install build dependencies
- Copy requirements.txt
- Install dependencies with pip wheel

Stage 2: runtime
- Base: python:3.11-slim
- Copy wheels from builder
- Copy application code
- Create non-root user 'stj-user' (UID 1003)
- Set working directory: /app
- Expose port: 8003
- Health check: curl localhost:8003/health
- Entrypoint: python main.py --server --port=8003

Environment Variables:
- DUCKDB_PATH=/db/stj.duckdb
- DATA_PATH_ENV=/data
- PYTHONUNBUFFERED=1

Layer Optimization:
1. System packages
2. Python dependencies (DuckDB, httpx)
3. Application code
```

### 5. lw-trello-mcp (Trello MCP Server)

**Path:** `/legal-workbench/ferramentas/trello-mcp/Dockerfile`

**Specification:**
```
Multi-stage Build: Yes (2 stages)

Stage 1: builder
- Base: python:3.11-slim
- Install build dependencies
- Copy pyproject.toml
- Install dependencies with pip wheel

Stage 2: runtime
- Base: python:3.11-slim
- Copy wheels from builder
- Copy application code (src/)
- Create non-root user 'trello' (UID 1004)
- Set working directory: /app
- Expose port: 8004
- Health check: curl localhost:8004/health
- Entrypoint: python -m src.server --port=8004

Environment Variables:
- TRELLO_API_KEY=${TRELLO_API_KEY}
- TRELLO_API_TOKEN=${TRELLO_API_TOKEN}
- PYTHONUNBUFFERED=1

Layer Optimization:
1. System packages
2. Python dependencies (mcp, httpx)
3. Application code
```

---

## Docker Compose Structure

**Path:** `/legal-workbench/docker-compose.yml`

```yaml
version: '3.9'

networks:
  lw-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16

volumes:
  lw-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_PATH_HOST:-~/juridico-data}

  lw-cache:
    driver: local
    # Persist marker models between restarts

  lw-duckdb:
    driver: local
    # Persist STJ database

  lw-shared:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${REPO_PATH}/shared

  lw-templates:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${REPO_PATH}/Word-Templates

secrets:
  google_api_key:
    file: ./secrets/google_api_key.txt

  trello_api_key:
    file: ./secrets/trello_api_key.txt

  trello_api_token:
    file: ./secrets/trello_api_token.txt

services:

  # ===== FRONTEND =====

  hub:
    build:
      context: .
      dockerfile: Dockerfile.hub
      cache_from:
        - lw-hub:latest
      args:
        BUILDKIT_INLINE_CACHE: 1

    image: lw-hub:latest
    container_name: lw-hub

    ports:
      - "8501:8501"

    networks:
      lw-network:
        ipv4_address: 172.28.0.10

    volumes:
      - lw-data:/data:rw
      - lw-shared:/app/shared:ro
      - ./config.yaml:/app/config.yaml:ro

    environment:
      - DATA_PATH_ENV=/data
      - PYTHONUNBUFFERED=1
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
      - TEXT_EXTRACTOR_URL=http://lw-text-extractor:8001
      - DOC_ASSEMBLER_URL=http://lw-doc-assembler:8002
      - STJ_URL=http://lw-stj:8003
      - TRELLO_MCP_URL=http://lw-trello-mcp:8004

    depends_on:
      text-extractor:
        condition: service_healthy
      doc-assembler:
        condition: service_healthy
      stj:
        condition: service_healthy
      trello-mcp:
        condition: service_healthy

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ===== BACKEND SERVICES =====

  text-extractor:
    build:
      context: ./ferramentas/legal-text-extractor
      dockerfile: Dockerfile
      cache_from:
        - lw-text-extractor:latest
      args:
        BUILDKIT_INLINE_CACHE: 1
        ENABLE_GPU: ${ENABLE_GPU:-false}

    image: lw-text-extractor:latest
    container_name: lw-text-extractor

    ports:
      - "8001:8001"

    networks:
      lw-network:
        ipv4_address: 172.28.0.11

    volumes:
      - lw-data:/data:rw
      - lw-cache:/app/.cache:rw
      - lw-shared:/app/shared:ro

    secrets:
      - google_api_key

    environment:
      - DATA_PATH_ENV=/data
      - MARKER_CACHE_DIR=/app/.cache/marker
      - GOOGLE_API_KEY_FILE=/run/secrets/google_api_key
      - PYTHONUNBUFFERED=1
      - MALLOC_TRIM_THRESHOLD_=65536

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 15s
      retries: 5
      start_period: 120s  # Marker model loading

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 10G
        reservations:
          cpus: '2.0'
          memory: 7G

    # Optional GPU support
    # runtime: nvidia
    # environment:
    #   - NVIDIA_VISIBLE_DEVICES=all

    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"

  doc-assembler:
    build:
      context: ./ferramentas/legal-doc-assembler
      dockerfile: Dockerfile
      cache_from:
        - lw-doc-assembler:latest
      args:
        BUILDKIT_INLINE_CACHE: 1

    image: lw-doc-assembler:latest
    container_name: lw-doc-assembler

    ports:
      - "8002:8002"

    networks:
      lw-network:
        ipv4_address: 172.28.0.12

    volumes:
      - lw-data:/data:rw
      - lw-templates:/templates:ro
      - lw-shared:/app/shared:ro

    environment:
      - DATA_PATH_ENV=/data
      - TEMPLATE_PATH=/templates
      - PYTHONUNBUFFERED=1

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  stj:
    build:
      context: ./ferramentas/stj-dados-abertos
      dockerfile: Dockerfile
      cache_from:
        - lw-stj:latest
      args:
        BUILDKIT_INLINE_CACHE: 1

    image: lw-stj:latest
    container_name: lw-stj

    ports:
      - "8003:8003"

    networks:
      lw-network:
        ipv4_address: 172.28.0.13

    volumes:
      - lw-duckdb:/db:rw
      - lw-shared:/app/shared:ro

    environment:
      - DUCKDB_PATH=/db/stj.duckdb
      - DATA_PATH_ENV=/data
      - PYTHONUNBUFFERED=1

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  trello-mcp:
    build:
      context: ./ferramentas/trello-mcp
      dockerfile: Dockerfile
      cache_from:
        - lw-trello-mcp:latest
      args:
        BUILDKIT_INLINE_CACHE: 1

    image: lw-trello-mcp:latest
    container_name: lw-trello-mcp

    ports:
      - "8004:8004"

    networks:
      lw-network:
        ipv4_address: 172.28.0.14

    volumes:
      - lw-shared:/app/shared:ro

    secrets:
      - trello_api_key
      - trello_api_token

    environment:
      - TRELLO_API_KEY_FILE=/run/secrets/trello_api_key
      - TRELLO_API_TOKEN_FILE=/run/secrets/trello_api_token
      - PYTHONUNBUFFERED=1

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Build Strategy

### Multi-Stage Build Benefits

1. **Reduced Image Size**: Builder stages discarded, only runtime artifacts kept
2. **Layer Caching**: Dependencies cached separately from application code
3. **Security**: Build tools not present in final image
4. **Reproducibility**: Explicit dependency resolution

### Build Optimization Techniques

#### 1. Layer Ordering (Least to Most Frequently Changed)

```dockerfile
# Layer 1: Base system packages (change: monthly)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Python dependencies (change: weekly)
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Layer 3: Shared library (change: daily)
COPY shared/ /app/shared/

# Layer 4: Application code (change: hourly during dev)
COPY src/ /app/src/
COPY main.py /app/
```

#### 2. BuildKit Cache Mounts

```dockerfile
# Cache pip downloads across builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Cache apt packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y marker-dependencies
```

#### 3. Parallel Dependency Installation

```dockerfile
# Install heavy dependencies in parallel
RUN pip install --no-cache-dir \
    marker-pdf \
    torch \
    transformers \
    --find-links https://download.pytorch.org/whl/torch_stable.html
```

#### 4. Pre-downloaded Model Caching (Text Extractor)

```dockerfile
# Download marker models during build
RUN python -c "from marker.models import setup; setup()" && \
    ls -lh /root/.cache/marker
```

### Build Commands

```bash
# Development builds (with cache)
docker-compose build

# Production builds (no cache, explicit platform)
docker-compose build --no-cache --platform linux/amd64

# Single service rebuild
docker-compose build text-extractor

# BuildKit enabled (recommended)
DOCKER_BUILDKIT=1 docker-compose build

# Multi-platform builds (for ARM Macs)
docker buildx build --platform linux/amd64,linux/arm64 -t lw-hub:latest .
```

### Image Size Targets

| Image | Target Size | Actual (Estimated) | Notes |
|-------|-------------|---------------------|-------|
| lw-hub | < 500MB | ~400MB | Streamlit + minimal deps |
| lw-text-extractor | < 8GB | ~6.5GB | Marker models dominate |
| lw-doc-assembler | < 300MB | ~250MB | Python-docx + Jinja2 |
| lw-stj | < 300MB | ~280MB | DuckDB binary included |
| lw-trello-mcp | < 200MB | ~180MB | Minimal MCP server |

---

## Networking

### Network Configuration

- **Type**: Bridge network with custom subnet
- **Subnet**: `172.28.0.0/16`
- **DNS**: Automatic service discovery via container names

### Static IP Assignments

| Service | IP Address | Purpose |
|---------|------------|---------|
| lw-hub | 172.28.0.10 | Frontend, always accessible |
| lw-text-extractor | 172.28.0.11 | Backend service |
| lw-doc-assembler | 172.28.0.12 | Backend service |
| lw-stj | 172.28.0.13 | Backend service |
| lw-trello-mcp | 172.28.0.14 | Backend service |

### Service-to-Service Communication

```python
# In lw-hub (app.py), modules call backends via internal URLs:
TEXT_EXTRACTOR_URL = os.getenv("TEXT_EXTRACTOR_URL", "http://lw-text-extractor:8001")
DOC_ASSEMBLER_URL = os.getenv("DOC_ASSEMBLER_URL", "http://lw-doc-assembler:8002")
STJ_URL = os.getenv("STJ_URL", "http://lw-stj:8003")
TRELLO_MCP_URL = os.getenv("TRELLO_MCP_URL", "http://lw-trello-mcp:8004")
```

### Port Mapping Strategy

- **8501**: Public (Streamlit UI)
- **8001-8004**: Internal only (backend APIs)
- Optional: Expose backend ports for debugging with `--profile debug`

---

## Volume Management

### Volume Types

#### 1. lw-data (Bind Mount)
```yaml
type: bind
source: ~/juridico-data
purpose: Persistent user data (PDFs, generated docs)
permissions: rw (all containers)
backup: Daily via host-level backup
```

#### 2. lw-cache (Named Volume)
```yaml
type: named
purpose: Marker models, pip cache
size: ~8GB
permissions: rw (text-extractor only)
backup: Optional (can regenerate)
```

#### 3. lw-duckdb (Named Volume)
```yaml
type: named
purpose: STJ database persistence
size: ~2GB
permissions: rw (stj container only)
backup: Weekly via volume backup
```

#### 4. lw-shared (Bind Mount)
```yaml
type: bind
source: ./shared
purpose: Shared Python library
permissions: ro (all containers)
backup: Git-managed
```

#### 5. lw-templates (Bind Mount)
```yaml
type: bind
source: ./Word-Templates
purpose: DOCX templates
permissions: ro (doc-assembler only)
backup: Git-managed
```

### Volume Backup Strategy

```bash
# Backup named volumes
docker run --rm -v lw-cache:/source -v ~/backups:/backup \
  alpine tar czf /backup/lw-cache-$(date +%Y%m%d).tar.gz -C /source .

# Restore named volume
docker run --rm -v lw-cache:/target -v ~/backups:/backup \
  alpine tar xzf /backup/lw-cache-20251211.tar.gz -C /target

# Bind mounts backed up via host filesystem
rsync -av ~/juridico-data ~/backups/juridico-data-$(date +%Y%m%d)
```

---

## Secret Management

### Docker Secrets (Production)

```bash
# Create secret files
mkdir -p ./secrets
echo "YOUR_GOOGLE_API_KEY" > ./secrets/google_api_key.txt
echo "YOUR_TRELLO_KEY" > ./secrets/trello_api_key.txt
echo "YOUR_TRELLO_TOKEN" > ./secrets/trello_api_token.txt

# Secure permissions
chmod 600 ./secrets/*
```

### Environment Variables (Development)

```bash
# .env file (not committed to Git)
GOOGLE_API_KEY=your_key_here
TRELLO_API_KEY=your_key_here
TRELLO_API_TOKEN=your_token_here
DATA_PATH_HOST=/home/user/juridico-data
REPO_PATH=/home/user/Claude-Code-Projetos
ENABLE_GPU=false
```

### Secret Rotation

```bash
# Update secret without downtime
echo "NEW_API_KEY" > ./secrets/google_api_key.txt
docker-compose up -d --no-deps text-extractor
```

### Secret Access in Containers

```python
# In Python code:
import os

def load_secret(secret_name: str) -> str:
    """Load secret from Docker secret file or environment variable."""
    secret_file = f"/run/secrets/{secret_name}"
    if os.path.exists(secret_file):
        with open(secret_file) as f:
            return f.read().strip()
    return os.getenv(secret_name.upper(), "")

# Usage:
GOOGLE_API_KEY = load_secret("google_api_key")
```

---

## Health Checks

### Health Check Endpoints

Each backend service exposes a `/health` endpoint:

```python
# Example health check implementation (FastAPI)
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "text-extractor",
        "timestamp": datetime.now().isoformat(),
        "marker_loaded": check_marker_models(),
        "gemini_api": check_gemini_connection()
    }
```

### Dependency-Based Startup

```yaml
# Hub waits for all backends to be healthy
depends_on:
  text-extractor:
    condition: service_healthy
  doc-assembler:
    condition: service_healthy
```

### Monitoring via Health Checks

```bash
# Health check all services
docker-compose ps

# Detailed health status
docker inspect --format='{{.State.Health.Status}}' lw-text-extractor

# Health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' lw-hub

# View logs
docker-compose logs -f --tail=100 lw-text-extractor
```

---

## Scaling Considerations

### Horizontal Scaling

```yaml
# Scale light services for load balancing
docker-compose up -d --scale doc-assembler=3 --scale stj=2

# Requires nginx/traefik reverse proxy for load balancing
```

### Resource Limits vs Requests

```yaml
deploy:
  resources:
    limits:      # Hard cap (container killed if exceeded)
      cpus: '4.0'
      memory: 10G
    reservations:  # Guaranteed resources
      cpus: '2.0'
      memory: 6G
```

### Auto-Scaling with Docker Swarm

```yaml
# Deploy to Swarm with auto-scaling
deploy:
  replicas: 2
  update_config:
    parallelism: 1
    delay: 10s
  rollback_config:
    parallelism: 1
    delay: 5s
  restart_policy:
    condition: on-failure
    max_attempts: 3
```

### Kubernetes Migration Path

```yaml
# Ready for K8s translation:
# - Services → Deployments
# - Networks → Services + Ingress
# - Volumes → PersistentVolumeClaims
# - Secrets → Kubernetes Secrets
# - Health checks → Liveness/Readiness probes
```

---

## Deployment Strategy

### Development Workflow

```bash
# 1. Start all services
docker-compose up -d

# 2. Watch logs
docker-compose logs -f hub

# 3. Hot reload (mount code as volume)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 4. Rebuild after dependency changes
docker-compose build text-extractor
docker-compose up -d --no-deps text-extractor
```

### Production Deployment

```bash
# 1. Build optimized images
DOCKER_BUILDKIT=1 docker-compose -f docker-compose.prod.yml build --no-cache

# 2. Tag for registry
docker tag lw-hub:latest registry.example.com/lw-hub:v1.0.0

# 3. Push to registry
docker-compose push

# 4. Deploy to production server
ssh production "docker-compose pull && docker-compose up -d"

# 5. Health check
curl http://production-server:8501/_stcore/health
```

### Rolling Updates

```bash
# Zero-downtime update
docker-compose pull
docker-compose up -d --no-deps --build hub
docker-compose up -d --no-deps --build text-extractor
# etc...
```

### Rollback Strategy

```bash
# Rollback to previous image
docker tag lw-hub:latest lw-hub:backup
docker tag lw-hub:v1.0.0 lw-hub:latest
docker-compose up -d --no-deps hub
```

### Logging

```bash
# View logs from all services
docker-compose logs -f

# View specific service logs
docker-compose logs -f lw-text-extractor

# Export logs for analysis
docker-compose logs --no-color > logs-$(date +%Y%m%d).txt
```

### CI/CD Integration

```yaml
# .github/workflows/docker-build.yml
name: Build and Push Docker Images

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build images
        run: |
          cd legal-workbench
          DOCKER_BUILDKIT=1 docker-compose build

      - name: Run health checks
        run: |
          docker-compose up -d
          sleep 60
          docker-compose ps
          curl -f http://localhost:8501/_stcore/health

      - name: Push to registry
        if: success()
        run: docker-compose push
```

---

## Deployment Checklist

- [ ] Multi-stage Dockerfiles implemented for all services
- [ ] Health checks configured with appropriate timeouts
- [ ] Resource limits set based on service requirements
- [ ] Secrets managed via Docker secrets (not environment variables)
- [ ] Persistent volumes configured for data/cache/db
- [ ] Logging configured with rotation
- [ ] Network isolation with static IPs
- [ ] Service dependencies configured (depends_on)
- [ ] Restart policies set to `unless-stopped`
- [ ] Images tagged with version numbers
- [ ] Backup strategy documented
- [ ] Documentation updated with deployment procedures

---

**Next Steps:**
1. Implement Dockerfiles based on specifications above
2. Create `docker-compose.dev.yml` for hot-reload development
3. Test resource limits on target hardware (14GB RAM (WSL), i5 12th gen)
4. Set up automated backups
5. Document disaster recovery procedures

---

**References:**
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [BuildKit Cache](https://docs.docker.com/build/cache/)
- [Health Checks](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Compose Specification](https://docs.docker.com/compose/compose-file/)

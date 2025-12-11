# STJ Dados Abertos API - Dockerfile
# Multi-stage build for optimized image size
#
# Build from legal-workbench root:
#   docker build -f docker/services/stj-api/Dockerfile -t stj-api .
#
# Or use docker-compose:
#   cd docker/services/stj-api && docker-compose up --build

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY docker/services/stj-api/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

LABEL maintainer="PGR <pedro@example.com>"
LABEL description="FastAPI REST API for STJ Dados Abertos jurisprudence database"

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash apiuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/apiuser/.local

# Copy API application code
COPY docker/services/stj-api/api/ /app/api/

# Copy backend modules (needed for imports)
COPY ferramentas/stj-dados-abertos/src /app/backend/src
COPY ferramentas/stj-dados-abertos/config.py /app/backend/

# Create data directories with proper permissions
RUN mkdir -p /app/data/database /app/data/logs /app/data/staging /app/data/metadata \
    && chown -R apiuser:apiuser /app/data

# Set environment variables
ENV PATH=/home/apiuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app:/app/backend

# Switch to non-root user
USER apiuser

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()"

# Run FastAPI with uvicorn
# Using single worker for development, increase for production
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

# FastHTML STJ PoC - BFF Layer
# Multi-stage build for optimized image
# Context: legal-workbench/ (parent of docker/)

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY docker/services/fasthtml-stj/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy FastHTML PoC application
COPY poc-fasthtml-stj/ /app/

# Copy real backend engines from ferramentas
COPY ferramentas/stj-dados-abertos/src/ /app/backend/src/
COPY ferramentas/stj-dados-abertos/config.py /app/backend/

# Set Python path to include backend
ENV PYTHONPATH=/app:/app/backend

# Create data directory
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001", "--log-level", "info"]

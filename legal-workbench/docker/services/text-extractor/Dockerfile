# =====================================
# Stage 1: Builder
# =====================================
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
WORKDIR /build
COPY docker/services/text-extractor/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =====================================
# Stage 2: Runtime
# =====================================
FROM python:3.11-slim

# Install runtime dependencies (libgl1 needed for OpenCV/Marker)
RUN apt-get update && apt-get install -y \
    curl \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -s /bin/bash -m appuser

# Create application directories (including fonts dir for Marker)
RUN mkdir -p /app/data /app/cache /app/cache/fonts /app/api && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser docker/services/text-extractor/api/ /app/api/
COPY --chown=appuser:appuser docker/services/text-extractor/celery_worker.py /app/

# Copy shared logging/middleware module
COPY --chown=appuser:appuser shared/ /app/shared/

# Copy entrypoint script
COPY --chown=appuser:appuser docker/services/text-extractor/entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8001 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:8001/health || exit 1

# Set Python path
ENV PYTHONPATH=/app

# Configure Marker to use writable directories for fonts and output
ENV FONT_DIR=/app/cache/fonts
ENV FONT_PATH=/app/cache/fonts/GoNotoCurrent-Regular.ttf
ENV OUTPUT_DIR=/app/cache/output
ENV DEBUG_DATA_FOLDER=/app/cache/debug

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

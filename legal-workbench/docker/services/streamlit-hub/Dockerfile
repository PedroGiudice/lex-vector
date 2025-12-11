# Multi-stage build for Streamlit Hub
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user FIRST (before copying dependencies)
RUN useradd -m -u 1000 streamlit

# Copy Python dependencies from builder to streamlit user's home
COPY --from=builder /root/.local /home/streamlit/.local

# Fix ownership of dependencies
RUN chown -R streamlit:streamlit /home/streamlit/.local

# Make sure scripts in .local are usable
ENV PATH=/home/streamlit/.local/bin:$PATH

# Create app and data directories with proper ownership
RUN mkdir -p /app/data && chown -R streamlit:streamlit /app

# Copy application files
COPY --chown=streamlit:streamlit app.py .
COPY --chown=streamlit:streamlit lib/ lib/

# Switch to non-root user
USER streamlit

# Expose Streamlit port
EXPOSE 8501

# Healthcheck - uses 127.0.0.1 to bypass any proxy
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://127.0.0.1:8501/_stcore/health', timeout=5); exit(0 if r.status_code == 200 else 1)"

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

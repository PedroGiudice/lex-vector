FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck and create non-root user
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

COPY docker/services/ccui-ws/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/services/ccui-ws/main.py .
COPY shared/ /app/shared/

# Set ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8005/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]

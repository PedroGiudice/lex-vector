#!/bin/bash
# legal-workbench/scripts/dev-build.sh
# Rebuild and restart a specific service
set -e

cd "$(dirname "$0")/.."

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "Usage: ./scripts/dev-build.sh <service-name>"
    echo ""
    echo "Available services:"
    echo "  frontend-react     - React SPA (Vite)"
    echo "  api-stj            - Jurisprudence API"
    echo "  api-text-extractor - PDF Processing"
    echo "  api-doc-assembler  - Document Generation"
    echo "  api-ledes-converter - LEDES Format Converter"
    echo "  api-trello         - Trello Integration"
    echo "  api-ccui-ws        - Chat WebSocket Backend"
    echo ""
    exit 1
fi

echo "Rebuilding $SERVICE..."
docker compose -f docker-compose.dev.yml build "$SERVICE"

echo "Restarting $SERVICE..."
docker compose -f docker-compose.dev.yml up -d "$SERVICE"

echo ""
echo "Done! $SERVICE has been rebuilt and restarted."
echo "Check logs: ./scripts/logs.sh $SERVICE"

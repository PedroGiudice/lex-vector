#!/bin/bash
# legal-workbench/scripts/logs.sh
# View formatted logs from services

cd "$(dirname "$0")/.."

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "Showing logs for all services (Ctrl+C to exit)..."
    docker compose -f docker-compose.dev.yml logs -f --tail=100
else
    echo "Showing logs for $SERVICE (Ctrl+C to exit)..."
    docker compose -f docker-compose.dev.yml logs -f --tail=100 "$SERVICE"
fi

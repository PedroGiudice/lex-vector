#!/bin/bash
# legal-workbench/scripts/clean.sh
# Clean development environment
set -e

echo "Cleaning development environment..."

cd "$(dirname "$0")/.."

echo ""
echo "Stopping and removing containers, networks, and volumes..."
docker compose -f docker-compose.dev.yml down -v --remove-orphans

echo ""
echo "Pruning unused Docker resources..."
docker system prune -f

echo ""
echo "Clean complete!"
echo ""
echo "To start fresh: ./scripts/dev.sh"

#!/bin/bash
# Rebuild frontend with cache busting
# Usage: ./scripts/rebuild-frontend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

CACHEBUST=$(date +%s)

echo "=== Rebuilding frontend-react ==="
echo "Timestamp: $CACHEBUST"

# Build with cache buster arg (forces fresh build)
TRELLO_API_KEY="${TRELLO_API_KEY}" \
TRELLO_API_TOKEN="${TRELLO_API_TOKEN}" \
docker compose build frontend-react \
  --build-arg "CACHEBUST=$CACHEBUST" \
  --no-cache

# Prune dangling images left by multi-stage build
docker image prune -f 2>/dev/null

# Recreate container with new image
TRELLO_API_KEY="${TRELLO_API_KEY}" \
TRELLO_API_TOKEN="${TRELLO_API_TOKEN}" \
docker compose up -d frontend-react --force-recreate

echo "=== Waiting for healthy status ==="
sleep 3
docker compose ps frontend-react

# Verify bundle contains expected code
echo ""
echo "=== Bundle verification ==="
docker compose exec frontend-react sh -c 'ls -la /usr/share/nginx/html/assets/ | grep -E "index-|TrelloModule"'

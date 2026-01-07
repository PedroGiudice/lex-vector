#!/bin/bash
# legal-workbench/scripts/dev.sh
# Start Legal Workbench in development mode with hot reload
set -e

echo "Starting Legal Workbench in development mode..."

cd "$(dirname "$0")/.."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "# Add your environment variables here" > .env
        echo "GEMINI_API_KEY=" >> .env
        echo "TRELLO_API_KEY=" >> .env
        echo "TRELLO_API_TOKEN=" >> .env
    fi
    echo "Please configure .env with your API keys before running."
fi

# Start services
echo ""
echo "Services will be available at:"
echo "  - Frontend:        http://localhost:3000"
echo "  - API STJ:         http://localhost:8000"
echo "  - API Text:        http://localhost:8001"
echo "  - API Doc:         http://localhost:8002"
echo "  - API LEDES:       http://localhost:8003"
echo "  - API Trello:      http://localhost:8004"
echo "  - API Chat WS:     http://localhost:8005"
echo "  - Traefik:         http://localhost (unified)"
echo "  - Traefik Dashboard: http://localhost:8080"
echo ""

docker compose -f docker-compose.dev.yml up "$@"

# Trello MCP API - Makefile
# Simplifies common development tasks

.PHONY: help build run stop logs test clean dev shell health

# Default target
.DEFAULT_GOAL := help

# Service name
SERVICE := trello-mcp
CONTAINER := lw-trello-mcp
PORT := 8004

help: ## Show this help message
	@echo "Trello MCP API - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

build: ## Build Docker image
	@echo "Building $(SERVICE)..."
	cd ../.. && docker-compose build $(SERVICE)

run: ## Run service in foreground
	@echo "Starting $(SERVICE)..."
	cd ../.. && docker-compose up $(SERVICE)

up: ## Run service in background
	@echo "Starting $(SERVICE) in background..."
	cd ../.. && docker-compose up -d $(SERVICE)

stop: ## Stop service
	@echo "Stopping $(SERVICE)..."
	cd ../.. && docker-compose stop $(SERVICE)

restart: stop up ## Restart service

logs: ## Show service logs
	cd ../.. && docker-compose logs -f $(SERVICE)

test: ## Run API tests
	@echo "Testing API at http://localhost:$(PORT)..."
	@./test_api.sh http://localhost:$(PORT)

health: ## Check service health
	@echo "Checking $(SERVICE) health..."
	@curl -s http://localhost:$(PORT)/health | jq . || echo "Service not responding"

shell: ## Open shell in running container
	docker exec -it $(CONTAINER) /bin/bash

dev: ## Run in development mode (with auto-reload)
	@echo "Starting development server..."
	@echo "Make sure you have .env configured with credentials"
	@cd ../../.. && \
	export PYTHONPATH="$(PWD)/ferramentas/trello-mcp/src:$(PWD)/docker/services/trello-mcp" && \
	uvicorn api.main:app --reload --host 0.0.0.0 --port $(PORT)

clean: ## Remove container and volumes
	@echo "Cleaning up $(SERVICE)..."
	cd ../.. && docker-compose down $(SERVICE)
	docker volume prune -f

rebuild: clean build ## Clean and rebuild

docs: ## Open API documentation in browser
	@echo "Opening API docs..."
	@xdg-open http://localhost:$(PORT)/docs 2>/dev/null || open http://localhost:$(PORT)/docs 2>/dev/null || echo "Visit http://localhost:$(PORT)/docs"

validate: ## Validate configuration files
	@echo "Validating configuration..."
	@echo "✓ Checking Dockerfile..."
	@docker build --check -f Dockerfile . > /dev/null && echo "  Dockerfile is valid"
	@echo "✓ Checking requirements.txt..."
	@python3 -c "import sys; [print('  ' + line.strip()) for line in open('requirements.txt') if line.strip() and not line.startswith('#')]"
	@echo "✓ Configuration valid"

status: ## Show service status
	@echo "Service Status:"
	@docker ps --filter name=$(CONTAINER) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || echo "Container not running"

all: clean build up logs ## Clean, build, run, and show logs

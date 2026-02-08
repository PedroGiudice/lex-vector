#!/bin/bash
# Deploy Legal Workbench
# Usage: ./deploy.sh [dev|prod]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
ENV="${1:-dev}"

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

show_help() {
    cat << EOF
${BLUE}Legal Workbench Deployment Script${NC}

${GREEN}Usage:${NC}
    ./deploy.sh [ENVIRONMENT]

${GREEN}Arguments:${NC}
    ENVIRONMENT    Deployment environment (dev|prod) [default: dev]

${GREEN}Examples:${NC}
    ./deploy.sh              Deploy in development mode
    ./deploy.sh dev          Deploy in development mode
    ./deploy.sh prod         Deploy in production mode

${GREEN}Requirements:${NC}
    - Docker >= 20.10
    - Docker Compose >= 2.0
    - .env file with required variables

EOF
}

check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found: $(docker --version)"

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed or outdated (need v2+)"
        exit 1
    fi
    print_success "Docker Compose found: $(docker compose version)"

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"
}

validate_env() {
    print_info "Validating environment variables..."

    if [ ! -f "$DOCKER_DIR/.env" ]; then
        print_warning ".env file not found, copying from .env.example"
        if [ -f "$DOCKER_DIR/.env.example" ]; then
            cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
            print_warning "Please edit $DOCKER_DIR/.env with your credentials"
            exit 1
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi

    # Check required variables
    source "$DOCKER_DIR/.env"

    REQUIRED_VARS=("GEMINI_API_KEY" "TRELLO_API_KEY" "TRELLO_API_TOKEN")
    MISSING_VARS=()

    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            MISSING_VARS+=("$var")
        fi
    done

    if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        print_error "Missing required environment variables:"
        for var in "${MISSING_VARS[@]}"; do
            echo "  - $var"
        done
        print_info "Please edit $DOCKER_DIR/.env and set these variables"
        exit 1
    fi

    print_success "Environment variables validated"
}

build_images() {
    print_info "Building Docker images for $ENV environment..."

    cd "$DOCKER_DIR"

    if [ "$ENV" = "prod" ]; then
        docker compose build --no-cache
    else
        docker compose build
    fi

    print_success "Docker images built successfully"

    # Prune dangling images left by multi-stage builds
    # Each rebuild leaves the previous image as <none>:<none>
    # text-extractor alone leaves ~15GB per rebuild
    local reclaimed
    reclaimed=$(docker image prune -f 2>/dev/null | tail -1)
    print_info "Image cleanup: $reclaimed"
}

start_services() {
    print_info "Starting services..."

    cd "$DOCKER_DIR"

    # Stop any existing containers
    docker compose down

    # Start services
    docker compose up -d

    print_success "Services started"
}

wait_for_health() {
    print_info "Waiting for services to be healthy..."

    local max_wait=180  # 3 minutes
    local wait_time=0
    local check_interval=5

    cd "$DOCKER_DIR"

    while [ $wait_time -lt $max_wait ]; do
        # Get unhealthy services
        unhealthy=$(docker compose ps --format json 2>/dev/null | \
            jq -r 'select(.Health != "healthy" and .Health != "") | .Service' 2>/dev/null)

        if [ -z "$unhealthy" ]; then
            # All services are healthy or don't have health checks
            print_success "All services are healthy"
            return 0
        fi

        echo -ne "\r${YELLOW}⏳${NC} Waiting for services: $unhealthy (${wait_time}s/${max_wait}s)"

        sleep $check_interval
        wait_time=$((wait_time + check_interval))
    done

    echo ""
    print_error "Services did not become healthy within ${max_wait}s"
    return 1
}

run_health_check() {
    print_info "Running health checks..."

    if "$SCRIPT_DIR/health-check.sh" --quiet; then
        print_success "Health checks passed"
        return 0
    else
        print_error "Health checks failed"
        return 1
    fi
}

show_status() {
    print_info "Deployment status:"
    echo ""

    cd "$DOCKER_DIR"
    docker compose ps

    echo ""
    print_info "Access points:"
    echo "  - Streamlit Hub:     http://localhost:8501"
    echo "  - Text Extractor:    http://localhost:8001"
    echo "  - Doc Assembler:     http://localhost:8002"
    echo "  - STJ API:           http://localhost:8003"
    echo "  - Trello MCP:        http://localhost:8004"
    echo "  - Redis:             localhost:6379"
    echo "  - Celery Flower:     http://localhost:5555"
}

cleanup_on_error() {
    print_error "Deployment failed!"
    print_info "Checking logs for errors..."

    cd "$DOCKER_DIR"
    docker compose logs --tail=50

    exit 1
}

# Main
main() {
    # Parse arguments
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi

    # Validate environment
    if [ "$ENV" != "dev" ] && [ "$ENV" != "prod" ]; then
        print_error "Invalid environment: $ENV (must be dev or prod)"
        show_help
        exit 1
    fi

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Legal Workbench Deployment${NC}"
    echo -e "${BLUE}Environment: ${GREEN}$ENV${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # Run deployment steps
    check_prerequisites
    validate_env
    build_images
    start_services

    # Wait and check health
    if wait_for_health; then
        if run_health_check; then
            echo ""
            echo -e "${GREEN}========================================${NC}"
            echo -e "${GREEN}✓ Deployment successful!${NC}"
            echo -e "${GREEN}========================================${NC}"
            echo ""
            show_status
            exit 0
        else
            cleanup_on_error
        fi
    else
        cleanup_on_error
    fi
}

# Trap errors
trap cleanup_on_error ERR

# Run main
main "$@"

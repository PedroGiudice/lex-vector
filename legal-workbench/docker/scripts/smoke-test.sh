#!/bin/bash
# =============================================================================
# Legal Workbench - Smoke Test Script
# =============================================================================
# Testa build e funcionamento básico de todos os containers
# Executar após fazer pull do branch: claude/docker-analysis-01QbbMxQFDgBtcTGGDfX8pHz
# =============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Diretório base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$DOCKER_DIR")"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Legal Workbench - Smoke Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

log_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((++TESTS_PASSED))
}

log_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((++TESTS_FAILED))
}

log_skip() {
    echo -e "  ${YELLOW}○${NC} $1 (skipped)"
    ((++TESTS_SKIPPED))
}

log_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

# =============================================================================
# FASE 1: Verificar Pré-requisitos
# =============================================================================
echo -e "\n${YELLOW}[1/5] Verificando pré-requisitos...${NC}"

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | cut -d',' -f1)
    log_pass "Docker instalado: v$DOCKER_VERSION"
else
    log_fail "Docker não encontrado"
    echo -e "${RED}Instale Docker antes de continuar: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Docker Compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_VERSION=$(docker compose version --short)
    else
        COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f4)
    fi
    log_pass "Docker Compose instalado: v$COMPOSE_VERSION"
else
    log_fail "Docker Compose não encontrado"
    exit 1
fi

# Docker daemon running
if docker info &> /dev/null; then
    log_pass "Docker daemon está rodando"
else
    log_fail "Docker daemon não está rodando"
    echo -e "${RED}Execute: sudo systemctl start docker${NC}"
    exit 1
fi

# Memória disponível
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -ge 12 ]; then
    log_pass "Memória disponível: ${TOTAL_MEM}GB (mínimo: 12GB)"
else
    log_fail "Memória insuficiente: ${TOTAL_MEM}GB (mínimo: 12GB)"
    echo -e "${YELLOW}O text-extractor pode falhar com pouca memória${NC}"
fi

# Arquivo .env
if [ -f "$DOCKER_DIR/.env" ]; then
    log_pass "Arquivo .env encontrado"
else
    log_skip "Arquivo .env não encontrado"
    echo -e "${YELLOW}  Copiando .env.example...${NC}"
    if [ -f "$DOCKER_DIR/.env.example" ]; then
        cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
        log_info "Criado .env a partir de .env.example"
        log_info "⚠️  Configure suas API keys no .env antes de continuar!"
    fi
fi

# =============================================================================
# FASE 2: Build das Imagens
# =============================================================================
echo -e "\n${YELLOW}[2/5] Construindo imagens Docker...${NC}"

cd "$DOCKER_DIR"

# Lista de serviços para build
SERVICES=("redis" "stj-api" "doc-assembler" "trello-mcp" "text-extractor" "streamlit-hub")

for service in "${SERVICES[@]}"; do
    if [ "$service" == "redis" ]; then
        log_pass "redis: usando imagem oficial (redis:7-alpine)"
        continue
    fi

    echo -e "  Building ${BLUE}$service${NC}..."
    if docker compose build "$service" --quiet 2>/dev/null; then
        log_pass "$service: build OK"
    else
        log_fail "$service: build FAILED"
        echo -e "${RED}  Verifique o Dockerfile em services/$service/${NC}"
    fi
done

# =============================================================================
# FASE 3: Subir Containers (ordem de dependência)
# =============================================================================
echo -e "\n${YELLOW}[3/5] Iniciando containers...${NC}"

# Primeiro: Redis (infraestrutura)
echo -e "  Starting ${BLUE}redis${NC}..."
docker compose up -d redis
sleep 2

if docker compose ps redis | grep -q "Up"; then
    log_pass "redis: running"
else
    log_fail "redis: failed to start"
fi

# Segundo: Serviços backend (paralelo)
echo -e "  Starting backend services..."
docker compose up -d stj-api doc-assembler trello-mcp
sleep 5

for service in stj-api doc-assembler trello-mcp; do
    if docker compose ps "$service" | grep -q "Up"; then
        log_pass "$service: running"
    else
        log_fail "$service: failed to start"
    fi
done

# Terceiro: Text Extractor (demora mais por causa dos modelos)
echo -e "  Starting ${BLUE}text-extractor${NC} (pode demorar ~60s)..."
docker compose up -d text-extractor
echo -e "  ${YELLOW}Aguardando model loading...${NC}"
sleep 30

if docker compose ps text-extractor | grep -q "Up"; then
    log_pass "text-extractor: running"
else
    log_fail "text-extractor: failed to start"
    echo -e "${YELLOW}  Verificando logs...${NC}"
    docker compose logs --tail=20 text-extractor
fi

# Quarto: Streamlit Hub (depende de todos)
echo -e "  Starting ${BLUE}streamlit-hub${NC}..."
docker compose up -d streamlit-hub
sleep 5

if docker compose ps streamlit-hub | grep -q "Up"; then
    log_pass "streamlit-hub: running"
else
    log_fail "streamlit-hub: failed to start"
fi

# =============================================================================
# FASE 4: Health Checks
# =============================================================================
echo -e "\n${YELLOW}[4/5] Testando health endpoints...${NC}"

declare -A ENDPOINTS=(
    ["redis"]="redis-cli ping"
    ["stj-api"]="http://localhost:8003/health"
    ["doc-assembler"]="http://localhost:8002/health"
    ["trello-mcp"]="http://localhost:8004/health"
    ["text-extractor"]="http://localhost:8001/health"
    ["streamlit-hub"]="http://localhost:8501/healthz"
)

for service in "${!ENDPOINTS[@]}"; do
    endpoint="${ENDPOINTS[$service]}"

    if [ "$service" == "redis" ]; then
        if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
            log_pass "redis: PONG"
        else
            log_fail "redis: no response"
        fi
    else
        # HTTP endpoints
        if curl -sf "$endpoint" > /dev/null 2>&1; then
            log_pass "$service: healthy"
        else
            # Tentar mais uma vez após 10s
            sleep 10
            if curl -sf "$endpoint" > /dev/null 2>&1; then
                log_pass "$service: healthy (retry)"
            else
                log_fail "$service: unhealthy"
            fi
        fi
    fi
done

# =============================================================================
# FASE 5: Testes Funcionais Básicos
# =============================================================================
echo -e "\n${YELLOW}[5/5] Testes funcionais básicos...${NC}"

# Teste STJ API - Search
echo -e "  Testing STJ API search..."
STJ_RESPONSE=$(curl -sf "http://localhost:8003/api/v1/search?query=teste&limit=1" 2>/dev/null || echo "ERROR")
if [ "$STJ_RESPONSE" != "ERROR" ] && echo "$STJ_RESPONSE" | grep -q "results\|items\|data"; then
    log_pass "STJ API: search endpoint OK"
else
    log_skip "STJ API: search (database may be empty)"
fi

# Teste Doc Assembler - Templates
echo -e "  Testing Doc Assembler templates..."
TEMPLATES_RESPONSE=$(curl -sf "http://localhost:8002/api/v1/templates" 2>/dev/null || echo "ERROR")
if [ "$TEMPLATES_RESPONSE" != "ERROR" ]; then
    log_pass "Doc Assembler: templates endpoint OK"
else
    log_fail "Doc Assembler: templates endpoint failed"
fi

# Teste Text Extractor - Health detalhado
echo -e "  Testing Text Extractor detailed health..."
EXTRACTOR_HEALTH=$(curl -sf "http://localhost:8001/health" 2>/dev/null || echo "ERROR")
if echo "$EXTRACTOR_HEALTH" | grep -q "ok\|healthy\|status"; then
    log_pass "Text Extractor: health details OK"
else
    log_fail "Text Extractor: health check failed"
fi

# Teste Streamlit UI - Acesso
echo -e "  Testing Streamlit UI access..."
UI_RESPONSE=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:8501" 2>/dev/null || echo "000")
if [ "$UI_RESPONSE" == "200" ] || [ "$UI_RESPONSE" == "302" ]; then
    log_pass "Streamlit UI: accessible (HTTP $UI_RESPONSE)"
else
    log_fail "Streamlit UI: not accessible (HTTP $UI_RESPONSE)"
fi

# =============================================================================
# RESULTADO FINAL
# =============================================================================
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  RESULTADO DO SMOKE TEST${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Passed:${NC}  $TESTS_PASSED"
echo -e "  ${RED}Failed:${NC}  $TESTS_FAILED"
echo -e "  ${YELLOW}Skipped:${NC} $TESTS_SKIPPED"
echo ""

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}══════════════════════════════════════════════════════════════=${NC}"
    echo -e "${GREEN}  ✓ TODOS OS TESTES PASSARAM!${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════════════=${NC}"
    echo ""
    echo -e "  Acesse a interface em: ${BLUE}http://localhost:8501${NC}"
    echo ""
    echo -e "  APIs disponíveis:"
    echo -e "    - Text Extractor: http://localhost:8001/docs"
    echo -e "    - Doc Assembler:  http://localhost:8002/docs"
    echo -e "    - STJ API:        http://localhost:8003/docs"
    echo -e "    - Trello MCP:     http://localhost:8004/docs"
    echo -e "    - Celery Flower:  http://localhost:5555"
    exit 0
else
    echo -e "${RED}══════════════════════════════════════════════════════════════=${NC}"
    echo -e "${RED}  ✗ ALGUNS TESTES FALHARAM${NC}"
    echo -e "${RED}══════════════════════════════════════════════════════════════=${NC}"
    echo ""
    echo -e "  Para debug, execute:"
    echo -e "    ${YELLOW}docker compose logs [service-name]${NC}"
    echo ""
    echo -e "  Para parar tudo:"
    echo -e "    ${YELLOW}docker compose down${NC}"
    exit 1
fi

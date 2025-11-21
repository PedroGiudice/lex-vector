#!/bin/bash
#
# Script para executar scheduler em background
#
# Uso:
#   ./run_scheduler.sh            # Executar em background
#   ./run_scheduler.sh --now      # Executar job imediatamente + agendar
#   ./run_scheduler.sh --stop     # Parar scheduler em execução
#   ./run_scheduler.sh --status   # Verificar status
#

set -e

# Diretórios
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_FILE="$SCRIPT_DIR/scheduler.pid"
LOG_FILE="$LOG_DIR/scheduler_background.log"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função: verificar se scheduler está rodando
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Rodando
        else
            rm -f "$PID_FILE"
            return 1  # PID file obsoleto
        fi
    fi
    return 1  # Não rodando
}

# Função: parar scheduler
stop_scheduler() {
    echo -e "${YELLOW}Parando scheduler...${NC}"

    if ! is_running; then
        echo -e "${RED}Scheduler não está em execução${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")
    echo "Enviando SIGTERM para PID $PID..."

    kill -TERM "$PID" 2>/dev/null || true

    # Aguardar até 30 segundos
    for i in {1..30}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Scheduler parado com sucesso${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # Se não parou, forçar
    echo -e "${YELLOW}Forçando parada (SIGKILL)...${NC}"
    kill -KILL "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Scheduler forçado a parar${NC}"
}

# Função: mostrar status
show_status() {
    echo "======================================================================"
    echo "STATUS DO SCHEDULER"
    echo "======================================================================"

    if is_running; then
        PID=$(cat "$PID_FILE")
        echo -e "${GREEN}✓ Scheduler em execução${NC}"
        echo "  PID: $PID"
        echo "  Uptime: $(ps -p $PID -o etime= | tr -d ' ')"
        echo "  Log: $LOG_FILE"
        echo ""
        echo "Últimas linhas do log:"
        tail -20 "$LOG_FILE" 2>/dev/null || echo "(log vazio)"
    else
        echo -e "${RED}✗ Scheduler não está em execução${NC}"
    fi

    echo "======================================================================"
}

# Função: iniciar scheduler
start_scheduler() {
    local ARGS="$1"

    echo "======================================================================"
    echo "INICIANDO SCHEDULER EM BACKGROUND"
    echo "======================================================================"

    # Verificar se já está rodando
    if is_running; then
        echo -e "${YELLOW}⚠ Scheduler já está em execução!${NC}"
        show_status
        exit 1
    fi

    # Criar diretório de logs
    mkdir -p "$LOG_DIR"

    # Ativar venv e executar
    cd "$SCRIPT_DIR"
    source .venv/bin/activate

    echo "Executando scheduler..."
    echo "  Log: $LOG_FILE"
    echo "  PID file: $PID_FILE"

    if [ -n "$ARGS" ]; then
        echo "  Argumentos: $ARGS"
    fi

    # Executar em background
    nohup python scheduler.py $ARGS > "$LOG_FILE" 2>&1 &
    PID=$!

    # Salvar PID
    echo "$PID" > "$PID_FILE"

    # Aguardar 2 segundos e verificar se ainda está rodando
    sleep 2

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Scheduler iniciado com sucesso!${NC}"
        echo "  PID: $PID"
        echo ""
        echo "Comandos úteis:"
        echo "  ./run_scheduler.sh --status   # Ver status e logs"
        echo "  ./run_scheduler.sh --stop     # Parar scheduler"
        echo "  tail -f $LOG_FILE  # Acompanhar log em tempo real"
    else
        echo -e "${RED}✗ Erro ao iniciar scheduler${NC}"
        echo "Verifique o log: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi

    echo "======================================================================"
}

# ==============================================================================
# MAIN
# ==============================================================================

case "${1:-}" in
    --stop)
        stop_scheduler
        ;;
    --status)
        show_status
        ;;
    --now)
        start_scheduler "--now"
        ;;
    "")
        start_scheduler ""
        ;;
    *)
        echo "Uso: $0 [--now|--stop|--status]"
        echo ""
        echo "Opções:"
        echo "  (sem opções)  Iniciar scheduler em background"
        echo "  --now         Executar job imediatamente + agendar"
        echo "  --stop        Parar scheduler em execução"
        echo "  --status      Verificar status e ver logs"
        exit 1
        ;;
esac

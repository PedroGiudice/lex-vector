#!/bin/bash

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKER="${SCRIPT_DIR}/../simple_tracker.py"

# Load logger library
source "${SCRIPT_DIR}/lib/logger.sh"

# Recebe JSON do Claude Code
INPUT=$(cat)

# Sanitize SESSION_ID - remove all chars except alphanumeric, underscore, hyphen
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' | tr -cd 'a-zA-Z0-9_-')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

log_debug "detect_agents" "Starting agent detection" "$SESSION_ID"

# Se não há transcript, skip
if [ -z "$TRANSCRIPT" ] || [ "$TRANSCRIPT" = "null" ]; then
    log_debug "detect_agents" "No transcript provided, skipping" "$SESSION_ID"
    echo "$INPUT"
    exit 0
fi

# Verifica se transcript existe
if [ ! -f "$TRANSCRIPT" ]; then
    log_warn "detect_agents" "Transcript file not found: $TRANSCRIPT" "$SESSION_ID"
    echo "$INPUT"
    exit 0
fi

log_info "detect_agents" "Processing transcript: $TRANSCRIPT" "$SESSION_ID"

# Extrai últimas mensagens do assistant
RECENT=$(tail -n 10 "$TRANSCRIPT" 2>/dev/null | jq -r 'select(.role=="assistant") | .content' 2>/dev/null || echo "")

# Detecta patterns de spawn de agentes
# Pattern 1: @agent-name
AGENTS=$(echo "$RECENT" | grep -oP '@[a-z][a-z0-9-]*' | tr -d '@' | sort -u)

# Pattern 2: "creating subagent"
if echo "$RECENT" | grep -qiE '(creating|spawning|delegating to).*(subagent|agent)'; then
    log_info "detect_agents" "Detected orchestrator spawn pattern" "$SESSION_ID"
    # Registra evento genérico
    if "$TRACKER" agent "orchestrator-spawn" spawning "$SESSION_ID" 2>&1; then
        log_info "detect_agents" "Tracked orchestrator spawn" "$SESSION_ID"
    else
        log_error "detect_agents" "Failed to track orchestrator spawn" "$SESSION_ID"
    fi
fi

# Registra cada agente detectado
for AGENT in $AGENTS; do
    if [ -n "$AGENT" ]; then
        log_info "detect_agents" "Detected agent: $AGENT" "$SESSION_ID"
        if "$TRACKER" agent "$AGENT" active "$SESSION_ID" 2>&1; then
            log_info "detect_agents" "Tracked agent: $AGENT" "$SESSION_ID"
        else
            log_error "detect_agents" "Failed to track agent: $AGENT" "$SESSION_ID"
        fi
    fi
done

# Retorna input inalterado
echo "$INPUT"

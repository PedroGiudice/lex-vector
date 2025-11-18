#!/bin/bash

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKER="${SCRIPT_DIR}/../simple_tracker.py"

# Recebe JSON do Claude Code
INPUT=$(cat)

# Sanitize SESSION_ID - remove all chars except alphanumeric, underscore, hyphen
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' | tr -cd 'a-zA-Z0-9_-')
TRANSCRIPT=$(echo "$INPUT" | jq -r '.transcript_path // ""')

# Se não há transcript, skip
[ -z "$TRANSCRIPT" ] || [ "$TRANSCRIPT" = "null" ] && echo "$INPUT" && exit 0

# Verifica se transcript existe
[ ! -f "$TRANSCRIPT" ] && echo "$INPUT" && exit 0

# Extrai últimas mensagens do assistant
RECENT=$(tail -n 10 "$TRANSCRIPT" 2>/dev/null | jq -r 'select(.role=="assistant") | .content' 2>/dev/null || echo "")

# Detecta patterns de spawn de agentes
# Pattern 1: @agent-name
AGENTS=$(echo "$RECENT" | grep -oP '@[a-z][a-z0-9-]*' | tr -d '@' | sort -u)

# Pattern 2: "creating subagent"
if echo "$RECENT" | grep -qiE '(creating|spawning|delegating to).*(subagent|agent)'; then
    # Registra evento genérico
    "$TRACKER" agent "orchestrator-spawn" spawning "$SESSION_ID" 2>/dev/null || true
fi

# Registra cada agente detectado
for AGENT in $AGENTS; do
    [ -n "$AGENT" ] && \
        "$TRACKER" agent "$AGENT" active "$SESSION_ID" 2>/dev/null || true
done

# Retorna input inalterado
echo "$INPUT"

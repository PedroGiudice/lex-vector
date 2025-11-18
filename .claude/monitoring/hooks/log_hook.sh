#!/bin/bash

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKER="${SCRIPT_DIR}/../simple_tracker.py"

# Load logger library
source "${SCRIPT_DIR}/lib/logger.sh"

# Primeiro argumento é o nome do hook
HOOK_NAME=${1:-"unknown"}

# Recebe JSON
INPUT=$(cat)
# Sanitize SESSION_ID - remove all chars except alphanumeric, underscore, hyphen
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' | tr -cd 'a-zA-Z0-9_-')

log_debug "log_hook" "Executing: $HOOK_NAME" "$SESSION_ID"

# Registra execução
if "$TRACKER" hook "$HOOK_NAME" "$SESSION_ID" 2>&1; then
    log_info "log_hook" "Tracked hook execution: $HOOK_NAME" "$SESSION_ID"
else
    log_error "log_hook" "Failed to track hook: $HOOK_NAME" "$SESSION_ID"
fi

# Retorna input
echo "$INPUT"

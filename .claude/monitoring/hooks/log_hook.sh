#!/bin/bash

# Get script directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRACKER="${SCRIPT_DIR}/../simple_tracker.py"

# Primeiro argumento é o nome do hook
HOOK_NAME=${1:-"unknown"}

# Recebe JSON
INPUT=$(cat)
# Sanitize SESSION_ID - remove all chars except alphanumeric, underscore, hyphen
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' | tr -cd 'a-zA-Z0-9_-')

# Registra execução
"$TRACKER" hook "$HOOK_NAME" "$SESSION_ID" 2>/dev/null || true

# Retorna input
echo "$INPUT"

#!/bin/bash

# Primeiro argumento é o nome do hook
HOOK_NAME=${1:-"unknown"}

# Recebe JSON
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')

# Registra execução
/home/user/Claude-Code-Projetos/.claude/monitoring/simple_tracker.py hook "$HOOK_NAME" "$SESSION_ID" 2>/dev/null || true

# Retorna input
echo "$INPUT"

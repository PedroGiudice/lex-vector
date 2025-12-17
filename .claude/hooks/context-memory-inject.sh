#!/bin/bash
##
# context-memory-inject.sh - SessionStart hook wrapper for context memory
#
# Wrapper script to ensure proper execution of the Python hook.
##

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
PYTHON="$PROJECT_DIR/.venv/bin/python"
HOOK="$SCRIPT_DIR/context-memory-inject.py"

# Check if Python exists
if [ ! -f "$PYTHON" ]; then
    echo '{"continue": true, "systemMessage": "context-memory: venv not found"}'
    exit 0
fi

# Check if hook exists
if [ ! -f "$HOOK" ]; then
    echo '{"continue": true, "systemMessage": "context-memory: hook not found"}'
    exit 0
fi

# Execute the Python hook
exec "$PYTHON" "$HOOK"

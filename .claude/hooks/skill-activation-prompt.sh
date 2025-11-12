#!/bin/bash
# Wrapper para executar skill-activation-prompt.ts via Node.js

# Verificar se Node.js está disponível
if ! command -v node &> /dev/null; then
    # Node não disponível - falhar silenciosamente
    echo '{"continue": true}' | jq .
    exit 0
fi

# Executar TypeScript via ts-node ou node diretamente
if command -v ts-node &> /dev/null; then
    ts-node "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.ts"
else
    # Fallback: compilar on-the-fly (requer typescript instalado)
    node --loader ts-node/esm "$CLAUDE_PROJECT_DIR/.claude/hooks/skill-activation-prompt.ts" 2>/dev/null || echo '{"continue": true}' | jq .
fi

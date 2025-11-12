#!/bin/bash
# SessionStart Hook - Verifica venv ativo (RULE_006)

if [ -z "$VIRTUAL_ENV" ]; then
    MESSAGE="⚠️  RULE_006 VIOLATION: Virtual environment NÃO está ativo!

Para ativar:
  source .venv/bin/activate

Este é um requisito OBRIGATÓRIO antes de qualquer execução Python."

    cat << EOJSON
{
  "continue": true,
  "systemMessage": "${MESSAGE}"
}
EOJSON
else
    cat << EOJSON
{
  "continue": true,
  "systemMessage": "✓ Virtual environment ativo: ${VIRTUAL_ENV}"
}
EOJSON
fi

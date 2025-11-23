#!/usr/bin/env bash
# vibe-log-safe-wrapper.sh
# Executa vibe-log apenas se autenticado (graceful skip se não autenticado)

set -e

HOOK_TRIGGER="${1:-unknown}"

# Verificar se arquivo .key existe (indica autenticação configurada)
if [ ! -f "$HOME/.vibe-log/.key" ]; then
  # Ambiente não autenticado (Claude Code Web) - skip silenciosamente
  exit 0
fi

# Verificar se config.json tem token
if ! grep -q '"token"' "$HOME/.vibe-log/config.json" 2>/dev/null; then
  # Sem token - skip silenciosamente
  exit 0
fi

# Autenticado - executar vibe-log
npx vibe-log-cli send --silent --hook-trigger="$HOOK_TRIGGER" --hook-version=1.0.0

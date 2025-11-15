#!/bin/bash
# start-claude-with-venv.sh - Inicia Claude Code com venv ativo
#
# RULE_006 compliance: Garante que VIRTUAL_ENV está ativo para todos os hooks
#
# Uso:
#   ./start-claude-with-venv.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

echo "🔧 Ativando venv em: $VENV_PATH"

# Ativar venv
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Erro: venv não encontrado em $VENV_PATH"
    echo "   Crie com: python3 -m venv .venv"
    exit 1
fi

# Exportar VIRTUAL_ENV (necessário para venv-check hook)
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"

echo "✓ VIRTUAL_ENV ativo: $VIRTUAL_ENV"
echo "✓ Python: $(which python)"
echo ""
echo "🚀 Iniciando Claude Code..."

# Iniciar Claude Code
# Tentar via command (global)
if command -v claude &> /dev/null; then
    claude "$PROJECT_ROOT"
# Tentar via NVM path (instalação via npm)
elif [ -f "$HOME/.nvm/versions/node/v24.11.1/bin/claude" ]; then
    "$HOME/.nvm/versions/node/v24.11.1/bin/claude" "$PROJECT_ROOT"
# Tentar via .local/bin
elif [ -f "$HOME/.local/bin/claude" ]; then
    "$HOME/.local/bin/claude" "$PROJECT_ROOT"
else
    echo "❌ Claude Code não encontrado"
    echo "   Caminhos verificados:"
    echo "   - $(which claude 2>/dev/null || echo 'não encontrado via PATH')"
    echo "   - $HOME/.nvm/versions/node/v24.11.1/bin/claude"
    echo "   - $HOME/.local/bin/claude"
    exit 1
fi

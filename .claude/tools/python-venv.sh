#!/bin/bash

##
## Python VEnv Wrapper
##
## Usage: .claude/tools/python-venv.sh <comando>
## Exemplo: .claude/tools/python-venv.sh pip list
##          .claude/tools/python-venv.sh python main.py
##
## CRITICAL: Este wrapper DEVE ser robusto.
## Qualquer erro aqui afeta TODOS os comandos Python do projeto.
##

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Diretório do projeto (usa CLAUDE_PROJECT_DIR ou fallback para localização do script)
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
VENV_PATH="$PROJECT_ROOT/.venv"
VENV_PYTHON="$VENV_PATH/bin/python"
VENV_ACTIVATE="$VENV_PATH/bin/activate"

# Validações CRÍTICAS (fail-fast)
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "ERROR: Project root not found: $PROJECT_ROOT" >&2
  exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
  echo "ERROR: Python venv not found at $VENV_PATH" >&2
  echo "Run: cd $PROJECT_ROOT && python -m venv .venv" >&2
  exit 1
fi

if [ ! -f "$VENV_ACTIVATE" ]; then
  echo "ERROR: venv activation script missing: $VENV_ACTIVATE" >&2
  exit 1
fi

if [ ! -x "$VENV_PYTHON" ]; then
  echo "ERROR: Python interpreter not executable: $VENV_PYTHON" >&2
  exit 1
fi

# Ativar venv
# shellcheck disable=SC1090
source "$VENV_ACTIVATE"

# Validar que ativação funcionou
if [ -z "${VIRTUAL_ENV:-}" ]; then
  echo "ERROR: venv activation failed (VIRTUAL_ENV not set)" >&2
  exit 1
fi

# Executar comando passado como argumento
if [ $# -eq 0 ]; then
  # Nenhum argumento - mostrar help
  echo "Usage: $0 <command> [args...]"
  echo ""
  echo "Examples:"
  echo "  $0 python --version"
  echo "  $0 pip list"
  echo "  $0 python agentes/oab-watcher/main.py"
  echo ""
  echo "Active venv: $VIRTUAL_ENV"
  echo "Python: $(which python)"
  exit 0
fi

# Executar comando COM venv ativo
exec "$@"

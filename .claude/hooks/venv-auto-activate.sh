#!/bin/bash

##
## VEnv Auto-Activate Hook
##
## Trigger: SessionStart
## Behavior: Ativa automaticamente o venv do projeto
##
## Problema que resolve:
## - Bash tool não mantém estado entre comandos
## - Cada comando precisa de "source .venv/bin/activate &&"
## - Usuário não deveria ter que lembrar disso
##

PROJECT_ROOT="/home/cmr-auto/claude-work/repos/Claude-Code-Projetos"
VENV_PATH="$PROJECT_ROOT/.venv"

# Cores para output
CYAN='\x1b[38;5;51m'
GREEN='\x1b[38;5;48m'
YELLOW='\x1b[38;5;227m'
GRAY='\x1b[38;5;245m'
RESET='\x1b[0m'

# Verificar se venv existe
if [ ! -d "$VENV_PATH" ]; then
  echo -e "${YELLOW}⚠️  Python venv not found at $VENV_PATH${RESET}"
  echo -e "${GRAY}   Run: python -m venv .venv${RESET}"
  exit 0
fi

# Ativar venv
source "$VENV_PATH/bin/activate"

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Python venv activated:${RESET} ${CYAN}$(which python)${RESET}"
  echo -e "${GRAY}   Python version: $(python --version)${RESET}"
else
  echo -e "${YELLOW}⚠️  Failed to activate venv${RESET}"
  exit 1
fi

# Exportar para subprocessos (não funciona entre comandos Bash tool, mas documenta intenção)
export VIRTUAL_ENV="$VENV_PATH"
export PATH="$VENV_PATH/bin:$PATH"

# Criar/atualizar session-start.json para statusline tracking
SESSION_START_FILE="$PROJECT_ROOT/.claude/statusline/session-start.json"
mkdir -p "$(dirname "$SESSION_START_FILE")"
TIMESTAMP=$(date +%s)000  # milliseconds
echo "{\"timestamp\":$TIMESTAMP}" > "$SESSION_START_FILE"

exit 0

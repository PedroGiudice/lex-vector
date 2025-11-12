#!/bin/bash
# SessionStart Hook - Injeta contexto essencial do projeto

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/user/Claude-Code-Projetos}"

# Ler contexto do projeto
CONTEXT=""

# 1. Arquitetura 3 Layers
CONTEXT+="
ARQUITETURA DO PROJETO:
- LAYER_1_CODE: Código em Git (/home/user/Claude-Code-Projetos)
- LAYER_2_ENVIRONMENT: venv local (.venv/)
- LAYER_3_DATA: Dados externos (configurável via env vars)

REGRAS CRÍTICAS:
- RULE_006: venv SEMPRE obrigatório
- RULE_004: NUNCA hardcode paths
- LESSON_001: Código NUNCA em HD externo
"

# 2. Skills disponíveis
if [ -d "${PROJECT_DIR}/skills" ]; then
    SKILL_COUNT=$(find "${PROJECT_DIR}/skills" -maxdepth 1 -type d 2>/dev/null | wc -l)
    CONTEXT+="
SKILLS DISPONÍVEIS: $((SKILL_COUNT - 1)) skills instaladas
Localização: ${PROJECT_DIR}/skills/
"
fi

# 3. Agentes disponíveis
if [ -d "${PROJECT_DIR}/.claude/agents" ]; then
    AGENT_COUNT=$(find "${PROJECT_DIR}/.claude/agents" -name "*.md" 2>/dev/null | wc -l)
    if [ $AGENT_COUNT -gt 0 ]; then
        CONTEXT+="
AGENTES ESPECIALIZADOS: ${AGENT_COUNT} agentes
"
        find "${PROJECT_DIR}/.claude/agents" -name "*.md" -exec basename {} .md \; 2>/dev/null | sed 's/^/  - /'
    fi
fi

# Output JSON
cat << EOJSON
{
  "continue": true,
  "systemMessage": "${CONTEXT}"
}
EOJSON

#!/bin/bash
# ============================================================================
# validate-hook.sh - Valida hooks antes de adicionar a settings.json
# ============================================================================

set -e

if [ -z "$1" ]; then
  echo "❌ Uso: ./validate-hook.sh <hook-name>.js"
  echo ""
  echo "Exemplos:"
  echo "  ./validate-hook.sh git-status-watcher.js"
  echo "  ./validate-hook.sh data-layer-validator.js"
  exit 1
fi

HOOK=$1
HOOK_PATH=".claude/hooks/$HOOK"

if [ ! -f "$HOOK_PATH" ]; then
  echo "❌ Hook não encontrado: $HOOK_PATH"
  exit 1
fi

echo "🧪 Validando hook: $HOOK"
echo "=" | tr '\n' '=' | head -c 70 && echo ""
echo ""

# ============================================================================
# TESTE 1: Sintaxe JavaScript
# ============================================================================
echo "[1/5] Verificando sintaxe JavaScript..."
node --check "$HOOK_PATH" 2>&1
if [ $? -eq 0 ]; then
  echo "   ✅ Sintaxe válida"
else
  echo "   ❌ FALHOU: Erro de sintaxe"
  exit 1
fi

# ============================================================================
# TESTE 2: Timeout (1s máximo)
# ============================================================================
echo ""
echo "[2/5] Testando execução com timeout (1s máximo)..."
timeout 1s node "$HOOK_PATH" > /tmp/hook-output.json 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
  echo "   ❌ FALHOU: Hook travou (timeout 1s)"
  echo "   ⚠️  Hooks DEVEM terminar em <500ms"
  exit 1
elif [ $EXIT_CODE -ne 0 ]; then
  echo "   ❌ FALHOU: Hook retornou código de erro $EXIT_CODE"
  cat /tmp/hook-output.json
  exit 1
else
  echo "   ✅ Executou em <1s"
fi

# ============================================================================
# TESTE 3: Output é JSON válido
# ============================================================================
echo ""
echo "[3/5] Validando output JSON..."
cat /tmp/hook-output.json | jq . > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "   ❌ FALHOU: Output não é JSON válido"
  echo "   Output recebido:"
  cat /tmp/hook-output.json
  exit 1
else
  echo "   ✅ JSON válido"
fi

# ============================================================================
# TESTE 4: Estrutura do output
# ============================================================================
echo ""
echo "[4/5] Verificando estrutura do output..."

HAS_CONTINUE=$(cat /tmp/hook-output.json | jq -r '.continue')

if [ "$HAS_CONTINUE" != "true" ]; then
  echo "   ❌ FALHOU: Output deve ter { continue: true }"
  cat /tmp/hook-output.json | jq .
  exit 1
else
  echo "   ✅ Estrutura correta (continue: true)"
fi

# ============================================================================
# TESTE 5: Run-once guard (segunda execução deve ser instantânea)
# ============================================================================
echo ""
echo "[5/5] Testando run-once guard (segunda execução)..."

# Resetar env vars primeiro (para alguns hooks)
unset CLAUDE_GIT_STATUS_CHECKED
unset CLAUDE_DATA_LAYER_VALIDATED
unset CLAUDE_DEPS_CHECKED
unset CLAUDE_ERRORS_CHECKED
unset CLAUDE_LEGAL_CONTEXT_INJECTED

# Primeira execução
node "$HOOK_PATH" > /tmp/hook-first.json 2>&1

# Segunda execução (deve ser instantânea se run-once guard funciona)
START_TIME=$(date +%s%N)
node "$HOOK_PATH" > /tmp/hook-second.json 2>&1
END_TIME=$(date +%s%N)

ELAPSED_MS=$(( (END_TIME - START_TIME) / 1000000 ))

if [ $ELAPSED_MS -lt 100 ]; then
  echo "   ✅ Segunda execução em ${ELAPSED_MS}ms (run-once guard funcionando)"
else
  echo "   ⚠️  Segunda execução em ${ELAPSED_MS}ms (pode não ter run-once guard)"
  echo "   💡 Isso é OK se hook é stateless"
fi

# ============================================================================
# RESUMO
# ============================================================================
echo ""
echo "=" | tr '\n' '=' | head -c 70 && echo ""
echo "✅ HOOK VALIDADO COM SUCESSO!"
echo "=" | tr '\n' '=' | head -c 70 && echo ""
echo ""

echo "📋 Output do hook:"
cat /tmp/hook-output.json | jq .
echo ""

HAS_MESSAGE=$(cat /tmp/hook-output.json | jq -r '.systemMessage // empty')
if [ ! -z "$HAS_MESSAGE" ]; then
  echo "💬 Mensagem que será injetada:"
  echo "---"
  echo "$HAS_MESSAGE"
  echo "---"
  echo ""
fi

echo "🚀 Próximos passos:"
echo "   1. Adicione a settings.local.json para teste integrado:"
echo "      {"
echo "        \"hooks\": {"
echo "          \"UserPromptSubmit\": [{"
echo "            \"hooks\": [{"
echo "              \"type\": \"command\","
echo "              \"command\": \"node .claude/hooks/$HOOK\""
echo "            }]"
echo "          }]"
echo "        }"
echo "      }"
echo ""
echo "   2. Teste com: claude"
echo ""
echo "   3. Se funcionar, adicione a settings.json e commit"
echo ""

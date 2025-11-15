#!/bin/bash
# Validação Sprint 5 - Adaptação Cache-First - Claude Code Projetos
# Data: 2025-11-15

echo "=========================================="
echo "VALIDAÇÃO SPRINT 5 - CACHE-FIRST"
echo "=========================================="
echo ""

# 1. Verificar path_utils.py
echo "=== 1. PATH_UTILS.PY (shared/utils/) ==="
PATH_UTILS_FILE="shared/utils/path_utils.py"

if [ -f "$PATH_UTILS_FILE" ]; then
    echo "✅ $PATH_UTILS_FILE existe"

    # Verificar funções críticas
    FUNCOES_ESPERADAS=("get_documento_juridico" "get_output_path" "cleanup_temp")
    FUNCOES_FALTANTES=()

    for func in "${FUNCOES_ESPERADAS[@]}"; do
        if grep -q "def $func" "$PATH_UTILS_FILE"; then
            echo "   ✅ Função: $func"
        else
            echo "   ❌ Função AUSENTE: $func"
            FUNCOES_FALTANTES+=("$func")
        fi
    done

    # Verificar estratégia cache-first
    if grep -q "cache-first" "$PATH_UTILS_FILE" || grep -q "use_cache" "$PATH_UTILS_FILE"; then
        echo "   ✅ Estratégia cache-first implementada"
    else
        echo "   ⚠️  Estratégia cache-first não detectada (buscar 'use_cache' ou 'cache-first' nos comentários)"
    fi

    PATH_UTILS_OK=$((${#FUNCOES_FALTANTES[@]} == 0))
else
    echo "❌ $PATH_UTILS_FILE NÃO EXISTE"
    PATH_UTILS_OK=0
fi
echo ""

# 2. Estrutura de diretórios cache
echo "=== 2. ESTRUTURA DE DIRETÓRIOS CACHE ==="
DIRETORIOS_CACHE=(
    "$HOME/documentos-juridicos-cache"
    "$HOME/claude-code-data/outputs"
)

DIRETORIOS_OK=0
for dir in "${DIRETORIOS_CACHE[@]}"; do
    if [ -d "$dir" ]; then
        # Calcular tamanho do diretório
        SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
        COUNT=$(find "$dir" -type f 2>/dev/null | wc -l)
        echo "✅ $dir"
        echo "   Tamanho: $SIZE | Arquivos: $COUNT"
        DIRETORIOS_OK=$((DIRETORIOS_OK + 1))
    else
        echo "❌ $dir NÃO EXISTE"
    fi
done
echo ""

# 3. Agentes Python adaptados
echo "=== 3. AGENTES ADAPTADOS (imports path_utils) ==="
AGENTES_ADAPTADOS=0
AGENTES_TOTAL=0

for agente_dir in agentes/*/; do
    agente_name=$(basename "$agente_dir")

    # Verificar se é agente Python (tem main.py ou *.py)
    if [ -f "${agente_dir}main.py" ] || ls "${agente_dir}"*.py >/dev/null 2>&1; then
        AGENTES_TOTAL=$((AGENTES_TOTAL + 1))

        # Verificar imports de path_utils
        if grep -r "from shared.utils.path_utils import" "${agente_dir}"*.py 2>/dev/null | grep -q .; then
            echo "✅ $agente_name - usa path_utils"
            AGENTES_ADAPTADOS=$((AGENTES_ADAPTADOS + 1))

            # Listar funções importadas
            IMPORTS=$(grep -h "from shared.utils.path_utils import" "${agente_dir}"*.py 2>/dev/null | sed 's/.*import /   → /')
            echo "$IMPORTS"
        else
            echo "⚠️  $agente_name - NÃO usa path_utils ainda"
        fi
    fi
done

echo ""
echo "Agentes adaptados: $AGENTES_ADAPTADOS/$AGENTES_TOTAL"
echo ""

# 4. Servidor montado (OPCIONAL)
echo "=== 4. SERVIDOR CORPORATIVO (OPCIONAL) ==="
SERVIDOR_PATH="/mnt/servidor"

if [ -d "$SERVIDOR_PATH" ]; then
    # Verificar se está realmente montado (não é diretório vazio)
    if mountpoint -q "$SERVIDOR_PATH" 2>/dev/null || [ "$(ls -A $SERVIDOR_PATH 2>/dev/null)" ]; then
        SIZE=$(du -sh "$SERVIDOR_PATH" 2>/dev/null | cut -f1 || echo "N/A")
        echo "✅ $SERVIDOR_PATH está montado"
        echo "   Tamanho: $SIZE"
        SERVIDOR_OK=1
    else
        echo "⚠️  $SERVIDOR_PATH existe mas está vazio (não montado)"
        echo "   Modo: Offline (usando apenas cache local)"
        SERVIDOR_OK=0
    fi
else
    echo "ℹ️  $SERVIDOR_PATH não existe"
    echo "   Modo: Offline (usando apenas cache local)"
    echo "   Status: OK - Sprint 5 funciona sem servidor"
    SERVIDOR_OK=0
fi
echo ""

# 5. Verificar shared/ structure
echo "=== 5. SHARED/ STRUCTURE ==="
if [ -d "shared/utils" ]; then
    UTILS_COUNT=$(ls shared/utils/*.py 2>/dev/null | wc -l)
    echo "✅ shared/utils/ - $UTILS_COUNT arquivos Python"
    if [ $UTILS_COUNT -gt 0 ]; then
        ls shared/utils/*.py 2>/dev/null | xargs -n1 basename | sed 's/^/   - /'
    fi
else
    echo "❌ shared/utils/ NÃO EXISTE"
fi

if [ -d "shared/models" ]; then
    MODELS_COUNT=$(ls shared/models/*.py 2>/dev/null | wc -l)
    echo "✅ shared/models/ - $MODELS_COUNT arquivos Python"
else
    echo "⚠️  shared/models/ não existe"
fi
echo ""

# 6. Git Status
echo "=== 6. GIT STATUS ==="
git status --short | head -10
if [ -z "$(git status --short)" ]; then
    echo "✅ Working tree clean"
else
    echo "⚠️  Mudanças pendentes (ver acima)"
fi
echo ""

# 7. Resumo Final
echo "=========================================="
echo "RESUMO SPRINT 5"
echo "=========================================="
echo "path_utils.py: $([ $PATH_UTILS_OK -eq 1 ] && echo '✅' || echo '❌')"
echo "Diretórios cache: $DIRETORIOS_OK/${#DIRETORIOS_CACHE[@]}"
echo "Agentes adaptados: $AGENTES_ADAPTADOS/$AGENTES_TOTAL"
echo "Servidor montado: $([ $SERVIDOR_OK -eq 1 ] && echo '✅ (Online)' || echo 'ℹ️  (Offline - OK)')"
echo ""

# Determinar status Sprint 5
if [ $PATH_UTILS_OK -eq 1 ] && [ $DIRETORIOS_OK -ge 1 ] && [ $AGENTES_ADAPTADOS -ge 1 ]; then
    if [ $DIRETORIOS_OK -eq ${#DIRETORIOS_CACHE[@]} ] && [ $AGENTES_ADAPTADOS -eq $AGENTES_TOTAL ]; then
        echo "Status: ✅ SPRINT 5 COMPLETO"
    else
        echo "Status: ✅ SPRINT 5 FUNCIONAL (parcialmente completo)"
    fi
else
    echo "Status: ⚠️  SPRINT 5 PENDENTE"
    echo ""
    echo "Requisitos mínimos:"
    echo "  - path_utils.py com funções cache-first"
    echo "  - Pelo menos 1 diretório cache criado"
    echo "  - Pelo menos 1 agente adaptado"
fi
echo "=========================================="

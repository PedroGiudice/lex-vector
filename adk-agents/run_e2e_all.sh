#!/bin/bash
# Script para rodar testes E2E de todos os módulos do Legal Workbench

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  LEGAL WORKBENCH - E2E Test Suite"
echo "=========================================="
echo ""

# Verifica ambiente
if [ ! -f ".env" ]; then
    echo "ERROR: .env não encontrado"
    echo "Copie .env.example para .env e configure GOOGLE_API_KEY"
    exit 1
fi

# Ativa venv se existir
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
    echo "✓ Virtual env ativado"
fi

# Verifica dependências
python3 -c "import google.adk" 2>/dev/null || {
    echo "ERROR: google-adk não instalado"
    echo "Execute: pip install google-adk"
    exit 1
}

python3 -c "import mcp" 2>/dev/null || {
    echo "ERROR: mcp não instalado"
    echo "Execute: pip install mcp"
    exit 1
}

# Verifica se frontend está rodando
echo ""
echo "Verificando frontend..."
if curl -s http://localhost/app/ > /dev/null 2>&1; then
    echo "✓ Frontend acessível em http://localhost/app/"
else
    echo "⚠ Frontend NÃO está acessível em http://localhost/app/"
    echo "  Inicie o frontend antes de rodar os testes:"
    echo "  cd ../legal-workbench/docker && docker compose up -d"
    echo ""
    read -p "Continuar mesmo assim? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Limpa resultados anteriores
echo ""
echo "Limpando resultados anteriores..."
rm -f qa_commander/results/test_*.json
rm -f qa_commander/screenshots/*_$(date +%Y%m%d)*.png

# Roda o agente
echo ""
echo "=========================================="
echo "  Iniciando QA Commander"
echo "=========================================="
echo ""

timeout 600 python run_agent.py qa_commander --file prompts/e2e_all_modules.md --timeout 600

# Mostra resultados
echo ""
echo "=========================================="
echo "  Resultados"
echo "=========================================="
echo ""

if ls qa_commander/results/test_*.json 1> /dev/null 2>&1; then
    echo "Arquivos de resultado:"
    ls -la qa_commander/results/test_*.json
    echo ""
    echo "Conteúdo:"
    for f in qa_commander/results/test_*.json; do
        cat "$f"
        echo ""
    done
else
    echo "Nenhum resultado encontrado."
fi

echo ""
echo "Screenshots salvos em: qa_commander/screenshots/"
ls -la qa_commander/screenshots/ 2>/dev/null || echo "(nenhum screenshot)"

echo ""
echo "=========================================="
echo "  E2E Test Suite Finalizado"
echo "=========================================="

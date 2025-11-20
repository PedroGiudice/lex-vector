#!/bin/bash
# Setup script para jurisprudencia-collector (WSL2/Linux)

set -e  # Exit on error

echo "=== Setup: jurisprudencia-collector ==="
echo ""

# 1. Verificar Python
echo "1. Verificando Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale com: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION encontrado"
echo ""

# 2. Criar virtual environment
echo "2. Criando virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  .venv já existe - pulando criação"
else
    python3 -m venv .venv
    echo "✅ .venv criado"
fi
echo ""

# 3. Ativar venv e instalar dependências
echo "3. Instalando dependências..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Instalar requirements
pip install -r requirements.txt --quiet

echo "✅ Dependências instaladas"
echo ""

# 4. Criar diretórios de dados
echo "4. Criando diretórios..."
mkdir -p data/{downloads,logs,cache}
echo "✅ Diretórios criados"
echo ""

# 5. Executar testes (opcional)
echo "5. Executando testes..."
if pytest tests/ -v --tb=short; then
    echo "✅ Testes passaram"
else
    echo "⚠️  Alguns testes falharam (verifique acima)"
fi
echo ""

# 6. Resumo
echo "=== Setup Completo ==="
echo ""
echo "Para ativar o ambiente:"
echo "  source .venv/bin/activate"
echo ""
echo "Para executar exemplos:"
echo "  python exemplo_uso.py api        # Download via API"
echo "  python exemplo_uso.py caderno    # Download de caderno"
echo "  python exemplo_uso.py multiplos  # Múltiplos tribunais"
echo "  python exemplo_uso.py validar    # Validar comandos"
echo ""
echo "Para executar testes:"
echo "  pytest tests/ -v"
echo ""

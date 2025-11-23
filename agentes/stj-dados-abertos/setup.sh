#!/bin/bash
# Setup script para STJ Dados Abertos

set -e

echo "=========================================="
echo "STJ Dados Abertos - Setup"
echo "=========================================="
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "config.py" ]; then
    echo "❌ Erro: Execute este script no diretório stj-dados-abertos/"
    exit 1
fi

# Verificar Python
echo "1. Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"
echo ""

# Criar venv se não existir
if [ ! -d ".venv" ]; then
    echo "2. Criando virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment criado"
else
    echo "2. Virtual environment já existe"
fi
echo ""

# Ativar venv
echo "3. Ativando virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment ativado"
echo ""

# Atualizar pip
echo "4. Atualizando pip..."
pip install --upgrade pip --quiet
echo "✅ pip atualizado"
echo ""

# Instalar dependências
echo "5. Instalando dependências..."
pip install -r requirements.txt --quiet
echo "✅ Dependências instaladas"
echo ""

# Verificar instalação
echo "6. Verificando instalação..."
python3 -c "import duckdb; import typer; import httpx" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Módulos principais importados com sucesso"
else
    echo "❌ Erro ao importar módulos"
    exit 1
fi
echo ""

# Verificar HD externo
echo "7. Verificando HD externo..."
if [ -d "/mnt/e" ]; then
    echo "✅ HD externo acessível: /mnt/e"
else
    echo "⚠️  HD externo NÃO acessível: /mnt/e"
    echo "   Dados serão salvos localmente em: data_local/"
fi
echo ""

# Testar CLI
echo "8. Testando CLI..."
python3 cli.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ CLI funcionando"
else
    echo "❌ Erro na CLI"
    exit 1
fi
echo ""

# Criar diretórios de teste
echo "9. Criando estrutura de diretórios..."
mkdir -p tests
echo "✅ Diretórios criados"
echo ""

echo "=========================================="
echo "✅ Setup concluído com sucesso!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "  1. Ativar venv: source .venv/bin/activate"
echo "  2. Inicializar: python3 cli.py stj-init"
echo "  3. Ver ajuda: python3 cli.py --help"
echo "  4. Quick start: cat QUICK_START.md"
echo ""

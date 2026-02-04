#!/bin/bash
# Setup script para STJ Dados Abertos

set -e

echo "=========================================="
echo "STJ Dados Abertos - Setup"
echo "=========================================="
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "config.py" ]; then
    echo "[ERRO] Erro: Execute este script no diretório stj-dados-abertos/"
    exit 1
fi

# Verificar Python
echo "1. Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "[ERRO] Python 3 não encontrado"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "[OK] $PYTHON_VERSION"
echo ""

# Criar venv se não existir
if [ ! -d ".venv" ]; then
    echo "2. Criando virtual environment..."
    python3 -m venv .venv
    echo "[OK] Virtual environment criado"
else
    echo "2. Virtual environment já existe"
fi
echo ""

# Ativar venv
echo "3. Ativando virtual environment..."
source .venv/bin/activate
echo "[OK] Virtual environment ativado"
echo ""

# Atualizar pip
echo "4. Atualizando pip..."
pip install --upgrade pip --quiet
echo "[OK] pip atualizado"
echo ""

# Instalar dependências
echo "5. Instalando dependências..."
pip install -r requirements.txt --quiet
echo "[OK] Dependências instaladas"
echo ""

# Verificar instalação
echo "6. Verificando instalação..."
python3 -c "import duckdb; import typer; import httpx" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "[OK] Módulos principais importados com sucesso"
else
    echo "[ERRO] Erro ao importar módulos"
    exit 1
fi
echo ""

# Verificar diretorio de dados
echo "7. Verificando diretorio de dados..."
DATA_DIR="${DATA_PATH:-./data}"
mkdir -p "$DATA_DIR"
echo "[OK] Diretorio de dados: $DATA_DIR"
echo ""

# Testar CLI
echo "8. Testando CLI..."
python3 cli.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "[OK] CLI funcionando"
else
    echo "[ERRO] Erro na CLI"
    exit 1
fi
echo ""

# Criar diretórios de teste
echo "9. Criando estrutura de diretórios..."
mkdir -p tests
echo "[OK] Diretórios criados"
echo ""

echo "=========================================="
echo "[OK] Setup concluído com sucesso!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "  1. Ativar venv: source .venv/bin/activate"
echo "  2. Inicializar: python3 cli.py stj-init"
echo "  3. Ver ajuda: python3 cli.py --help"
echo "  4. Quick start: cat QUICK_START.md"
echo ""

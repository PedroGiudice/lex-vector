#!/bin/bash
# Script para executar o Legal Extractor CLI
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verifica se venv existe
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Ativa venv
source .venv/bin/activate

# Instala dependências se necessário
if ! python -c "import typer" 2>/dev/null; then
    echo "Instalando dependências..."
    pip install -e .
fi

# Executa CLI
python -m legal_extractor_cli.cli "$@"

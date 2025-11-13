#!/bin/bash

# MD2PDF Converter - Setup Script (Linux/Mac)
# Configura o ambiente e verifica dependências

echo "========================================"
echo "  MD2PDF CONVERTER - SETUP"
echo "========================================"
echo ""

# Cria estrutura de diretórios
echo "[1/4] Criando estrutura de diretórios..."
mkdir -p assets lib docs
echo "  - Estrutura criada"

# Verifica dependências
echo ""
echo "[2/4] Verificando dependências..."

if command -v curl &> /dev/null; then
    echo "  - curl: OK"
    DOWNLOADER="curl -sL -o"
elif command -v wget &> /dev/null; then
    echo "  - wget: OK"
    DOWNLOADER="wget -q -O"
else
    echo "  [AVISO] curl ou wget não encontrados"
    DOWNLOADER=""
fi

# Baixa bibliotecas (opcional)
if [ -n "$DOWNLOADER" ]; then
    echo "  - Baixando bibliotecas JavaScript..."

    if [ ! -f "lib/marked.min.js" ]; then
        echo "    - marked.js..."
        $DOWNLOADER lib/marked.min.js https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js
    fi

    if [ ! -f "lib/docx.min.js" ]; then
        echo "    - docx.js..."
        $DOWNLOADER lib/docx.min.js https://cdnjs.cloudflare.com/ajax/libs/docx/7.8.2/docx.min.js
    fi

    if [ ! -f "lib/FileSaver.min.js" ]; then
        echo "    - FileSaver.js..."
        $DOWNLOADER lib/FileSaver.min.js https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js
    fi

    echo "  - Bibliotecas instaladas"
fi

# Verifica arquivo principal
echo ""
echo "[3/4] Verificando arquivo principal..."
if [ ! -f "index.html" ]; then
    echo "  [AVISO] index.html não encontrado!"
    echo "  O arquivo index.html deve estar presente no diretório"
else
    echo "  - index.html encontrado"
    FILE_SIZE=$(du -h "index.html" | cut -f1)
    echo "    Tamanho: $FILE_SIZE"
fi

# Verifica Python
echo ""
echo "[4/4] Verificando servidor HTTP..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  - Python3 detectado: $PYTHON_VERSION"
    echo "  - Servidor disponível via: python3 -m http.server 8000"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo "  - Python detectado: $PYTHON_VERSION"
    echo "  - Servidor disponível via: python -m http.server 8000"
else
    echo "  [INFO] Python não detectado"
    echo "  Recomenda-se instalar Python para usar o servidor HTTP"
fi

# Torna server.py executável
if [ -f "server.py" ]; then
    chmod +x server.py
    echo "  - server.py configurado"
fi

# Torna este script executável
chmod +x "$0" 2>/dev/null

# Sumário
echo ""
echo "========================================"
echo "  CONFIGURAÇÃO CONCLUÍDA"
echo "========================================"
echo ""
echo "Para iniciar o servidor:"
echo "  1. Python:  python3 -m http.server 8000"
echo "  2. Script:  ./server.py"
echo ""
echo "Acesse: http://localhost:8000"
echo ""
echo "Funcionalidades disponíveis:"
echo "  - 14 opções de fontes profissionais"
echo "  - Controles avançados de formatação"
echo "  - Exportação para PDF"
echo "  - Exportação para DOCX"
echo ""

#!/bin/bash
#
# Exemplo de uso do Step 02: Vision Pipeline
#
# Processa páginas RASTER_NEEDED usando OpenCV
#

set -e  # Aborta em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Step 02: Vision Pipeline (O Saneador)${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Diretório do projeto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Verificar venv
if [ ! -d ".venv" ]; then
    echo -e "${RED}Erro: Virtual environment não encontrado${NC}"
    echo "Crie com: python -m venv .venv"
    exit 1
fi

# Ativar venv
source .venv/bin/activate

# Verificar dependências
echo -e "${YELLOW}[1/5] Verificando dependências...${NC}"

if ! python -c "import pdf2image" 2>/dev/null; then
    echo -e "${RED}Erro: pdf2image não instalado${NC}"
    echo "Instale com: pip install -r requirements.txt"
    exit 1
fi

if ! python -c "import cv2" 2>/dev/null; then
    echo -e "${RED}Erro: opencv-python-headless não instalado${NC}"
    echo "Instale com: pip install -r requirements.txt"
    exit 1
fi

if ! command -v pdftoppm &> /dev/null; then
    echo -e "${RED}Erro: Poppler não instalado${NC}"
    echo "Instale com: sudo apt install poppler-utils"
    exit 1
fi

echo -e "${GREEN}✓ Todas as dependências instaladas${NC}"
echo ""

# Parâmetros
DOC_ID="${1:-exemplo_scan}"
LAYOUT_JSON="${2:-outputs/$DOC_ID/layout.json}"
PDF_PATH="${3:-test-documents/exemplo_scan.pdf}"

# Validar inputs
echo -e "${YELLOW}[2/5] Validando inputs...${NC}"

if [ ! -f "$LAYOUT_JSON" ]; then
    echo -e "${RED}Erro: Layout não encontrado: $LAYOUT_JSON${NC}"
    echo ""
    echo "Execute primeiro o Step 01:"
    echo "  python src/steps/step_01_layout.py $PDF_PATH --doc-id $DOC_ID"
    exit 1
fi

if [ ! -f "$PDF_PATH" ]; then
    echo -e "${RED}Erro: PDF não encontrado: $PDF_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Inputs validados${NC}"
echo "  - Layout: $LAYOUT_JSON"
echo "  - PDF:    $PDF_PATH"
echo "  - Doc ID: $DOC_ID"
echo ""

# Verificar páginas RASTER_NEEDED
echo -e "${YELLOW}[3/5] Analisando layout...${NC}"

RASTER_COUNT=$(python -c "
import json
with open('$LAYOUT_JSON') as f:
    data = json.load(f)
    count = sum(1 for p in data.get('pages', []) if p.get('type') == 'RASTER_NEEDED')
    print(count)
")

if [ "$RASTER_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}⚠ Nenhuma página RASTER_NEEDED encontrada${NC}"
    echo "  Todas as páginas são NATIVE (texto extraível)"
    echo "  Step 02 não é necessário para este documento"
    exit 0
fi

echo -e "${GREEN}✓ $RASTER_COUNT página(s) RASTER_NEEDED detectada(s)${NC}"
echo ""

# Processar
echo -e "${YELLOW}[4/5] Processando imagens...${NC}"
echo ""

python src/steps/step_02_vision.py \
    "$LAYOUT_JSON" \
    "$PDF_PATH" \
    --doc-id "$DOC_ID" \
    --verbose

echo ""

# Verificar output
echo -e "${YELLOW}[5/5] Verificando output...${NC}"

IMAGES_DIR="outputs/$DOC_ID/images"

if [ ! -d "$IMAGES_DIR" ]; then
    echo -e "${RED}Erro: Diretório de imagens não criado${NC}"
    exit 1
fi

IMAGE_COUNT=$(ls -1 "$IMAGES_DIR"/*.png 2>/dev/null | wc -l)

echo -e "${GREEN}✓ $IMAGE_COUNT imagem(s) gerada(s)${NC}"
echo "  Localização: $IMAGES_DIR"
echo ""

# Listar imagens
if [ "$IMAGE_COUNT" -gt "0" ]; then
    echo "Imagens processadas:"
    ls -lh "$IMAGES_DIR"/*.png
    echo ""
fi

# Próximos passos
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PROCESSAMENTO CONCLUÍDO${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Próximos passos:"
echo "  1. Inspecionar imagens: ls $IMAGES_DIR/"
echo "  2. Executar Step 03 (OCR):"
echo "     python src/steps/step_03_extract.py \\"
echo "         $LAYOUT_JSON \\"
echo "         $IMAGES_DIR/ \\"
echo "         --doc-id $DOC_ID"
echo ""

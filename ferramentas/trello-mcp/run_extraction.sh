#!/bin/bash
#
# Trello Data Extraction Runner
#
# Easy-to-use script for extracting litigation data from Trello without Claude.
# Handles environment setup and provides clear instructions.
#
# Usage:
#   ./run_extraction.sh                          # Interactive mode
#   ./run_extraction.sh "Board Name"             # Direct extraction
#   ./run_extraction.sh "Board Name" "List Name" # Filter by list

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Trello Data Extraction - Standalone Runner          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================

echo -e "${YELLOW}[1/5]${NC} Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
echo -e "${GREEN}  ✓${NC} Python $PYTHON_VERSION found"

# Check uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}  ! uv not found. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo -e "${GREEN}  ✓${NC} uv package manager ready"

# ============================================================================
# Step 2: Check Environment Variables
# ============================================================================

echo -e "${YELLOW}[2/5]${NC} Checking Trello credentials..."

if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file not found!${NC}"
    echo ""
    echo "To create .env file:"
    echo "  1. Copy template: cp .env.example .env"
    echo "  2. Get API credentials from: https://trello.com/power-ups/admin"
    echo "  3. Edit .env and add your TRELLO_API_KEY and TRELLO_API_TOKEN"
    echo ""
    exit 1
fi

# Source .env and check
source .env

if [ -z "$TRELLO_API_KEY" ] || [ -z "$TRELLO_API_TOKEN" ]; then
    echo -e "${RED}✗ TRELLO_API_KEY or TRELLO_API_TOKEN not set in .env${NC}"
    echo ""
    echo "Edit .env file and add:"
    echo "  TRELLO_API_KEY=your_key_here"
    echo "  TRELLO_API_TOKEN=your_token_here"
    echo ""
    echo "Get credentials from: https://trello.com/power-ups/admin"
    exit 1
fi

echo -e "${GREEN}  ✓${NC} Trello credentials found"

# ============================================================================
# Step 3: Install Dependencies
# ============================================================================

echo -e "${YELLOW}[3/5]${NC} Installing dependencies..."

if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}  ! Creating virtual environment...${NC}"
    uv venv
fi

# Install dependencies
uv sync --quiet

echo -e "${GREEN}  ✓${NC} Dependencies installed"

# ============================================================================
# Step 4: Get Board Information (Interactive or Direct)
# ============================================================================

if [ $# -eq 0 ]; then
    # Interactive mode
    echo -e "${YELLOW}[4/5]${NC} Discovering available boards..."
    echo ""

    # List boards
    PYTHONPATH=src uv run python -c "
import asyncio
import sys
from models import EnvironmentSettings
from trello_client import TrelloClient

async def list_boards():
    settings = EnvironmentSettings()
    async with TrelloClient(settings) as client:
        await client.validate_credentials()
        boards = await client.get_all_boards()

        print('Available boards:')
        for i, board in enumerate(boards, 1):
            status = '🟢 Open' if not board.closed else '🔴 Closed'
            print(f'  {i}. {board.name} ({status})')

        return boards

boards = asyncio.run(list_boards())
    " 2>/dev/null

    echo ""
    read -p "Enter board name to extract from: " BOARD_NAME

    echo ""
    read -p "Filter by list name? (press Enter to skip): " LIST_NAME

else
    # Direct mode
    BOARD_NAME="$1"
    LIST_NAME="${2:-}"
fi

# ============================================================================
# Step 5: Run Extraction
# ============================================================================

echo ""
echo -e "${YELLOW}[5/5]${NC} Running extraction..."
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Build command
CMD="PYTHONPATH=src uv run python examples/extract_litigation_data.py \"$BOARD_NAME\""

if [ -n "$LIST_NAME" ]; then
    CMD="$CMD --list \"$LIST_NAME\""
fi

# Run extraction
eval $CMD

# ============================================================================
# Success Summary
# ============================================================================

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Extraction complete!${NC}"
echo ""
echo "Output files:"
echo "  - output/litigation_dataset_clean.json (valid records)"
echo "  - output/litigation_dataset_errors.json (errors, if any)"
echo ""
echo "Next steps:"
echo "  1. Review output files in the output/ directory"
echo "  2. Process clean data for your use case"
echo "  3. Fix errors in Trello cards if needed"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

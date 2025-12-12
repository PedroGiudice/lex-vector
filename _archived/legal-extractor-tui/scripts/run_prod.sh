#!/bin/bash
#
# Production runner for TUI Template
# Launches app in production mode (no dev tools)
#

set -e

cd "$(dirname "$0")/.."

echo "=== TUI Template Production Runner ==="
echo ""

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv .venv"
    exit 1
fi

echo "🔧 Activating virtual environment..."
source .venv/bin/activate

echo "📦 Installing dependencies..."
pip install -e . --break-system-packages 2>/dev/null || pip install -e .

echo ""
echo "🚀 Launching TUI..."
echo ""

# Run normally (no --dev flag)
python -m tui_app

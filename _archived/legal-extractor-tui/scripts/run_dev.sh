#!/bin/bash
#
# Development runner for TUI Template
# Activates venv, installs dependencies, and launches with Textual dev mode
#

set -e  # Exit on error

# Navigate to project root
cd "$(dirname "$0")/.."

echo "=== TUI Template Dev Runner ==="
echo ""

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run: python3 -m venv .venv"
    exit 1
fi

# Activate venv
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install in editable mode with dev dependencies
echo "📦 Installing dependencies..."
pip install -e ".[dev]" --break-system-packages 2>/dev/null || pip install -e ".[dev]"

echo ""
echo "🚀 Launching TUI in dev mode..."
echo "   (Textual DevTools will be available)"
echo ""

# Run with Textual dev mode
textual run --dev src/legal_extractor_tui/app.py:LegalExtractorApp

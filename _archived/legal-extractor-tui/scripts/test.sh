#!/bin/bash
#
# Test runner for TUI Template
# Runs pytest with coverage and verbose output
#

set -e

cd "$(dirname "$0")/.."

echo "=== TUI Template Test Runner ==="
echo ""

if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    exit 1
fi

source .venv/bin/activate

echo "📦 Installing test dependencies..."
pip install -e ".[dev]" --break-system-packages 2>/dev/null || pip install -e ".[dev]"

echo ""
echo "🧪 Running tests..."
echo ""

# Run pytest with coverage
pytest tests/ \
    --verbose \
    --cov=src/tui_app \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"

echo ""
echo "✅ Tests complete!"
echo "📊 Coverage report: htmlcov/index.html"

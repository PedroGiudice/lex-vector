#!/bin/bash
#
# Quick launcher for Legal Extractor TUI
# Usage: ./run.sh [--dev]
#

cd "$(dirname "$0")"

# Activate venv
source .venv/bin/activate 2>/dev/null || {
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]" -q
}

# Check for dev flag
if [ "$1" == "--dev" ]; then
    echo "Starting Legal Extractor TUI (dev mode)..."
    textual run --dev src/legal_extractor_tui/app.py:LegalExtractorApp
else
    echo "Starting Legal Extractor TUI..."
    python -m legal_extractor_tui
fi

#!/bin/bash
# Setup script for ADK agents

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== ADK Agents Setup ==="

# 1. Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# 2. Activate venv
source .venv/bin/activate

# 3. Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# 4. Check for .env
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Creating from template..."
    cp .env.example .env
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo "   Get one at: https://aistudio.google.com/apikey"
    echo ""
fi

# 5. Verify API key
if grep -q "your_gemini_api_key_here" .env 2>/dev/null; then
    echo "❌ API key not configured in .env"
    echo "   Edit adk-agents/.env and replace 'your_gemini_api_key_here' with your actual key"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run Frontend Commander:"
echo "  source .venv/bin/activate"
echo "  python -m frontend-commander.watcher --once"
echo ""

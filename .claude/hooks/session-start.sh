#!/bin/bash
set -euo pipefail

# Only run in Claude Code on the web (remote environment)
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "🔧 Setting up Python environment for Claude-Code-Projetos (web)..."

# Install root-level dependencies
if [ -f "$CLAUDE_PROJECT_DIR/requirements.txt" ]; then
  echo "📦 Installing root dependencies..."
  pip install --user --quiet -r "$CLAUDE_PROJECT_DIR/requirements.txt" || true
fi

# Install oab-watcher agent dependencies (includes pytest)
if [ -f "$CLAUDE_PROJECT_DIR/agentes/oab-watcher/requirements.txt" ]; then
  echo "📦 Installing oab-watcher dependencies (includes pytest)..."
  pip install --user --quiet -r "$CLAUDE_PROJECT_DIR/agentes/oab-watcher/requirements.txt" || true
  # Install pytest-cov for coverage support
  pip install --user --quiet pytest-cov || true
fi

# Install legal-rag dependencies (includes mypy for linting)
if [ -f "$CLAUDE_PROJECT_DIR/agentes/legal-rag/requirements.txt" ]; then
  echo "📦 Installing legal-rag dependencies (includes mypy)..."
  pip install --user --quiet -r "$CLAUDE_PROJECT_DIR/agentes/legal-rag/requirements.txt" || true
fi

# Install type stubs for mypy
echo "📦 Installing type stubs for mypy..."
pip install --user --quiet types-requests types-tqdm || true

# Set PYTHONPATH to include project root for imports
echo "export PYTHONPATH=\"$CLAUDE_PROJECT_DIR:\${PYTHONPATH:-}\"" >> "$CLAUDE_ENV_FILE"

echo "✅ Python environment setup complete!"
echo "   - Root dependencies installed"
echo "   - pytest available for testing"
echo "   - mypy available for linting"
echo "   - PYTHONPATH configured"

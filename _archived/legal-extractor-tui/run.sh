#!/bin/bash
#
# Quick launcher for Legal Extractor TUI
# Usage: ./run.sh [--dev] [--theme THEME] [--help]
#
# Options:
#   --dev       Enable development mode with Textual DevTools (hot CSS reload)
#   --theme     Set theme: neon (default), matrix, synthwave, dark
#   --help      Show this help message
#
set -e  # Exit on error

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Force true color support (24-bit) for proper theme rendering
# Without this, dark colors (#0d0d0d) appear blue in 256-color terminals
export COLORTERM=truecolor

# Complete terminal reset sequence (matches tui_safety.py)
TERMINAL_RESET_SEQ='\x1b[?9l\x1b[?1000l\x1b[?1001l\x1b[?1002l\x1b[?1003l\x1b[?1004l\x1b[?1005l\x1b[?1006l\x1b[?1015l\x1b[?1016l\x1b[?47l\x1b[?1047l\x1b[?1049l\x1b[?2004l\x1b[?2048l\x1b[?25h\x1b[?7h\x1b>\x1b(B\x1b[>0u\x1b[0m'

# Cleanup function - reset terminal completely
cleanup() {
    printf "$TERMINAL_RESET_SEQ"
}

# Show help message
show_help() {
    echo "Legal Extractor TUI - Extract text from Brazilian legal PDFs"
    echo ""
    echo "Usage: ./run.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dev           Enable development mode with Textual DevTools"
    echo "                  (hot CSS reload, DOM inspector)"
    echo "  --theme THEME   Set color theme:"
    echo "                    neon      - Dracula/Cyberpunk (default)"
    echo "                    matrix    - Matrix green"
    echo "                    synthwave - Pink/purple synthwave"
    echo "                    dark      - Minimal dark"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run.sh                    # Start with default theme"
    echo "  ./run.sh --theme matrix     # Start with Matrix theme"
    echo "  ./run.sh --dev              # Start in dev mode"
    echo "  ./run.sh --dev --theme dark # Dev mode with dark theme"
}

# Register cleanup on ALL exit scenarios
trap cleanup EXIT INT TERM QUIT HUP

# Parse arguments
DEV_MODE=""
THEME_NAME=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dev)
            DEV_MODE="1"
            shift
            ;;
        --theme)
            shift
            if [[ -z "$1" || "$1" == --* ]]; then
                echo "ERROR: --theme requires a value"
                echo "Valid themes: neon, matrix, synthwave, dark"
                exit 1
            fi
            THEME_NAME="$1"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Activate venv (create if missing)
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate 2>/dev/null || {
    echo "ERROR: Failed to activate virtual environment"
    exit 1
}

# Install/update if needed (check if package is installed)
if ! python -c "import legal_extractor_tui" 2>/dev/null; then
    echo "Installing Legal Extractor TUI..."
    pip install -e ".[dev]" -q
fi

# CRITICAL: Clear Python bytecode cache to prevent stale code execution
# This fixes DuplicateIds and other bugs that persist after code fixes
# See: skills/tui-core/bug-patterns.md (BUG 9, BUG 10)
find "$SCRIPT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Build command arguments
THEME_ARG=""
if [[ -n "$THEME_NAME" ]]; then
    THEME_ARG="--theme $THEME_NAME"
fi

# Run application
if [[ -n "$DEV_MODE" ]]; then
    echo "Starting Legal Extractor TUI (dev mode with hot-reload)..."
    # Use module path for textual run (enables hot CSS reload)
    # Note: textual run --dev doesn't pass args to app, so theme is ignored in dev mode
    textual run --dev legal_extractor_tui.app:LegalExtractorApp
else
    echo "Starting Legal Extractor TUI..."
    # shellcheck disable=SC2086
    python -m legal_extractor_tui $THEME_ARG
fi

# Cleanup is automatically called by trap on exit

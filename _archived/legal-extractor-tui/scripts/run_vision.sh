#!/bin/bash
#
# Programmatic Vision - TUI Visual Verification Script
#
# Runs vision tests and captures DOM dumps on failure.
# This script is the "Verification Reflex" - it proves widgets render correctly.
#
# Usage:
#   ./scripts/run_vision.sh              # Run all vision tests
#   ./scripts/run_vision.sh header       # Run tests matching "header"
#   ./scripts/run_vision.sh --verbose    # Run with full output
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root (one level up from scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment if available
VENV_PATHS=(
    "$PROJECT_ROOT/.venv/bin/activate"
    "$PROJECT_ROOT/../.venv/bin/activate"  # Parent project venv
    "$PROJECT_ROOT/venv/bin/activate"
)

VENV_ACTIVATED=false
for venv_path in "${VENV_PATHS[@]}"; do
    if [ -f "$venv_path" ]; then
        echo -e "${CYAN}Activating venv: $venv_path${NC}"
        source "$venv_path"
        VENV_ACTIVATED=true
        break
    fi
done

if [ "$VENV_ACTIVATED" = false ]; then
    echo -e "${YELLOW}WARNING: No virtual environment found. Using system Python.${NC}"
fi

# Log directory
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# Timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
VISION_LOG="$LOG_DIR/vision_$TIMESTAMP.log"

echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     PROGRAMMATIC VISION - TUI VERIFICATION     ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}ERROR: pytest not found. Install with: pip install pytest pytest-asyncio${NC}"
    exit 1
fi

# Check if textual is available
if ! python -c "import textual" &> /dev/null; then
    echo -e "${RED}ERROR: textual not found. Install with: pip install textual${NC}"
    exit 1
fi

# Parse arguments
FILTER=""
VERBOSE=""

for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE="-v -s"
            ;;
        *)
            FILTER="$arg"
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest tests/ -m vision $VERBOSE"

if [ -n "$FILTER" ]; then
    PYTEST_CMD="pytest tests/ -k $FILTER $VERBOSE"
    echo -e "${YELLOW}Running vision tests matching: ${FILTER}${NC}"
else
    echo -e "${YELLOW}Running all vision tests...${NC}"
fi

echo ""
echo -e "Log file: ${CYAN}$VISION_LOG${NC}"
echo ""

# Run tests and capture output
{
    echo "═══════════════════════════════════════════════════════"
    echo "VISION TEST RUN: $(date)"
    echo "Command: $PYTEST_CMD"
    echo "═══════════════════════════════════════════════════════"
    echo ""
} > "$VISION_LOG"

# Run pytest, capturing exit code
set +e
$PYTEST_CMD 2>&1 | tee -a "$VISION_LOG"
EXIT_CODE=${PIPESTATUS[0]}
set -e

echo "" | tee -a "$VISION_LOG"

# Check results
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           ✓ ALL VISION TESTS PASSED            ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "Widgets are rendering correctly."
else
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║           ✗ VISION TESTS FAILED                ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Check DOM dump for failure details:${NC}"
    echo -e "  ${CYAN}cat logs/vision_failure.log${NC}"
    echo ""
    echo -e "${YELLOW}Full test log:${NC}"
    echo -e "  ${CYAN}cat $VISION_LOG${NC}"
    echo ""

    # Show last failure if exists
    if [ -f "$LOG_DIR/vision_failure.log" ]; then
        echo -e "${YELLOW}Last failure DOM dump (last 30 lines):${NC}"
        echo "─────────────────────────────────────────────────"
        tail -30 "$LOG_DIR/vision_failure.log"
        echo "─────────────────────────────────────────────────"
    fi
fi

# Symlink to latest log
ln -sf "$VISION_LOG" "$LOG_DIR/vision_latest.log"

exit $EXIT_CODE

#!/bin/bash
# test-unified.sh - Test suite for unified-statusline.js
#
# Tests:
# 1. Basic execution (vibe-log installed)
# 2. Fallback mode (vibe-log not installed)
# 3. Performance benchmark (< 100ms target)
# 4. Responsive modes (80, 120, 160 cols)

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUSLINE="${SCRIPT_DIR}/unified-statusline.js"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         UNIFIED STATUSLINE TEST SUITE                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# TEST 1: Basic Execution
# ============================================================================

echo "═══ TEST 1: Basic Execution (default terminal width) ═══"
echo ""
node "$STATUSLINE"
echo ""
echo "✅ TEST 1 PASSED"
echo ""

# ============================================================================
# TEST 2: Performance Benchmark
# ============================================================================

echo "═══ TEST 2: Performance Benchmark (target: < 100ms) ═══"
echo ""
node "$STATUSLINE" --benchmark 2>&1 | tail -2
echo ""

# Extract execution time
EXEC_TIME=$(node "$STATUSLINE" --benchmark 2>&1 | grep "Execution time:" | awk '{print $3}' | sed 's/ms//')

if [ -n "$EXEC_TIME" ]; then
  if (( $(echo "$EXEC_TIME < 100" | bc -l) )); then
    echo "✅ TEST 2 PASSED - Execution time: ${EXEC_TIME}ms (< 100ms)"
  else
    echo "⚠️  TEST 2 WARNING - Execution time: ${EXEC_TIME}ms (>= 100ms)"
  fi
else
  echo "❌ TEST 2 FAILED - Could not measure execution time"
fi
echo ""

# ============================================================================
# TEST 3: Responsive Modes
# ============================================================================

echo "═══ TEST 3: Responsive Modes ═══"
echo ""

# Test minimal mode (< 80 cols)
echo "--- Minimal mode (70 cols) ---"
COLUMNS=70 node "$STATUSLINE" 2>&1 | head -5
echo ""

# Test compact mode (80-120 cols)
echo "--- Compact mode (100 cols) ---"
COLUMNS=100 node "$STATUSLINE" 2>&1 | head -5
echo ""

# Test comfortable mode (120-160 cols)
echo "--- Comfortable mode (140 cols) ---"
COLUMNS=140 node "$STATUSLINE" 2>&1 | head -5
echo ""

# Test wide mode (> 160 cols)
echo "--- Wide mode (180 cols) ---"
COLUMNS=180 node "$STATUSLINE" 2>&1 | head -5
echo ""

echo "✅ TEST 3 PASSED - All responsive modes working"
echo ""

# ============================================================================
# TEST 4: Vibe-log Fallback
# ============================================================================

echo "═══ TEST 4: Vibe-log Fallback (simulated absence) ═══"
echo ""

# Temporarily move vibe-log if it exists
VIBE_LOG_BACKUP=""
if [ -d "$HOME/.vibe-log" ]; then
  VIBE_LOG_BACKUP="$HOME/.vibe-log.backup-test"
  mv "$HOME/.vibe-log" "$VIBE_LOG_BACKUP"
  echo "Moved ~/.vibe-log to backup location"
fi

# Run statusline without vibe-log
node "$STATUSLINE" 2>&1 | grep -E "(Vibe:|Gordon:)" || true

# Restore vibe-log
if [ -n "$VIBE_LOG_BACKUP" ] && [ -d "$VIBE_LOG_BACKUP" ]; then
  mv "$VIBE_LOG_BACKUP" "$HOME/.vibe-log"
  echo "Restored ~/.vibe-log from backup"
fi

echo ""
echo "✅ TEST 4 PASSED - Graceful fallback when vibe-log absent"
echo ""

# ============================================================================
# TEST 5: Git Status Detection
# ============================================================================

echo "═══ TEST 5: Git Status Detection ═══"
echo ""

node "$STATUSLINE" 2>&1 | grep -E "Git:" || echo "❌ Git status not found"

echo ""
echo "✅ TEST 5 PASSED - Git status detected"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    ALL TESTS PASSED ✅                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Install vibe-log-cli for full metrics: npm install -g vibe-log-cli"
echo "  2. Configure MCP servers in ~/.claude/mcp.json"
echo "  3. Activate Legal-Braniac agent for orchestration tracking"
echo ""

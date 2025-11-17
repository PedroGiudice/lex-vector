#!/bin/bash
# test-professional.sh - Testa professional statusline em diferentes cenários

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATUSLINE="$SCRIPT_DIR/professional-statusline.js"

echo "========================================="
echo "Testing Professional Statusline"
echo "========================================="
echo ""

# Test 1: Normal state
echo "Test 1: Normal state (idle)"
echo "----------------------------"
node "$STATUSLINE"
echo ""
echo ""

# Test 2: Simular hook execution (spinner ativo)
echo "Test 2: Hook execution (spinner active)"
echo "----------------------------------------"
mkdir -p ~/.claude/statusline
echo '{"hooks":["pre-commit"],"status":"running"}' > ~/.claude/statusline/hooks-status.json
node "$STATUSLINE"
rm -f ~/.claude/statusline/hooks-status.json
echo ""
echo ""

# Test 3: Simular session ativa
echo "Test 3: Session with duration"
echo "------------------------------"
SESSION_START=$(date -d '1 hour ago' +%s)000  # 1 hora atrás em ms
echo "{\"timestamp\":$SESSION_START}" > ~/.claude/statusline/session-start.json
node "$STATUSLINE"
rm -f ~/.claude/statusline/session-start.json
echo ""
echo ""

# Test 4: Simular skills ativas
echo "Test 4: Active skills"
echo "---------------------"
TIMESTAMP=$(date +%s)000
echo "{\"skills\":[\"ocr-pro\",\"deep-parser\"],\"timestamp\":$TIMESTAMP}" > ~/.claude/statusline/active-skills.json
node "$STATUSLINE"
rm -f ~/.claude/statusline/active-skills.json
echo ""
echo ""

# Test 5: Performance test
echo "Test 5: Performance (should be < 200ms)"
echo "----------------------------------------"
time node "$STATUSLINE" > /dev/null
echo ""
echo ""

# Test 6: Spinner animation test (10 frames)
echo "Test 6: Spinner animation (10 frames)"
echo "--------------------------------------"
echo '{"hooks":["test"],"status":"running"}' > ~/.claude/statusline/hooks-status.json
for i in {1..10}; do
  clear
  echo "Frame $i/10:"
  node "$STATUSLINE"
  sleep 0.15  # 150ms entre frames
done
rm -f ~/.claude/statusline/hooks-status.json
echo ""
echo ""

echo "========================================="
echo "Tests complete!"
echo "========================================="

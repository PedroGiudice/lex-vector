#!/bin/bash
# test-pretool-simple.sh - Teste simplificado do PreToolUse hook

set -euo pipefail

HOOK=".claude/hooks/inject-tools-to-agents.js"

echo "=== Testing inject-tools-to-agents.js ==="
echo ""

# Test 1: Plan agent (should inject WebFetch)
echo -n "Test 1 (Plan agent): "
OUTPUT=$(echo '{"tool_name":"Task","tool_input":{"subagent_type":"Plan","prompt":"Test"},"hook_event_name":"PreToolUse"}' | bun run $HOOK)
if echo "$OUTPUT" | grep -q "WebFetch"; then
  echo "✓ PASS (WebFetch injected)"
else
  echo "✗ FAIL (WebFetch not found)"
  echo "Output: $OUTPUT"
  exit 1
fi

# Test 2: Bash tool (should pass through)
echo -n "Test 2 (Bash tool): "
OUTPUT=$(echo '{"tool_name":"Bash","tool_input":{"command":"ls"},"hook_event_name":"PreToolUse"}' | bun run $HOOK)
if [ "$OUTPUT" = "{}" ]; then
  echo "✓ PASS (passed through)"
else
  echo "✗ FAIL (unexpected output)"
  echo "Output: $OUTPUT"
  exit 1
fi

# Test 3: Unknown agent (should pass through)
echo -n "Test 3 (Unknown agent): "
OUTPUT=$(echo '{"tool_name":"Task","tool_input":{"subagent_type":"unknown","prompt":"Test"},"hook_event_name":"PreToolUse"}' | bun run $HOOK)
if [ "$OUTPUT" = "{}" ]; then
  echo "✓ PASS (passed through)"
else
  echo "✗ FAIL (unexpected output)"
  echo "Output: $OUTPUT"
  exit 1
fi

# Test 4: desenvolvimento agent (should inject multiple tools)
echo -n "Test 4 (desenvolvimento agent): "
OUTPUT=$(echo '{"tool_name":"Task","tool_input":{"subagent_type":"desenvolvimento","prompt":"Code"},"hook_event_name":"PreToolUse"}' | bun run $HOOK)
if echo "$OUTPUT" | grep -q "Read, Write, Edit"; then
  echo "✓ PASS (multiple tools injected)"
else
  echo "✗ FAIL (tools not found)"
  echo "Output: $OUTPUT"
  exit 1
fi

# Test 5: claude-code-guide (with critical_instruction)
echo -n "Test 5 (critical instruction): "
OUTPUT=$(echo '{"tool_name":"Task","tool_input":{"subagent_type":"claude-code-guide","prompt":"Help"},"hook_event_name":"PreToolUse"}' | bun run $HOOK)
if echo "$OUTPUT" | grep -q "MUST use WebFetch"; then
  echo "✓ PASS (critical instruction injected)"
else
  echo "✗ FAIL (instruction not found)"
  echo "Output: $OUTPUT"
  exit 1
fi

echo ""
echo "=== All tests passed! ===="
echo "Hook is ready to be added to settings.json"

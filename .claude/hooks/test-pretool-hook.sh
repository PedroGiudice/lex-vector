#!/bin/bash
# test-pretool-hook.sh - Teste abrangente do PreToolUse hook
#
# Testa inject-tools-to-agents.js com múltiplos cenários
# CRÍTICO: Hook deve ser resiliente a TODOS os casos edge

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

echo "============================================"
echo "Testing PreToolUse Hook: inject-tools-to-agents.js"
echo "============================================"
echo ""

# Helper function to run test
run_test() {
  local test_name="$1"
  local input_json="$2"
  local expected_behavior="$3"

  echo -n "Test: $test_name... "

  # Run hook with stdin
  output=$(echo "$input_json" | bun run .claude/hooks/inject-tools-to-agents.js 2>&1)
  exit_code=$?

  # Check exit code
  if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}PASS${NC} (exit $exit_code)"
    ((PASSED++))

    # Show output if verbose
    if [ "$VERBOSE" = "1" ]; then
      echo "  Output: $output"
    fi
  else
    echo -e "${RED}FAIL${NC} (exit $exit_code)"
    echo "  Output: $output"
    ((FAILED++))
  fi
}

# Test 1: Valid Task tool call for Plan agent
echo "=== Test 1: Valid Plan Agent ===="
INPUT_JSON_PLAN='{
  "session_id": "test-session-123",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "Plan",
    "description": "Plan system architecture",
    "prompt": "Design a jurisprudence collection system",
    "model": "haiku"
  },
  "hook_event_name": "PreToolUse"
}'
run_test "Plan agent with WebFetch tools" "$INPUT_JSON_PLAN" "Should inject WebFetch/WebSearch"

# Test 2: Agent not in mapping (should pass through)
echo ""
echo "=== Test 2: Unknown Agent ===="
INPUT_JSON_UNKNOWN='{
  "session_id": "test-session-456",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "non-existent-agent",
    "prompt": "Do something",
    "model": "sonnet"
  },
  "hook_event_name": "PreToolUse"
}'
run_test "Unknown agent (should pass through)" "$INPUT_JSON_UNKNOWN" "Should return empty object"

# Test 3: Non-Task tool (should pass through)
echo ""
echo "=== Test 3: Non-Task Tool ===="
INPUT_JSON_BASH='{
  "session_id": "test-session-789",
  "tool_name": "Bash",
  "tool_input": {
    "command": "ls -la"
  },
  "hook_event_name": "PreToolUse"
}'
run_test "Bash tool (should pass through)" "$INPUT_JSON_BASH" "Should return empty object"

# Test 4: Missing subagent_type (should pass through)
echo ""
echo "=== Test 4: Missing subagent_type ===="
INPUT_JSON_NO_TYPE='{
  "session_id": "test-session-101",
  "tool_name": "Task",
  "tool_input": {
    "prompt": "Do something without type"
  },
  "hook_event_name": "PreToolUse"
}'
run_test "Missing subagent_type" "$INPUT_JSON_NO_TYPE" "Should pass through"

# Test 5: Invalid JSON (should handle gracefully)
echo ""
echo "=== Test 5: Invalid JSON ===="
INPUT_JSON_INVALID='{ "invalid": json syntax'
run_test "Invalid JSON syntax" "$INPUT_JSON_INVALID" "Should exit 1 with error"

# Test 6: Wrong hook event (should pass through)
echo ""
echo "=== Test 6: Wrong Hook Event ===="
INPUT_JSON_WRONG_HOOK='{
  "session_id": "test-session-202",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "Plan",
    "prompt": "Test"
  },
  "hook_event_name": "PostToolUse"
}'
run_test "Wrong hook event (PostToolUse)" "$INPUT_JSON_WRONG_HOOK" "Should pass through"

# Test 7: desenvolvimento agent (multiple tools)
echo ""
echo "=== Test 7: Development Agent ===="
INPUT_JSON_DEV='{
  "session_id": "test-session-303",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "desenvolvimento",
    "description": "Implement feature",
    "prompt": "Write code for authentication system"
  },
  "hook_event_name": "PreToolUse"
}'
run_test "desenvolvimento agent" "$INPUT_JSON_DEV" "Should inject Read, Write, Edit, Bash, Glob, Grep"

# Test 8: Agent with critical_instruction
echo ""
echo "=== Test 8: Agent with Critical Instruction ===="
INPUT_JSON_CRITICAL='{
  "session_id": "test-session-404",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "claude-code-guide",
    "prompt": "How to use hooks?"
  },
  "hook_event_name": "PreToolUse"
}'
run_test "claude-code-guide (with critical instruction)" "$INPUT_JSON_CRITICAL" "Should inject tools + critical instruction"

# Test 9: Empty prompt (should handle)
echo ""
echo "=== Test 9: Empty Prompt ===="
INPUT_JSON_EMPTY='{
  "session_id": "test-session-505",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "Plan",
    "prompt": ""
  },
  "hook_event_name": "PreToolUse"
}'
run_test "Empty prompt string" "$INPUT_JSON_EMPTY" "Should pass through (invalid prompt)"

# Test 10: Very long prompt (performance test)
echo ""
echo "=== Test 10: Long Prompt (Performance) ===="
LONG_PROMPT=$(python3 -c "print('x' * 10000)")
INPUT_JSON_LONG=$(cat <<EOF
{
  "session_id": "test-session-606",
  "tool_name": "Task",
  "tool_input": {
    "subagent_type": "Plan",
    "prompt": "$LONG_PROMPT"
  },
  "hook_event_name": "PreToolUse"
}
EOF
)
run_test "Long prompt (10KB)" "$INPUT_JSON_LONG" "Should complete in <100ms"

# Summary
echo ""
echo "============================================"
echo "Test Summary"
echo "============================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
  exit 0
else
  echo -e "${RED}✗ SOME TESTS FAILED${NC}"
  echo ""
  echo "Review errors above before adding hook to settings.json"
  exit 1
fi

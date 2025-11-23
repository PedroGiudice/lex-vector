#!/bin/bash
#
# Test Suite Verification Script
#
# Verifies that the test suite is properly structured and ready to run
#

set -e

echo "🔍 Verifying Orchestration Tracker Test Suite..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper function
check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
  else
    echo -e "${RED}✗${NC} $1 (missing)"
    ((CHECKS_FAILED++))
  fi
}

check_dir() {
  if [ -d "$1" ]; then
    echo -e "${GREEN}✓${NC} $1/"
    ((CHECKS_PASSED++))
  else
    echo -e "${RED}✗${NC} $1/ (missing)"
    ((CHECKS_FAILED++))
  fi
}

# Check directory structure
echo "📁 Directory Structure:"
check_dir "tests"
check_dir "tests/unit"
check_dir "tests/integration"
check_dir "tests/fixtures"
echo ""

# Check infrastructure files
echo "⚙️  Test Infrastructure:"
check_file "tests/setup.ts"
check_file "tests/helpers.ts"
check_file "vitest.config.ts"
echo ""

# Check fixture files
echo "📦 Test Fixtures:"
check_file "tests/fixtures/mock-agents.ts"
check_file "tests/fixtures/mock-hooks.ts"
check_file "tests/fixtures/mock-skills.ts"
echo ""

# Check unit test files
echo "🧪 Unit Tests:"
check_file "tests/unit/plugin-registry.test.ts"
check_file "tests/unit/agent-discovery.test.ts"
check_file "tests/unit/hook-monitor.test.ts"
check_file "tests/unit/skill-tracker.test.ts"
echo ""

# Check integration test files
echo "🔗 Integration Tests:"
check_file "tests/integration/orchestration-full-cycle.test.ts"
check_file "tests/integration/performance.test.ts"
echo ""

# Check documentation
echo "📚 Documentation:"
check_file "tests/README.md"
check_file "TEST_SUITE_SUMMARY.md"
echo ""

# Count test files
echo "📊 Statistics:"
UNIT_TESTS=$(find tests/unit -name "*.test.ts" 2>/dev/null | wc -l)
INTEGRATION_TESTS=$(find tests/integration -name "*.test.ts" 2>/dev/null | wc -l)
TOTAL_TESTS=$((UNIT_TESTS + INTEGRATION_TESTS))
echo -e "${GREEN}✓${NC} Unit test files: $UNIT_TESTS"
echo -e "${GREEN}✓${NC} Integration test files: $INTEGRATION_TESTS"
echo -e "${GREEN}✓${NC} Total test files: $TOTAL_TESTS"
echo ""

# Count lines of code
if command -v wc &> /dev/null; then
  TOTAL_LINES=$(find tests -name "*.ts" -type f 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
  echo -e "${GREEN}✓${NC} Total lines of test code: $TOTAL_LINES"
  echo ""
fi

# Verify package.json has test scripts
if [ -f "package.json" ]; then
  if grep -q "\"test\":" package.json; then
    echo -e "${GREEN}✓${NC} package.json has test script"
    ((CHECKS_PASSED++))
  else
    echo -e "${YELLOW}⚠${NC} package.json missing test script (add manually)"
    ((CHECKS_FAILED++))
  fi
else
  echo -e "${RED}✗${NC} package.json not found"
  ((CHECKS_FAILED++))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $CHECKS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✅ All checks passed!${NC} ($CHECKS_PASSED/$((CHECKS_PASSED + CHECKS_FAILED)))"
  echo ""
  echo "Test suite is ready. Next steps:"
  echo "  1. Install dependencies: npm install -D vitest @vitest/coverage-v8"
  echo "  2. Run tests: npm test"
  echo "  3. Check coverage: npm run test:coverage"
else
  echo -e "${RED}❌ Some checks failed${NC} ($CHECKS_FAILED failures, $CHECKS_PASSED passed)"
  echo ""
  echo "Fix the missing files/directories listed above."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $CHECKS_FAILED

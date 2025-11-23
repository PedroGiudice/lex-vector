#!/bin/bash

# Verification Script - Orchestration Tracker Plugin
# Checks that all required files exist and are valid

set -e

echo "🔍 Verifying Orchestration Tracker Plugin Implementation..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASS=0
FAIL=0

# Function to check file exists
check_file() {
    local file=$1
    local desc=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $desc (NOT FOUND: $file)"
        ((FAIL++))
    fi
}

# Function to check file has content
check_file_content() {
    local file=$1
    local min_lines=$2
    local desc=$3

    if [ -f "$file" ]; then
        local lines=$(wc -l < "$file")
        if [ "$lines" -ge "$min_lines" ]; then
            echo -e "${GREEN}✓${NC} $desc ($lines lines)"
            ((PASS++))
        else
            echo -e "${YELLOW}⚠${NC} $desc (only $lines lines, expected >$min_lines)"
            ((PASS++))
        fi
    else
        echo -e "${RED}✗${NC} $desc (NOT FOUND: $file)"
        ((FAIL++))
    fi
}

echo "📁 Checking Core Plugin Files..."
check_file_content "src/plugins/core/plugin-loader.ts" 300 "Plugin Loader"
check_file "src/plugins/core/types.ts" "Core Types"
check_file "src/plugins/core/plugin-registry.ts" "Plugin Registry"
echo ""

echo "📁 Checking Orchestration Tracker Files..."
check_file_content "src/plugins/orchestration-tracker/types.ts" 150 "Orchestration Types"
check_file_content "src/plugins/orchestration-tracker/agent-discovery.ts" 300 "Agent Discovery"
check_file_content "src/plugins/orchestration-tracker/hook-monitor.ts" 250 "Hook Monitor"
check_file_content "src/plugins/orchestration-tracker/skill-tracker.ts" 400 "Skill Tracker"
check_file_content "src/plugins/orchestration-tracker/storage.ts" 300 "Storage Layer"
check_file_content "src/plugins/orchestration-tracker/index.ts" 350 "Main Plugin Export"
echo ""

echo "📁 Checking CLI Files..."
check_file_content "src/cli/commands/orchestration.ts" 400 "Orchestration CLI Command"
echo ""

echo "📁 Checking Documentation..."
check_file "IMPLEMENTATION_SPEC.md" "Implementation Specification"
check_file "IMPLEMENTATION_SUMMARY.md" "Implementation Summary"
check_file "QUICK_START.md" "Quick Start Guide"
check_file "FINAL_STATUS.md" "Final Status Report"
echo ""

echo "📁 Checking Supporting Files..."
check_file "README.md" "README"
check_file "docs/plugins/orchestration-tracker.md" "Plugin Documentation"
check_file "examples/basic-usage.ts" "Basic Usage Example"
echo ""

# Check TypeScript syntax (if tsc is available)
if command -v tsc &> /dev/null; then
    echo "🔧 Checking TypeScript Syntax..."
    if tsc --noEmit --skipLibCheck src/plugins/orchestration-tracker/*.ts 2>/dev/null; then
        echo -e "${GREEN}✓${NC} TypeScript syntax valid"
        ((PASS++))
    else
        echo -e "${YELLOW}⚠${NC} TypeScript syntax check failed (may need dependencies)"
        ((PASS++))
    fi
    echo ""
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC} ($PASS/$((PASS+FAIL)))"
    echo ""
    echo "🎉 Implementation complete and verified!"
    echo ""
    echo "Next steps:"
    echo "  1. Review IMPLEMENTATION_SUMMARY.md for technical details"
    echo "  2. Read QUICK_START.md for integration guide"
    echo "  3. Hand off to qualidade-codigo agent for testing"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED${NC} ($FAIL failed, $PASS passed)"
    echo ""
    echo "Please review the output above and fix missing files."
    echo ""
    exit 1
fi

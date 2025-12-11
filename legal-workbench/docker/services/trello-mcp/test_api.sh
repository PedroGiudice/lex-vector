#!/usr/bin/env bash
# Test script for Trello MCP API
# Usage: ./test_api.sh [base_url]

set -e

BASE_URL="${1:-http://localhost:8004}"

echo "=========================================="
echo "Testing Trello MCP API at $BASE_URL"
echo "=========================================="
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"

    echo -n "Testing: $name ... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$BASE_URL$endpoint")
    fi

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        if [ -n "$body" ]; then
            echo "   Response: $(echo $body | jq -c '.' 2>/dev/null || echo $body | head -c 100)"
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        if [ -n "$body" ]; then
            echo "   Error: $(echo $body | jq -c '.' 2>/dev/null || echo $body)"
        fi
    fi
    echo
}

# ==============================================================================
# System Endpoints
# ==============================================================================

echo "1. SYSTEM ENDPOINTS"
echo "-------------------"
test_endpoint "Root endpoint" "GET" "/"
test_endpoint "Health check" "GET" "/health"

# ==============================================================================
# Board Endpoints
# ==============================================================================

echo "2. BOARD ENDPOINTS"
echo "------------------"
test_endpoint "List all boards" "GET" "/api/v1/boards"

# Note: The following tests require a valid board_id
# Uncomment and replace with your board ID to test

# BOARD_ID="your_board_id_here"
# test_endpoint "Get board structure" "GET" "/api/v1/boards/$BOARD_ID"

# ==============================================================================
# Card Endpoints (require manual setup)
# ==============================================================================

echo "3. CARD ENDPOINTS (manual setup required)"
echo "------------------------------------------"
echo -e "${YELLOW}⚠ Skipping card tests (require valid list_id)${NC}"
echo "   To test card operations:"
echo "   1. Get a board structure: GET /api/v1/boards/{board_id}"
echo "   2. Copy a list_id from the response"
echo "   3. Use it in the card creation request"
echo

# Example card creation (commented out)
# LIST_ID="your_list_id_here"
# test_endpoint "Create card" "POST" "/api/v1/cards" \
#     '{
#       "list_id": "'$LIST_ID'",
#       "name": "Test Card from API",
#       "desc": "This is a test card created via the API",
#       "due": "2025-12-31T23:59:59Z"
#     }'

# ==============================================================================
# MCP Tools Endpoints
# ==============================================================================

echo "4. MCP TOOLS ENDPOINTS"
echo "----------------------"
test_endpoint "List MCP tools" "GET" "/api/v1/mcp/tools/list"

# Example MCP tool call (commented out)
# BOARD_ID="your_board_id_here"
# test_endpoint "Call MCP tool" "POST" "/api/v1/mcp/tools/call" \
#     '{
#       "tool_name": "trello_list_boards",
#       "arguments": {}
#     }'

# ==============================================================================
# Rate Limiting Test
# ==============================================================================

echo "5. RATE LIMITING TEST"
echo "---------------------"
echo "Testing rate limiter (10 rapid requests)..."

SUCCESS_COUNT=0
RATE_LIMITED=0

for i in {1..10}; do
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
    if [ "$http_code" = "200" ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    elif [ "$http_code" = "429" ]; then
        RATE_LIMITED=$((RATE_LIMITED + 1))
    fi
done

echo "   Successful: $SUCCESS_COUNT"
echo "   Rate limited: $RATE_LIMITED"

if [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✓ Rate limiter working${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "   ${RED}✗ All requests blocked${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo

# ==============================================================================
# Summary
# ==============================================================================

echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
echo

if [ "$TESTS_FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

#!/bin/bash
# legal-workbench/scripts/test.sh
# Run frontend tests
set -e

cd "$(dirname "$0")/../frontend"

case "${1:-watch}" in
    watch)
        echo "Running tests in watch mode..."
        bun run test:watch
        ;;
    coverage)
        echo "Running tests with coverage..."
        bun run test:coverage
        ;;
    ci)
        echo "Running tests in CI mode..."
        bun run test -- --run
        ;;
    *)
        echo "Usage: ./scripts/test.sh [watch|coverage|ci]"
        echo ""
        echo "Modes:"
        echo "  watch    - Run tests in watch mode (default)"
        echo "  coverage - Run tests with coverage report"
        echo "  ci       - Run tests once (for CI/CD)"
        exit 1
        ;;
esac

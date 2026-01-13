#!/usr/bin/env bash
#===============================================================================
# run-iterative-research.sh - Iterative Deep Research Agent Wrapper
#===============================================================================
#
# DESCRIPTION:
#   Wrapper for the Iterative Deep Research Agent. Unlike the standard agent,
#   this one executes multiple research iterations with gap analysis.
#
# USAGE:
#   ./run-iterative-research.sh "Your research topic here"
#   ./run-iterative-research.sh --help
#   ./run-iterative-research.sh --check-deps
#
# EXAMPLES:
#   ./run-iterative-research.sh "Compare vector databases: Pinecone vs Weaviate"
#   ./run-iterative-research.sh --iterations 3 "Latest developments in quantum computing"
#
# ENVIRONMENT VARIABLES:
#   GOOGLE_API_KEY      - Required. Google AI Studio API key.
#   RESEARCH_OUTPUT_DIR - Optional. Output directory (default: ./research_output)
#   RESEARCH_MODEL      - Optional. Model name (default: gemini-2.5-flash)
#
# EXIT CODES:
#   0 - Success
#   1 - Missing dependencies
#   2 - Missing API key
#   3 - Invalid arguments
#   4 - Runtime error
#
#===============================================================================

set -euo pipefail

# Script directory (resolve symlinks)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SCRIPT="${SCRIPT_DIR}/docs/iterative_research_agent.py"
VENV_DIR="${SCRIPT_DIR}/deep_research_sandbox/.venv"

# Default configuration
: "${RESEARCH_OUTPUT_DIR:=${SCRIPT_DIR}/deep_research_sandbox/research_output}"
: "${RESEARCH_MODEL:=gemini-2.5-flash}"
: "${MAX_ITERATIONS:=5}"
: "${MIN_SOURCES:=20}"

# Colors for output (disabled if not terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    NC='\033[0m' # No Color
else
    RED='' GREEN='' YELLOW='' BLUE='' CYAN='' NC=''
fi

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------

print_header() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  ITERATIVE DEEP RESEARCH AGENT${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

show_help() {
    cat << 'EOF'
ITERATIVE DEEP RESEARCH AGENT - Multi-Pass Research with Gap Analysis

USAGE:
    run-iterative-research.sh [OPTIONS] "TOPIC"

ARGUMENTS:
    TOPIC           Research topic (required unless using --help or --check-deps)

OPTIONS:
    -h, --help      Show this help message
    -c, --check-deps
                    Verify all dependencies are installed
    -o, --output DIR
                    Output directory (default: ./research_output)
    -m, --model MODEL
                    Gemini model to use (default: gemini-2.5-flash)
    -i, --iterations N
                    Maximum iterations (default: 5)
    -s, --min-sources N
                    Minimum sources before stopping (default: 20)
    -v, --verbose   Enable verbose output
    --json          Output in JSON format instead of Markdown

DIFFERENCE FROM STANDARD RESEARCH:
    The iterative agent:
    1. Decomposes topics into sub-vectors
    2. Executes multiple research passes
    3. Analyzes gaps after each iteration
    4. Refines queries based on what's missing
    5. Stops when criteria met (min sources, saturation, or max iterations)

ENVIRONMENT:
    GOOGLE_API_KEY  Google AI Studio API key (required)

EXAMPLES:
    # Basic iterative research
    ./run-iterative-research.sh "Best practices for Kubernetes security"

    # With custom iterations
    ./run-iterative-research.sh -i 3 -s 15 "Compare React vs Vue in 2026"

    # Custom output directory
    ./run-iterative-research.sh -o ./my-reports "Deep analysis of transformers"

EOF
}

check_dependencies() {
    local missing=0

    print_info "Checking dependencies..."

    # Check Python
    if command -v python3 &>/dev/null; then
        local py_version
        py_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python $py_version"
    else
        print_error "Python 3 not found"
        missing=1
    fi

    # Check virtual environment
    if [[ -d "$VENV_DIR" ]]; then
        print_success "Virtual environment: $VENV_DIR"
    else
        print_error "Virtual environment not found: $VENV_DIR"
        echo "       Run: python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install google-adk google-genai python-dotenv"
        missing=1
    fi

    # Check agent script
    if [[ -f "$AGENT_SCRIPT" ]]; then
        print_success "Agent script: $AGENT_SCRIPT"
    else
        print_error "Agent script not found: $AGENT_SCRIPT"
        missing=1
    fi

    # Check API key
    if [[ -n "${GOOGLE_API_KEY:-}" ]]; then
        print_success "GOOGLE_API_KEY is set"
    elif [[ -f "${SCRIPT_DIR}/.env" ]]; then
        if grep -q "GOOGLE_API_KEY" "${SCRIPT_DIR}/.env" 2>/dev/null; then
            print_success "GOOGLE_API_KEY found in .env"
        else
            print_error "GOOGLE_API_KEY not set and not found in .env"
            missing=1
        fi
    else
        print_error "GOOGLE_API_KEY not set"
        echo "       Set with: export GOOGLE_API_KEY='your-key-here'"
        missing=1
    fi

    # Check Python packages (if venv exists)
    if [[ -d "$VENV_DIR" ]]; then
        source "$VENV_DIR/bin/activate" 2>/dev/null || true

        declare -A pkg_imports=(
            ["google-adk"]="google.adk"
            ["google-genai"]="google.genai"
        )

        for pkg in "${!pkg_imports[@]}"; do
            local import_name="${pkg_imports[$pkg]}"
            if python3 -c "import ${import_name}" 2>/dev/null; then
                print_success "Python package: $pkg"
            else
                print_error "Python package missing: $pkg"
                missing=1
            fi
        done

        deactivate 2>/dev/null || true
    fi

    echo ""
    if [[ $missing -eq 0 ]]; then
        print_success "All dependencies satisfied!"
        return 0
    else
        print_error "Some dependencies are missing"
        return 1
    fi
}

load_env() {
    if [[ -z "${GOOGLE_API_KEY:-}" ]] && [[ -f "${SCRIPT_DIR}/.env" ]]; then
        while IFS='=' read -r key value; do
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            export "$key=$value"
        done < "${SCRIPT_DIR}/.env"
    fi
}

cleanup() {
    if [[ -n "${TEMP_LOG:-}" ]] && [[ -f "$TEMP_LOG" ]]; then
        rm -f "$TEMP_LOG"
    fi
}

#-------------------------------------------------------------------------------
# Main Execution
#-------------------------------------------------------------------------------

main() {
    local topic=""
    local verbose=0
    local json_output=0

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -c|--check-deps)
                check_dependencies
                exit $?
                ;;
            -o|--output)
                RESEARCH_OUTPUT_DIR="$2"
                shift 2
                ;;
            -m|--model)
                RESEARCH_MODEL="$2"
                shift 2
                ;;
            -i|--iterations)
                MAX_ITERATIONS="$2"
                shift 2
                ;;
            -s|--min-sources)
                MIN_SOURCES="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=1
                shift
                ;;
            --json)
                json_output=1
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 3
                ;;
            *)
                topic="$1"
                shift
                ;;
        esac
    done

    # Validate topic
    if [[ -z "$topic" ]]; then
        print_error "No research topic provided"
        echo "Usage: $0 \"Your research topic here\""
        echo "Use --help for more information"
        exit 3
    fi

    # Setup trap for cleanup
    trap cleanup EXIT

    # Load environment
    load_env

    # Verify API key
    if [[ -z "${GOOGLE_API_KEY:-}" ]]; then
        print_error "GOOGLE_API_KEY is not set"
        echo "Set it with: export GOOGLE_API_KEY='your-api-key'"
        exit 2
    fi

    # Verify dependencies exist
    if [[ ! -f "$AGENT_SCRIPT" ]]; then
        print_error "Agent script not found: $AGENT_SCRIPT"
        exit 1
    fi

    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found: $VENV_DIR"
        echo "Run: python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install google-adk google-genai"
        exit 1
    fi

    # Create output directory
    mkdir -p "$RESEARCH_OUTPUT_DIR"

    # Print header
    print_header
    echo ""
    print_info "Topic: $topic"
    print_info "Model: $RESEARCH_MODEL"
    print_info "Max Iterations: $MAX_ITERATIONS"
    print_info "Min Sources: $MIN_SOURCES"
    print_info "Output: $RESEARCH_OUTPUT_DIR"
    echo ""

    # Activate virtual environment and run
    print_info "Starting iterative research..."
    echo ""

    # Execute
    (
        cd "$SCRIPT_DIR/deep_research_sandbox"
        source "$VENV_DIR/bin/activate"
        export GOOGLE_API_KEY

        if [[ $verbose -eq 1 ]]; then
            python3 "$AGENT_SCRIPT" "$topic"
        else
            python3 "$AGENT_SCRIPT" "$topic" 2>&1
        fi
    )

    local exit_code=$?

    echo ""
    if [[ $exit_code -eq 0 ]]; then
        print_success "Iterative research completed successfully!"
    else
        print_error "Research failed with exit code: $exit_code"
        exit 4
    fi
}

# Run main function
main "$@"

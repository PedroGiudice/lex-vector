#!/usr/bin/env bash
#===============================================================================
# run-research.sh - Gemini ADK Deep Research Agent Wrapper
#===============================================================================
#
# DESCRIPTION:
#   Production-grade wrapper for the Gemini ADK Deep Research Agent.
#   Performs autonomous web research using Google's Agent Development Kit.
#
# USAGE:
#   ./run-research.sh "Your research topic here"
#   ./run-research.sh --help
#   ./run-research.sh --check-deps
#
# EXAMPLES:
#   ./run-research.sh "Compare vector databases: Pinecone vs Weaviate"
#   ./run-research.sh "Latest developments in quantum computing 2026"
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
# AUTHOR:
#   Generated for Claude Code automation
#
# LICENSE:
#   MIT
#
#===============================================================================

set -euo pipefail

# Script directory (resolve symlinks)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_SCRIPT="${SCRIPT_DIR}/docs/deep_research_agent.py"
VENV_DIR="${SCRIPT_DIR}/deep_research_sandbox/.venv"

# Default configuration
: "${RESEARCH_OUTPUT_DIR:=${SCRIPT_DIR}/research_output}"
: "${RESEARCH_MODEL:=gemini-2.5-flash}"

# Colors for output (disabled if not terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

#-------------------------------------------------------------------------------
# Helper Functions
#-------------------------------------------------------------------------------

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  DEEP RESEARCH AGENT${NC}"
    echo -e "${BLUE}============================================================${NC}"
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
DEEP RESEARCH AGENT - Autonomous Technical Research Tool

USAGE:
    run-research.sh [OPTIONS] "TOPIC"

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
    -v, --verbose   Enable verbose output
    --json          Output in JSON format instead of Markdown

ENVIRONMENT:
    GOOGLE_API_KEY  Google AI Studio API key (required)

EXAMPLES:
    # Basic research
    ./run-research.sh "What are the best practices for Kubernetes security?"

    # Custom output directory
    ./run-research.sh -o ./my-reports "Compare React vs Vue in 2026"

    # Use different model
    ./run-research.sh -m gemini-2.5-pro "Deep analysis of transformer architectures"

    # Check dependencies
    ./run-research.sh --check-deps

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
        echo "       Run: python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install google-adk google-genai tenacity python-dotenv"
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
        # Try to load from .env
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

        # Package name -> import name mapping
        declare -A pkg_imports=(
            ["google-adk"]="google.adk"
            ["google-genai"]="google.genai"
            ["tenacity"]="tenacity"
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
    # Load .env file if API key not already set
    if [[ -z "${GOOGLE_API_KEY:-}" ]] && [[ -f "${SCRIPT_DIR}/.env" ]]; then
        # Simple .env parser (handles KEY=value format)
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            # Remove quotes from value
            value="${value%\"}"
            value="${value#\"}"
            value="${value%\'}"
            value="${value#\'}"
            # Export the variable
            export "$key=$value"
        done < "${SCRIPT_DIR}/.env"
    fi
}

cleanup() {
    # Cleanup function for trap
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
        echo "Run: python3 -m venv $VENV_DIR && source $VENV_DIR/bin/activate && pip install google-adk google-genai tenacity"
        exit 1
    fi

    # Create output directory
    mkdir -p "$RESEARCH_OUTPUT_DIR"

    # Print header
    print_header
    echo ""
    print_info "Topic: $topic"
    print_info "Model: $RESEARCH_MODEL"
    print_info "Output: $RESEARCH_OUTPUT_DIR"
    echo ""

    # Activate virtual environment and run
    print_info "Starting research..."
    echo ""

    # Build command
    local cmd="python3 \"$AGENT_SCRIPT\" \"$topic\""

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
        print_success "Research completed successfully!"
    else
        print_error "Research failed with exit code: $exit_code"
        exit 4
    fi
}

# Run main function
main "$@"

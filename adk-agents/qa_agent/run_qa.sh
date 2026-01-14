#!/usr/bin/env bash
set -e

# Directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

# Help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: ./run_qa.sh <TARGET_URL> [--repo <PATH_TO_REPO>]"
    echo "Example: ./run_qa.sh http://localhost:3000 --repo /home/user/my-react-app"
    exit 0
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found."
    exit 1
fi

# Setup Venv
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r "${SCRIPT_DIR}/requirements.txt"
    playwright install chromium
else
    source "$VENV_DIR/bin/activate"
fi

# Run Agent
# Pass all arguments to main.py
python3 "${SCRIPT_DIR}/main.py" "$@"

#!/bin/bash
# Start the Abogen Web UI backend using the project's virtual environment
# This script ensures the backend has access to all installed dependencies

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .venv exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Error: Virtual environment not found at $PROJECT_ROOT/.venv"
    exit 1
fi

# Check if backend directory exists
if [ ! -d "$SCRIPT_DIR/backend" ]; then
    echo "Error: Backend directory not found at $SCRIPT_DIR/backend"
    exit 1
fi

echo "Starting Abogen Web UI Backend..."
echo "Using Python: $PROJECT_ROOT/.venv/bin/python"
echo "Backend directory: $SCRIPT_DIR/backend"
echo ""

# Start the backend server
cd "$SCRIPT_DIR/backend"
"$PROJECT_ROOT/.venv/bin/python" main.py

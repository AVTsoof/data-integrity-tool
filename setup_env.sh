#!/bin/bash

# Exit on error
set -e

echo "Setting up development environment via Python..."

# Check if Python is available
if ! command -v python3 > /dev/null 2>&1
then
    echo "python3 could not be found. Please install Python."
    # Debug info for the user
    which python3 || echo "python3 not found in PATH"
    exit 1
fi

python3 setup_env.py

echo
echo "Setup complete."
echo "To activate the environment, run: source .venv/bin/activate"

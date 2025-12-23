#!/bin/bash

# Exit on error
set -e

echo "Checking for environment..."

PYTHON_CMD="python3"
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo "Using virtual environment: .venv"
fi

# Check for PyInstaller
if ! "$PYTHON_CMD" -m PyInstaller --version > /dev/null 2>&1
then
    echo "PyInstaller is not installed."
    echo "Please run ./setup_env.sh first to install dependencies."
    exit 1
fi

echo "Building Data Integrity Tool..."
"$PYTHON_CMD" build_release.py

echo
echo "Build successful!"

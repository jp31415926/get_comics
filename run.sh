#!/usr/bin/env bash
# Run the comic downloader.
# On first run, creates a venv, installs dependencies, and downloads Chromium.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "First run: setting up virtual environment..."
    python3 -m venv venv
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt
    echo "Installing Playwright browsers (Chromium)..."
    venv/bin/playwright install chromium
    echo "Installing Chromium system dependencies..."
    venv/bin/playwright install-deps chromium
    echo "Setup complete."
fi

exec venv/bin/python main.py "$@"

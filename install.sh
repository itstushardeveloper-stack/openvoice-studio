#!/usr/bin/env bash
# ==========================================================
#   Chatterbox AI Voice Studio - Linux / macOS Installer
# ==========================================================

set -e

FULL_MODEL=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --full-model) FULL_MODEL=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "=========================================================="
echo "   Chatterbox AI Voice Studio - Installation (Unix)       "
echo "=========================================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[X] Python 3 is required but not installed. Aborting."
    exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[✓] Found Python $PY_VERSION"

# Setup virtual environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment 'venv'..."
    python3 -m venv venv
fi

echo "[*] Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install core dependencies
echo "[*] Installing core dependencies from requirements.txt..."
python -m pip install -r requirements.txt

# Optional full model
if [ "$FULL_MODEL" = true ]; then
    echo "[*] Installing full model dependencies..."
    if [ -d "upstream/chatterbox" ]; then
        python -m pip install -e upstream/chatterbox
    else
        python -m pip install chatterbox-tts
    fi
fi

# Create directories
mkdir -p generated_audio voice_profiles models

# Copy .env
if [ ! -f ".env" ]; then
    echo "[*] Creating .env from .env.example..."
    cp .env.example .env
fi

echo "=========================================================="
echo "[✓] Installation completed successfully!"
echo "To start the Voice Studio server, run: ./start-server.sh"
echo "=========================================================="

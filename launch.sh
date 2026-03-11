#!/usr/bin/env bash
# FME Training Automation - Launcher
# Checks prerequisites and starts the local server.

set -euo pipefail

echo "============================================"
echo " FME Training Automation - Launcher"
echo "============================================"
echo

# Run from the script's directory so relative paths work
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# -----------------------------------------------
# 1. Find Python
# -----------------------------------------------
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found."
    echo "       Install Python 3.9 or later from https://www.python.org/downloads/"
    exit 1
fi

# Require Python 3.9+
if ! "$PYTHON" -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null; then
    echo "ERROR: Python 3.9 or later is required. Found: $("$PYTHON" --version 2>&1)"
    exit 1
fi
echo "[OK] $("$PYTHON" --version 2>&1)"

# -----------------------------------------------
# 2. Check .env
# -----------------------------------------------
if [ ! -f ".env" ]; then
    if [ -f ".env.sample" ]; then
        echo
        echo "WARNING: No .env file found. Creating one from .env.sample..."
        cp ".env.sample" ".env"
        echo
        echo "ACTION REQUIRED:"
        echo "  Open .env and set your OPENAI_API_KEY, then re-run this script."
        echo
        echo "  nano .env    (or use any text editor)"
        exit 1
    else
        echo
        echo "ERROR: .env not found and .env.sample is also missing."
        echo "       Create a .env file with at least: OPENAI_API_KEY=your_key_here"
        exit 1
    fi
fi

# Check OPENAI_API_KEY is present and not the placeholder
if ! grep -E "^OPENAI_API_KEY=.+" ".env" | grep -qv "your_openai_api_key_here"; then
    echo
    echo "ERROR: OPENAI_API_KEY is missing or still set to the placeholder in .env."
    echo "       Open .env and replace \"your_openai_api_key_here\" with your actual key."
    exit 1
fi
echo "[OK] .env"

# -----------------------------------------------
# 3. Check / install Python requirements
# -----------------------------------------------
echo "Checking Python requirements..."
if ! "$PYTHON" -c "import openai, bs4, pandas, dotenv, requests, tqdm" 2>/dev/null; then
    echo "Some packages are missing. Installing from requirements.txt..."
    echo
    "$PYTHON" -m pip install -r requirements.txt
    echo
    echo "[OK] Requirements installed."
else
    echo "[OK] Requirements satisfied."
fi

# -----------------------------------------------
# 4. Free port 8080 if already in use
# -----------------------------------------------
PORT=8080
if command -v lsof &>/dev/null; then
    PIDS=$(lsof -ti :"$PORT" 2>/dev/null || true)
elif command -v fuser &>/dev/null; then
    PIDS=$(fuser "${PORT}/tcp" 2>/dev/null | tr -s ' ' '\n' | grep -E '^[0-9]+$' || true)
else
    PIDS=""
fi

if [ -n "$PIDS" ]; then
    echo "Port $PORT is already in use (PID $PIDS). Stopping existing process..."
    echo "$PIDS" | xargs kill 2>/dev/null || true
    sleep 1
fi

# -----------------------------------------------
# 5. Launch server and open browser
# -----------------------------------------------
echo
echo "Starting server at http://localhost:$PORT ..."
echo "Press Ctrl+C to stop."
echo

# Open browser after a short delay so the server has time to bind
(
    sleep 1.5
    if command -v xdg-open &>/dev/null; then
        xdg-open "http://localhost:$PORT/" 2>/dev/null || true
    elif command -v open &>/dev/null; then
        open "http://localhost:$PORT/"
    fi
) &

"$PYTHON" serve.py "$PORT"

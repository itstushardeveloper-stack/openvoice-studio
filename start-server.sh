#!/usr/bin/env bash
# ==========================================================
#   Chatterbox AI Voice Studio - Server Runner (Unix)
# ==========================================================

HOST="${1:-0.0.0.0}"
PORT="${2:-8000}"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

export PYTHONPATH=".:plugins/chatterbox:$PYTHONPATH"

echo "=========================================================="
echo "       Starting Chatterbox Voice Studio Server            "
echo "=========================================================="
echo "Host: http://$HOST:$PORT"
echo "Dashboard: http://localhost:$PORT/dashboard/index.html"
echo "API Health: http://localhost:$PORT/health"
echo "=========================================================="

exec python3 -m uvicorn plugins.chatterbox.backend.server:app --host "$HOST" --port "$PORT"

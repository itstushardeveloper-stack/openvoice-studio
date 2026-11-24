#!/usr/bin/env bash
# ==========================================================
#   OpenVoice Studio & VoiceStudio - Server Runner (Unix)
# ==========================================================

HOST="${1:-0.0.0.0}"
PORT="${2:-8000}"
PLUGIN="${3:-voicestudio}"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

export PYTHONPATH=".:plugins/$PLUGIN:plugins/chatterbox:$PYTHONPATH"

echo "=========================================================="
echo "   Starting OpenVoice Studio ($PLUGIN) Server             "
echo "=========================================================="
echo "Host: http://$HOST:$PORT"
echo "Dashboard: http://localhost:$PORT/dashboard/index.html"
echo "API Health: http://localhost:$PORT/health"
echo "=========================================================="

exec python3 -m uvicorn "plugins.$PLUGIN.backend.server:app" --host "$HOST" --port "$PORT"

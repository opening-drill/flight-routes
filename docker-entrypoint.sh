#!/bin/sh
set -e

echo "Starting Flask health server in background..."
python health_server.py &
FLASK_PID=$!

cleanup() {
  if kill -0 "$FLASK_PID" 2>/dev/null; then
    kill "$FLASK_PID" 2>/dev/null || true
    wait "$FLASK_PID" 2>/dev/null || true
  fi
}

trap cleanup TERM INT

echo "Starting planB (foreground)..."
exec python planB.py

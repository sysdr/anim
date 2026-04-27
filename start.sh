#!/usr/bin/env bash
# SynapseFlow - Start script
# Starts backend (port 8000) and frontend (port 5173)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
RUN_CMD="${RUN_CMD:-python -m anim.web.run}"

echo "Backend port: $BACKEND_PORT | Frontend port: $FRONTEND_PORT"

# Free backend port if in use
if lsof -ti :"$BACKEND_PORT" >/dev/null 2>&1; then
  echo "Port $BACKEND_PORT in use. Killing existing process..."
  lsof -ti :"$BACKEND_PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi
if lsof -ti :"$BACKEND_PORT" >/dev/null 2>&1; then
  echo "Failed to free port $BACKEND_PORT" >&2
  exit 1
fi

# Free frontend port if in use
if lsof -ti :"$FRONTEND_PORT" >/dev/null 2>&1; then
  echo "Port $FRONTEND_PORT in use. Killing existing process..."
  lsof -ti :"$FRONTEND_PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo "Starting backend: $RUN_CMD"
PORT="$BACKEND_PORT" $RUN_CMD &
BACKEND_PID=$!

echo "Starting frontend (Vite)..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID (port $BACKEND_PORT)"
echo "Frontend PID: $FRONTEND_PID (port $FRONTEND_PORT)"
echo "Use ./stop.sh to stop both."

wait

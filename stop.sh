#!/usr/bin/env bash
# SynapseFlow - Stop script
# Kills all processes on backend (8000) and frontend (5173) ports.

set -e

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

kill_port() {
  local port=$1
  local name=$2
  local killed=0
  while true; do
    local pids
    pids=$(lsof -ti :"$port" 2>/dev/null) || true
    if [ -z "$pids" ]; then
      break
    fi
    echo "Stopping $name on port $port (PIDs: $pids)..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
    killed=1
    sleep 0.5
  done
  if [ "$killed" -eq 1 ]; then
    echo "$name stopped."
  fi
  return 0
}

echo "Stopping SynapseFlow processes..."
kill_port "$BACKEND_PORT" "backend"
kill_port "$FRONTEND_PORT" "frontend"
echo "Done. All processes on ports $BACKEND_PORT and $FRONTEND_PORT have been killed."

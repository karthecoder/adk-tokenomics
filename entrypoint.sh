#!/bin/bash
set -e

echo "=== Booting Token Control Tower Container ==="

# 1. Start ADK Web Engine in subshell on port 8082
echo ">>> Starting ADK Agent Engine on port 8082..."
(cd /app/agent-nexus && adk web . --host 0.0.0.0 --port 8082 --allow_origins '*' --reload_agents) &

# 2. Wait up to 30 seconds for ADK Web engine on 8082 to be ready
echo ">>> Waiting for ADK Web Engine to start on port 8082..."
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8082/ > /dev/null 2>&1; then
    echo ">>> ADK Web Engine is READY on port 8082!"
    break
  fi
  sleep 1
done

# 3. Start Control Tower Dashboard Server from root /app directory
cd /app
PORT="${PORT:-8080}"
echo ">>> Starting Control Tower Dashboard on port ${PORT}..."
exec python3 /app/server.py "${PORT}"

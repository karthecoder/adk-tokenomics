#!/bin/bash
set -e

echo "=== Booting Token Control Tower Container ==="

# 1. Start ADK Web Engine in subshell on loopback 127.0.0.1:8082
echo ">>> Starting ADK Agent Engine on 127.0.0.1:8082..."
(cd /app/agent-nexus && adk web . --host 127.0.0.1 --port 8082 --allow_origins '*') &

# 2. Give ADK engine 2 seconds to initialize
sleep 2

# 3. Start Control Tower Dashboard Server from root /app directory
cd /app
PORT="${PORT:-8080}"
echo ">>> Starting Control Tower Dashboard on port ${PORT}..."
exec python3 /app/server.py "${PORT}"

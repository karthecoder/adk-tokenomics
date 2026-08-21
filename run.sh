#!/bin/bash
# Helper script to run the Agent Nexus Token Control Tower locally

# Find an open port starting from 8000
PORT=8000
while lsof -i :$PORT >/dev/null 2>&1; do
    PORT=$((PORT+1))
done

echo "=================================================================="
echo " Starting Agent Nexus Token Control Tower Dashboard locally..."
echo " Opening URL: http://localhost:$PORT"
echo "=================================================================="

# Boot custom python routing server in the background
python3 server.py $PORT

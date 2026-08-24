# Production Dockerfile for Token Control Tower & ADK Agent Nexus
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    bash \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . /app

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Cloud Run default port
ENV PORT=8080
EXPOSE 8080 8082

# Entrypoint script starts adk web on 8082 and server.py on $PORT
ENTRYPOINT ["/app/entrypoint.sh"]

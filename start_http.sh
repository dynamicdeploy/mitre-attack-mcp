#!/bin/bash

# Start MITRE ATT&CK MCP Server in HTTP mode
# This script starts the server using Docker Compose

set -e

echo "🌐 Starting MITRE ATT&CK MCP Server in HTTP mode..."
echo "📡 Server will be available at: http://localhost:8032"
echo ""

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    exit 1
fi

# Start the server
docker-compose up --build

echo ""
echo "✅ HTTP server started successfully!"
echo "🔗 Access the server at: http://localhost:8032/mcp/"
echo "🛑 Press Ctrl+C to stop the server"

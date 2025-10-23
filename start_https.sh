#!/bin/bash

# Start MITRE ATT&CK MCP Server in HTTPS mode
# This script starts the server using Docker Compose with SSL

set -e

echo "🔒 Starting MITRE ATT&CK MCP Server in HTTPS mode..."
echo "📡 Server will be available at: https://localhost:8032"
echo ""

# Check if SSL certificate exists
if [ ! -f "ssl/hd_app_ssl_server.crt" ] || [ ! -f "ssl/hd_app_ssl_server.key" ]; then
    echo "❌ SSL certificate not found. Generating from CSR..."
    echo "🔑 Running certificate generation script..."
    ./generate_ssl_cert.sh
    echo ""
fi

# Check if docker-compose.ssl.yml exists
if [ ! -f "docker-compose.ssl.yml" ]; then
    echo "❌ Error: docker-compose.ssl.yml not found"
    exit 1
fi

# Start the server
docker-compose -f docker-compose.ssl.yml up --build "$@"

echo ""
echo "✅ HTTPS server started successfully!"
echo "🔗 Access the server at: https://localhost:8032/mcp/"
echo "🛑 Press Ctrl+C to stop the server"

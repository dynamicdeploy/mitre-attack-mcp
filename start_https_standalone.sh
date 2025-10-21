#!/bin/bash

# Start MITRE ATT&CK MCP Server in HTTPS mode (standalone)
# This script starts the server directly without Docker using SSL

set -e

echo "🔒 Starting MITRE ATT&CK MCP Server in HTTPS mode (standalone)..."
echo "📡 Server will be available at: https://localhost:9443"
echo ""

# Check if SSL certificate exists
if [ ! -f "ssl/hd_app_ssl_server.crt" ] || [ ! -f "ssl/hd_app_ssl_server.key" ]; then
    echo "❌ SSL certificate not found. Generating from CSR..."
    echo "🔑 Running certificate generation script..."
    ./generate_ssl_cert.sh
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if server.py exists
if [ ! -f "src/mitre_attack_mcp/server.py" ]; then
    echo "❌ Error: server.py not found"
    exit 1
fi

# Start the server with SSL
echo "🚀 Starting HTTPS server..."
python src/mitre_attack_mcp/server.py --transport https --host 0.0.0.0 --port 9443 --ssl-cert ssl/hd_app_ssl_server.crt --ssl-key ssl/hd_app_ssl_server.key

echo ""
echo "✅ HTTPS server started successfully!"
echo "🔗 Access the server at: https://localhost:9443/mcp/"
echo "🛑 Press Ctrl+C to stop the server"

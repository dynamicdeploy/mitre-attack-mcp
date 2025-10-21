#!/bin/bash

# Start MITRE ATT&CK MCP Server in HTTP mode (standalone)
# This script starts the server directly without Docker

set -e

echo "🌐 Starting MITRE ATT&CK MCP Server in HTTP mode (standalone)..."
echo "📡 Server will be available at: http://localhost:8032"
echo ""

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

# Start the server
echo "🚀 Starting HTTP server..."
python src/mitre_attack_mcp/server.py --transport http --host 0.0.0.0 --port 8032

echo ""
echo "✅ HTTP server started successfully!"
echo "🔗 Access the server at: http://localhost:8032/mcp/"
echo "🛑 Press Ctrl+C to stop the server"

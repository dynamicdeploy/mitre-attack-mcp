#!/bin/bash

# MITRE ATT&CK MCP Server Launcher
# Interactive script to choose server startup mode

set -e

echo "🎯 MITRE ATT&CK MCP Server Launcher"
echo "=================================="
echo ""
echo "Choose your startup mode:"
echo ""
echo "🐳 Docker-based (Recommended):"
echo "  1) HTTP Server (Docker)"
echo "  2) HTTPS Server (Docker)"
echo ""
echo "🖥️  Standalone (Direct Python):"
echo "  3) HTTP Server (Standalone)"
echo "  4) HTTPS Server (Standalone)"
echo ""
echo "📚 Documentation:"
echo "  5) View startup scripts documentation"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo "🌐 Starting HTTP server with Docker..."
        ./start_http.sh
        ;;
    2)
        echo "🔒 Starting HTTPS server with Docker..."
        ./start_https.sh
        ;;
    3)
        echo "🌐 Starting HTTP server standalone..."
        ./start_http_standalone.sh
        ;;
    4)
        echo "🔒 Starting HTTPS server standalone..."
        ./start_https_standalone.sh
        ;;
    5)
        echo "📚 Opening documentation..."
        if command -v less &> /dev/null; then
            less STARTUP_SCRIPTS.md
        else
            cat STARTUP_SCRIPTS.md
        fi
        ;;
    *)
        echo "❌ Invalid choice. Please run the script again and select 1-5."
        exit 1
        ;;
esac

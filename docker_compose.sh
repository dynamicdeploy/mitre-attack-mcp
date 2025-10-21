#!/bin/bash

# MITRE ATT&CK MCP Server Docker Compose Manager
# HTTP mode with build and up/down operations

set -e

# Default values
ACTION="up"
BUILD="--build"
DETACHED=""
COMPOSE_FILE="docker-compose.yml"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        up)
            ACTION="up"
            shift
            ;;
        down)
            ACTION="down"
            shift
            ;;
        --no-build)
            BUILD=""
            shift
            ;;
        --detached)
            DETACHED="-d"
            shift
            ;;
        -d)
            DETACHED="-d"
            shift
            ;;
        --help|-h)
            echo "MITRE ATT&CK MCP Server Docker Compose Manager (HTTP)"
            echo ""
            echo "Usage: $0 [up|down] [options]"
            echo ""
            echo "Commands:"
            echo "  up       Start the server (default)"
            echo "  down     Stop the server"
            echo ""
            echo "Options:"
            echo "  --no-build    Skip building the image"
            echo "  --detached    Run in background"
            echo "  -d            Run in background (short form)"
            echo "  --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 up                    # Start with build"
            echo "  $0 up --detached         # Start in background"
            echo "  $0 up -d                 # Start in background (short)"
            echo "  $0 up --no-build         # Start without building"
            echo "  $0 down                  # Stop the server"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if docker-compose.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found"
    exit 1
fi

# Execute the action
if [ "$ACTION" = "up" ]; then
    echo "🌐 Starting MITRE ATT&CK MCP Server (HTTP mode)..."
    echo "📡 Server will be available at: http://localhost:8032"
    echo ""
    
    # Build and start
    docker-compose up $BUILD $DETACHED
    
    if [ -n "$DETACHED" ]; then
        echo ""
        echo "✅ HTTP server started in background!"
        echo "🔗 Access the server at: http://localhost:8032/mcp/"
        echo "🛑 To stop: $0 down"
    else
        echo ""
        echo "✅ HTTP server started successfully!"
        echo "🔗 Access the server at: http://localhost:8032/mcp/"
        echo "🛑 Press Ctrl+C to stop the server"
    fi
    
elif [ "$ACTION" = "down" ]; then
    echo "🛑 Stopping MITRE ATT&CK MCP Server (HTTP mode)..."
    docker-compose down
    echo "✅ HTTP server stopped successfully!"
fi

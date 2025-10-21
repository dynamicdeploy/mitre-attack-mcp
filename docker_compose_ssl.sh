#!/bin/bash

# MITRE ATT&CK MCP Server Docker Compose Manager (SSL)
# HTTPS mode with build and up/down operations

set -e

# Default values
ACTION="up"
BUILD="--build"
DETACHED=""
COMPOSE_FILE="docker-compose.ssl.yml"

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
            echo "MITRE ATT&CK MCP Server Docker Compose Manager (HTTPS/SSL)"
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
            echo ""
            echo "SSL Certificate Paths:"
            echo "  Certificate: ssl/hd_app_ssl_server.crt"
            echo "  Private Key: ssl/hd_app_ssl_server.key"
            exit 0
            ;;
        *)
            echo "❌ Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if docker-compose.ssl.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found"
    exit 1
fi

# Check for SSL certificates
if [ "$ACTION" = "up" ]; then
    if [ ! -f "ssl/hd_app_ssl_server.crt" ] || [ ! -f "ssl/hd_app_ssl_server.key" ]; then
        echo "❌ SSL certificate not found. Generating from CSR..."
        echo "🔑 Running certificate generation script..."
        if [ -f "generate_ssl_cert.sh" ]; then
            ./generate_ssl_cert.sh
        else
            echo "❌ Error: generate_ssl_cert.sh not found"
            exit 1
        fi
        echo ""
    fi
fi

# Execute the action
if [ "$ACTION" = "up" ]; then
    echo "🔒 Starting MITRE ATT&CK MCP Server (HTTPS/SSL mode)..."
    echo "📡 Server will be available at: https://localhost:9443"
    echo ""
    
    # Build and start
    docker-compose -f $COMPOSE_FILE up $BUILD $DETACHED
    
    if [ -n "$DETACHED" ]; then
        echo ""
        echo "✅ HTTPS server started in background!"
        echo "🔗 Access the server at: https://localhost:9443/mcp/"
        echo "🛑 To stop: $0 down"
    else
        echo ""
        echo "✅ HTTPS server started successfully!"
        echo "🔗 Access the server at: https://localhost:9443/mcp/"
        echo "🛑 Press Ctrl+C to stop the server"
    fi
    
elif [ "$ACTION" = "down" ]; then
    echo "🛑 Stopping MITRE ATT&CK MCP Server (HTTPS/SSL mode)..."
    docker-compose -f $COMPOSE_FILE down
    echo "✅ HTTPS server stopped successfully!"
fi

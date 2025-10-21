#!/bin/bash

# Generate SSL certificate from CSR for MITRE ATT&CK MCP Server
# This script creates a self-signed certificate from the provided CSR

set -e

# Create SSL directory
mkdir -p ssl

# Generate private key if it doesn't exist
if [ ! -f "ssl/hd_app_ssl_server.key" ]; then
    echo "🔑 Generating private key..."
    openssl genrsa -out ssl/hd_app_ssl_server.key 2048
fi

# Generate self-signed certificate from CSR
echo "📜 Generating self-signed certificate from CSR..."
openssl x509 -req -in hd_app_ssl_server.csr -signkey ssl/hd_app_ssl_server.key -out ssl/hd_app_ssl_server.crt -days 365

# Set proper permissions
chmod 600 ssl/hd_app_ssl_server.key
chmod 644 ssl/hd_app_ssl_server.crt

echo "✅ SSL certificate generated successfully!"
echo "📁 Certificate files:"
echo "   - Certificate: ssl/hd_app_ssl_server.crt"
echo "   - Private Key: ssl/hd_app_ssl_server.key"
echo ""
echo "🔒 You can now run the HTTPS server with:"
echo "   docker-compose -f docker-compose.ssl.yml up"

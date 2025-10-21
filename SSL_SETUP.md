# SSL Setup for MITRE ATT&CK MCP Server

This guide explains how to set up SSL/HTTPS for the MITRE ATT&CK MCP Server using your existing CSR file.

## Files Created

- `Dockerfile.ssl` - Dockerfile for SSL-enabled server
- `docker-compose.ssl.yml` - Docker Compose configuration for SSL
- `generate_ssl_cert.sh` - Script to generate SSL certificate from your CSR
- `SSL_SETUP.md` - This documentation

## Quick Start

1. **Generate SSL Certificate from your CSR:**
   ```bash
   ./generate_ssl_cert.sh
   ```

2. **Build and run the SSL-enabled server:**
   ```bash
   docker-compose -f docker-compose.ssl.yml up --build
   ```

3. **Test the HTTPS server:**
   ```bash
   curl -k https://localhost:9443/mcp/
   ```

## Manual SSL Certificate Generation

If you prefer to generate the certificate manually:

```bash
# Create SSL directory
mkdir -p ssl

# Generate private key (if not exists)
openssl genrsa -out ssl/hd_app_ssl_server.key 2048

# Generate self-signed certificate from your CSR
openssl x509 -req -in hd_app_ssl_server.csr -signkey ssl/hd_app_ssl_server.key -out ssl/hd_app_ssl_server.crt -days 365

# Set proper permissions
chmod 600 ssl/hd_app_ssl_server.key
chmod 644 ssl/hd_app_ssl_server.crt
```

## Running the Server

### With Docker Compose (Recommended)
```bash
docker-compose -f docker-compose.ssl.yml up --build
```

### Direct Docker Build
```bash
docker build -f Dockerfile.ssl -t mitre-attack-mcp-ssl .
docker run -p 8032:8032 -v $(pwd)/ssl:/app/ssl:ro mitre-attack-mcp-ssl
```

### Local Development
```bash
python src/mitre_attack_mcp/server.py --transport https --ssl-cert ssl/hd_app_ssl_server.crt --ssl-key ssl/hd_app_ssl_server.key
```

## Configuration

The SSL-enabled server uses these environment variables:
- `MCP_HOST=0.0.0.0` - Server host
- `MCP_PORT=8032` - Server port  
- `MCP_TRANSPORT=https` - Use HTTPS transport
- `MCP_DATA_DIR=/app/data` - Data directory

## Testing

Test the HTTPS endpoint:
```bash
# Test with curl (ignore certificate warnings)
curl -k https://localhost:9443/mcp/

# Test with browser (accept self-signed certificate)
open https://localhost:9443/mcp/
```

## Troubleshooting

1. **Certificate not found errors:**
   - Ensure the SSL directory is mounted correctly in Docker
   - Check file permissions (key should be 600, cert should be 644)

2. **Connection refused:**
   - Verify the server is running on the correct port
   - Check Docker port mapping

3. **SSL handshake errors:**
   - Ensure the certificate and key files are valid
   - Check that the certificate matches the private key

## Security Notes

- This setup uses a self-signed certificate for development/testing
- For production, use a certificate from a trusted CA
- The `-k` flag in curl ignores certificate verification (development only)
- Consider using Let's Encrypt for production certificates

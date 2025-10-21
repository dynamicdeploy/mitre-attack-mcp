# MITRE ATT&CK MCP Server Startup Scripts

This directory contains convenient shell scripts to start the MITRE ATT&CK MCP Server in different modes.

## 📋 Available Scripts

### Docker-based Scripts
- **`start_http.sh`** - Start HTTP server using Docker Compose
- **`start_https.sh`** - Start HTTPS server using Docker Compose with SSL

### Standalone Scripts  
- **`start_http_standalone.sh`** - Start HTTP server directly (no Docker)
- **`start_https_standalone.sh`** - Start HTTPS server directly (no Docker)

## 🚀 Quick Start

### HTTP Server (Docker)
```bash
./start_http.sh
```
- **URL**: http://localhost:8032/mcp/
- **Requirements**: Docker and docker-compose

### HTTPS Server (Docker)
```bash
./start_https.sh
```
- **URL**: https://localhost:8032/mcp/
- **Requirements**: Docker, docker-compose, SSL certificates
- **Auto-generates**: SSL certificates from CSR if missing

### HTTP Server (Standalone)
```bash
./start_http_standalone.sh
```
- **URL**: http://localhost:8032/mcp/
- **Requirements**: Python virtual environment with dependencies

### HTTPS Server (Standalone)
```bash
./start_https_standalone.sh
```
- **URL**: https://localhost:8032/mcp/
- **Requirements**: Python virtual environment, SSL certificates
- **Auto-generates**: SSL certificates from CSR if missing

## 🔧 Prerequisites

### For Docker Scripts
- Docker installed and running
- Docker Compose installed
- For HTTPS: SSL certificates (auto-generated if missing)

### For Standalone Scripts
- Python 3.13+ installed
- Virtual environment created: `python -m venv venv`
- Dependencies installed: `pip install -r requirements.txt`
- For HTTPS: SSL certificates (auto-generated if missing)

## 📁 SSL Certificate Paths

The scripts use these default SSL certificate paths:
- **Certificate**: `ssl/hd_app_ssl_server.crt`
- **Private Key**: `ssl/hd_app_ssl_server.key`
- **CSR**: `hd_app_ssl_server.csr` (for generation)

## 🛠️ Manual Certificate Generation

If you need to generate SSL certificates manually:

```bash
# Generate SSL certificate from CSR
./generate_ssl_cert.sh

# Or manually:
mkdir -p ssl
openssl genrsa -out ssl/hd_app_ssl_server.key 2048
openssl x509 -req -in hd_app_ssl_server.csr -signkey ssl/hd_app_ssl_server.key -out ssl/hd_app_ssl_server.crt -days 365
```

## 🔍 Troubleshooting

### Common Issues

1. **"Virtual environment not found"**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **"SSL certificate not found"**
   - Scripts will auto-generate certificates from CSR
   - Or run `./generate_ssl_cert.sh` manually

3. **"Docker not found"**
   - Install Docker Desktop
   - Ensure Docker is running

4. **"Port 8032 already in use"**
   - Stop existing server: `docker-compose down`
   - Or kill process: `lsof -ti:8032 | xargs kill -9`

### Testing the Server

```bash
# Test HTTP server
curl http://localhost:8032/mcp/

# Test HTTPS server (ignore certificate warnings)
curl -k https://localhost:8032/mcp/
```

## 📝 Script Features

- **Auto-detection**: Checks for required files and dependencies
- **Error handling**: Clear error messages and exit codes
- **SSL auto-generation**: Creates certificates from CSR if missing
- **Environment setup**: Activates virtual environment for standalone scripts
- **User-friendly**: Clear status messages and instructions

## 🔒 Security Notes

- Scripts use self-signed certificates for development
- For production, use certificates from a trusted CA
- The `-k` flag in curl ignores certificate verification (development only)
- Consider using Let's Encrypt for production certificates

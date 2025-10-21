# Docker Compose Management Scripts

This directory contains convenient shell scripts for managing the MITRE ATT&CK MCP Server using Docker Compose with build and up/down operations.

## 📋 Available Scripts

### HTTP Server Management
- **`docker_compose.sh`** - Manage HTTP server with Docker Compose

### HTTPS Server Management  
- **`docker_compose_ssl.sh`** - Manage HTTPS server with Docker Compose and SSL

## 🚀 Quick Start

### HTTP Server
```bash
# Start HTTP server (with build)
./docker_compose.sh up

# Start HTTP server in background
./docker_compose.sh up --detached

# Start without rebuilding
./docker_compose.sh up --no-build

# Stop HTTP server
./docker_compose.sh down
```

### HTTPS Server
```bash
# Start HTTPS server (with build)
./docker_compose_ssl.sh up

# Start HTTPS server in background
./docker_compose_ssl.sh up --detached

# Start without rebuilding
./docker_compose_ssl.sh up --no-build

# Stop HTTPS server
./docker_compose_ssl.sh down
```

## 🔧 Command Options

### Commands
- **`up`** - Start the server (default action)
- **`down`** - Stop the server

### Options
- **`--no-build`** - Skip building the Docker image
- **`--detached`** - Run in background mode
- **`-d`** - Run in background mode (short form)
- **`--help`** or **`-h`** - Show help information

## 📁 Default Configuration

### HTTP Server (`docker_compose.sh`)
- **Compose file**: `docker-compose.yml`
- **URL**: http://localhost:8032/mcp/
- **Build**: Enabled by default
- **Mode**: Foreground by default

### HTTPS Server (`docker_compose_ssl.sh`)
- **Compose file**: `docker-compose.ssl.yml`
- **URL**: https://localhost:9443/mcp/
- **Build**: Enabled by default
- **Mode**: Foreground by default
- **SSL Certificate**: `ssl/hd_app_ssl_server.crt`
- **SSL Private Key**: `ssl/hd_app_ssl_server.key`

## 🔒 SSL Certificate Handling

The HTTPS script automatically handles SSL certificates:

1. **Check for existing certificates**
2. **Auto-generate from CSR** if certificates are missing
3. **Use default paths**: `ssl/hd_app_ssl_server.crt` and `ssl/hd_app_ssl_server.key`

## 📝 Usage Examples

### Basic Operations
```bash
# Start HTTP server
./docker_compose.sh up

# Start HTTPS server  
./docker_compose_ssl.sh up

# Stop servers
./docker_compose.sh down
./docker_compose_ssl.sh down
```

### Background Operations
```bash
# Start HTTP server in background
./docker_compose.sh up --detached
# or
./docker_compose.sh up -d

# Start HTTPS server in background
./docker_compose_ssl.sh up --detached
# or
./docker_compose_ssl.sh up -d

# Check running containers
docker ps

# Stop background servers
./docker_compose.sh down
./docker_compose_ssl.sh down
```

### Development Workflow
```bash
# First time setup (with build)
./docker_compose_ssl.sh up

# Subsequent runs (no build needed)
./docker_compose_ssl.sh up --no-build

# Quick restart
./docker_compose_ssl.sh down && ./docker_compose_ssl.sh up --no-build
```

## 🔍 Troubleshooting

### Common Issues

1. **"docker-compose.yml not found"**
   - Ensure you're in the project root directory
   - Check that `docker-compose.yml` exists

2. **"SSL certificate not found"**
   - The HTTPS script will auto-generate certificates
   - Or run `./generate_ssl_cert.sh` manually

3. **"Port 8032 already in use"**
   - Stop existing server: `./docker_compose.sh down`
   - Or kill process: `lsof -ti:8032 | xargs kill -9`

4. **"Docker not found"**
   - Install Docker Desktop
   - Ensure Docker is running

### Testing the Servers

```bash
# Test HTTP server
curl http://localhost:8032/mcp/

# Test HTTPS server (ignore certificate warnings)
curl -k https://localhost:9443/mcp/

# Check container status
docker ps
docker logs mitre-attack-mcp
```

## 🛠️ Advanced Usage

### Custom Build Options
```bash
# Force rebuild without cache
docker-compose build --no-cache
./docker_compose.sh up --no-build

# Build specific service
docker-compose build mitre-attack-mcp
./docker_compose.sh up --no-build
```

### Log Management
```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f mitre-attack-mcp

# View last 100 lines
docker-compose logs --tail=100
```

### Resource Management
```bash
# Check resource usage
docker stats

# Clean up unused resources
docker system prune

# Remove all containers and images
docker-compose down --rmi all
```

## 📚 Script Features

- **Auto-detection**: Checks for required files and dependencies
- **Error handling**: Clear error messages and exit codes
- **SSL auto-generation**: Creates certificates from CSR if missing
- **Flexible options**: Build control and background mode
- **User-friendly**: Clear status messages and help information
- **Consistent interface**: Same options for both HTTP and HTTPS scripts

## 🔒 Security Notes

- Scripts use self-signed certificates for development
- For production, use certificates from a trusted CA
- The `-k` flag in curl ignores certificate verification (development only)
- Consider using Let's Encrypt for production certificates

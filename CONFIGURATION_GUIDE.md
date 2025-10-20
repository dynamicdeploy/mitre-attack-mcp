# MITRE ATT&CK MCP Server - Configuration Guide

This guide provides comprehensive examples for configuring the MITRE ATT&CK MCP server for both local development and remote deployment.

## 🏠 Local Configuration

### Quick Start (Local Development)

```bash
# 1. Install dependencies
poetry install

# 2. Run with STDIO transport (for MCP clients)
python -m mitre_attack_mcp.server

# 3. Run with HTTP transport (for web access)
python start_server.py
```

### Local Configuration Examples

Run the interactive local configuration examples:

```bash
python examples/local_config.py
```

**Available local examples**:
1. **Basic STDIO Server** - Simple local development setup
2. **Custom Data Directory** - Use a specific directory for MITRE data
3. **Environment Variables** - Configure via environment variables
4. **Async Server** - Run server asynchronously
5. **Development Server** - Development setup with hot reload

### Local Configuration Options

| Option | Description | Example |
|--------|-------------|---------|
| `--data-dir` | Custom data directory | `python app.py --data-dir ~/Documents/mitre-data` |
| `--host` | Host to bind to | `python app.py --host 127.0.0.1` |
| `--port` | Port to bind to | `python app.py --port 8080` |
| `--workers` | Number of workers | `python app.py --workers 4` |

## 🌐 Remote Configuration

### Quick Start (Remote Deployment)

```bash
# 1. Start HTTP server
python start_server.py

# 2. Access remotely
curl http://your-server.com:8032/mcp/
```

### Remote Configuration Examples

Run the interactive remote configuration examples:

```bash
python examples/remote_config.py
```

**Available remote examples**:
1. **Basic HTTP Server** - Simple HTTP deployment
2. **Production Server** - Multi-worker production setup
3. **Docker Deployment** - Containerized deployment
4. **Cloud Deployment** - Railway, Render, Heroku
5. **Kubernetes Deployment** - K8s production setup
6. **Nginx Reverse Proxy** - Behind reverse proxy
7. **Authentication Server** - Secure remote access

## 🐳 Docker Deployment

### Basic Docker

```bash
# Build the image
docker build -t mitre-attack-mcp .

# Run the container
docker run -p 8032:8032 mitre-attack-mcp
```

### Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f examples/docker-compose.production.yml up -d
```

### Docker Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | `0.0.0.0` | Host to bind to |
| `MCP_PORT` | `8032` | Port to bind to |
| `MCP_DATA_DIR` | `/app/data` | Data directory (Docker) |
| `MCP_WORKERS` | `1` | Number of workers |

## ☸️ Kubernetes Deployment

### Basic Kubernetes

```bash
# Apply the deployment
kubectl apply -f examples/kubernetes-deployment.yaml

# Check status
kubectl get pods
kubectl get services
```

### Kubernetes Configuration

The Kubernetes deployment includes:
- **Deployment**: 3 replicas with resource limits
- **Service**: LoadBalancer type for external access
- **PVC**: Persistent volume for data storage
- **Health Checks**: Liveness and readiness probes

## ☁️ Cloud Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render

Create `render.yaml`:
```yaml
services:
  - type: web
    name: mitre-attack-mcp
    env: python
    buildCommand: pip install -e .
    startCommand: python start_server.py
    envVars:
      - key: MCP_WORKERS
        value: 2
```

### Heroku

Create `Procfile`:
```
web: python start_server.py
```

## 🔐 Authentication Configuration

### Bearer Token Authentication

```python
# Set environment variable
export MCP_AUTH_TOKEN="your-secret-token"

# Start server
python start_server.py
```

### OAuth Authentication

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider

# Configure OAuth
auth = GitHubProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    issuer_url="https://your-server.com",
    base_url="https://your-server.com"
)

# Create authenticated server
mcp = FastMCP("MITRE ATT&CK Server", auth=auth)
```

## 🔀 Reverse Proxy Configuration

### Nginx Configuration

```nginx
upstream mitre_attack_mcp {
    server mitre-attack-mcp:8032;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location /mcp/ {
        proxy_pass http://mitre_attack_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Apache Configuration

```apache
<VirtualHost *:443>
    ServerName your-domain.com
    
    ProxyPreserveHost On
    ProxyPass /mcp/ http://localhost:8032/mcp/
    ProxyPassReverse /mcp/ http://localhost:8032/mcp/
</VirtualHost>
```

## 📊 Monitoring and Health Checks

### Health Check Endpoint

```bash
# Check server health
curl http://localhost:8032/mcp/

# Expected response: MCP server information
```

### Monitoring Configuration

```python
# Add custom health check
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({
        "status": "healthy",
        "service": "mitre-attack-mcp",
        "version": "1.0.2"
    })
```

## 🔧 Environment Variables Reference

### Server Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | `0.0.0.0` | Host to bind the server to |
| `MCP_PORT` | `8032` | Port to bind the server to |
| `MCP_PATH` | `/mcp/` | Custom path for the MCP endpoint |
| `MCP_DATA_DIR` | `~/Documents/mitre-attack-data` | Path to MITRE ATT&CK data directory |
| `MCP_WORKERS` | `1` | Number of worker processes |
| `MCP_LOG_LEVEL` | `info` | Logging level (debug, info, warning, error) |

### Authentication

| Variable | Description |
|----------|-------------|
| `MCP_AUTH_TOKEN` | Bearer token for authentication |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |
| `JWT_SIGNING_KEY` | JWT signing key for OAuth |
| `TOKEN_ENCRYPTION_KEY` | Token encryption key |

### Cloud Platform Variables

| Platform | Variable | Description |
|----------|----------|-------------|
| Railway | `PORT` | Port assigned by Railway |
| Render | `PORT` | Port assigned by Render |
| Heroku | `PORT` | Port assigned by Heroku |
| Cloud Run | `PORT` | Port assigned by Cloud Run |

## 🚀 Production Best Practices

### Performance Optimization

```bash
# Multiple workers for better concurrency
python start_server.py --workers 4

# With environment variables
MCP_WORKERS=4 python start_server.py
```

### Security Configuration

```bash
# Use HTTPS in production
# Set up SSL certificates
# Configure authentication
export MCP_AUTH_TOKEN="your-secure-token"

# Use environment variables for secrets
export GITHUB_CLIENT_ID="your-client-id"
export GITHUB_CLIENT_SECRET="your-client-secret"
```

### Monitoring Setup

```bash
# Enable debug logging
MCP_LOG_LEVEL=debug python start_server.py

# Production logging
MCP_LOG_LEVEL=info python start_server.py
```

## 🧪 Testing Your Configuration

### Test Script

```bash
# Run comprehensive tests
python test_http_server.py
```

### Manual Testing

```bash
# Test HTTP endpoint
curl http://localhost:8032/mcp/

# Test with authentication
curl -H "Authorization: Bearer your-token" http://localhost:8032/mcp/
```

### Load Testing

```bash
# Install Apache Bench
# Test with multiple requests
ab -n 100 -c 10 http://localhost:8032/mcp/
```

## 📚 Additional Resources

- **README.md**: Complete project documentation
- **HTTP_DEPLOYMENT.md**: Detailed HTTP deployment guide
- **examples/**: Configuration examples for different scenarios
- **test_http_server.py**: Comprehensive test suite

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Use different port
   python start_server.py --port 8080
   ```

2. **Data download fails**:
   ```bash
   # Check internet connection
   # Data will retry on next startup
   ```

3. **Authentication errors**:
   ```bash
   # Check token configuration
   echo $MCP_AUTH_TOKEN
   ```

4. **Memory issues**:
   ```bash
   # Reduce workers
   MCP_WORKERS=1 python start_server.py
   ```

### Debug Mode

```bash
# Enable debug logging
MCP_LOG_LEVEL=debug python start_server.py

# Check server logs
tail -f /var/log/mitre-attack-mcp.log
```

## 📞 Support

For additional help:
1. Check the README.md for basic usage
2. Run the test suite: `python test_http_server.py`
3. Review the examples in the `examples/` directory
4. Check the troubleshooting section above

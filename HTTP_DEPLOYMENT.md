# MITRE ATT&CK MCP HTTP Server

This document explains how to deploy the MITRE ATT&CK MCP server as an HTTP service using the FastMCP ASGI approach.

## Overview

The HTTP server makes your MITRE ATT&CK MCP server accessible over the network, allowing multiple clients to connect simultaneously and enabling integration with cloud-based LLM applications.

## Quick Start

### 1. Install Dependencies

```bash
# Install uvicorn for HTTP server
pip install uvicorn

# Or install all dependencies
poetry install
```

### 2. Run the Server

```bash
# Simple startup
python start_server.py

# Or with custom configuration
python app.py --host 0.0.0.0 --port 8032 --path /mcp/
```

### 3. Access the Server

Your server will be available at:
- **MCP Endpoint**: `http://localhost:8032/mcp/`
- **Health Check**: `http://localhost:8032/mcp/` (returns MCP server info)

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | `0.0.0.0` | Host to bind the server to |
| `MCP_PORT` | `8032` | Port to bind the server to |
| `MCP_PATH` | `/mcp/` | Custom path for the MCP endpoint |
| `MCP_DATA_DIR` | `~/Documents/mitre-attack-data` | Path to MITRE ATT&CK data directory |
| `MCP_WORKERS` | `1` | Number of worker processes |

### Command Line Options

```bash
python app.py --help

Options:
  --data-dir, -d    Location to store MITRE ATT&CK data
  --path, -p        Custom path for the MCP endpoint (default: /mcp/)
  --host           Host to bind the server to (default: 0.0.0.0)
  --port           Port to bind the server to (default: 8032)
  --workers        Number of worker processes (default: 1)
```

## Deployment Methods

### 1. Direct Python Execution

```bash
# Basic server
python start_server.py

# With custom settings
MCP_HOST=0.0.0.0 MCP_PORT=8080 python start_server.py
```

### 2. Using Uvicorn Directly

```bash
# Basic uvicorn
uvicorn app:app --host 0.0.0.0 --port 8032

# With multiple workers
uvicorn app:app --host 0.0.0.0 --port 8032 --workers 4

# With custom path
python -c "from app import create_app; app = create_app(custom_path='/api/mcp/')"
uvicorn app:app --host 0.0.0.0 --port 8032
```

### 3. Docker Deployment

```bash
# Build and run with Docker
docker build -t mitre-attack-mcp .
docker run -p 8032:8032 mitre-attack-mcp

# Or use docker-compose
docker-compose up -d
```

### 4. Production Deployment

For production, consider these options:

```bash
# Multiple workers for better performance
uvicorn app:app --host 0.0.0.0 --port 8032 --workers 4

# With Gunicorn (if you prefer)
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8032
```

## Server Features

### Automatic Data Management

- **Auto-download**: MITRE ATT&CK data is automatically downloaded on first run
- **Data persistence**: Data is cached locally for faster subsequent starts
- **Multi-domain support**: Enterprise, Mobile, and ICS domains are all supported

### Health Monitoring

The server includes built-in health checks:

```bash
# Check if server is running
curl http://localhost:8032/mcp/

# The endpoint returns MCP server information
```

### Custom Paths

You can customize the MCP endpoint path:

```python
# Custom path example
app = create_app(custom_path="/api/mcp/")
# Server will be available at: http://localhost:8032/api/mcp/
```

## Integration Examples

### With Existing Web Applications

```python
from fastapi import FastAPI
from app import create_app

# Your existing FastAPI app
main_app = FastAPI()

# Mount the MCP server
mcp_app = create_app(custom_path="/mcp/")
main_app.mount("/api", mcp_app)
```

### With Authentication

```python
from fastmcp import FastMCP
from fastmcp.server.auth import BearerTokenAuth

# Add authentication to your MCP server
auth = BearerTokenAuth(token="your-secret-token")
mcp = FastMCP("MITRE ATT&CK Server", auth=auth)
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Use a different port
   python app.py --port 8080
   ```

2. **Data download fails**
   ```bash
   # Check internet connection and try again
   # Data will be retried on next startup
   ```

3. **Import errors**
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate
   pip install -e .
   ```

### Logs and Debugging

```bash
# Run with debug logging
uvicorn app:app --host 0.0.0.0 --port 8032 --log-level debug

# Check server status
curl -v http://localhost:8032/mcp/
```

## Security Considerations

For production deployment:

1. **Use HTTPS**: Deploy behind a reverse proxy with SSL
2. **Authentication**: Add authentication for remote access
3. **Firewall**: Restrict access to necessary ports only
4. **Environment variables**: Store sensitive configuration in environment variables

## Performance Tuning

- **Multiple workers**: Use `--workers 4` for better concurrency
- **Data caching**: MITRE ATT&CK data is cached locally after first download
- **Memory usage**: Each worker process loads the full MITRE ATT&CK dataset

## Monitoring

The server provides several endpoints for monitoring:

- **Health check**: `GET /mcp/` - Returns server status
- **MCP endpoint**: `POST /mcp/` - Main MCP protocol endpoint

## Next Steps

- Configure authentication for production use
- Set up monitoring and logging
- Deploy to your preferred hosting platform
- Configure reverse proxy for HTTPS

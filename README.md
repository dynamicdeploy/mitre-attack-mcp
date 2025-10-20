# MITRE ATT&CK MCP Server

A Model Context Protocol (MCP) server that provides access to the MITRE ATT&CK knowledge base. This server allows AI assistants and other MCP clients to query and interact with MITRE ATT&CK data programmatically.

## Features

- 🔍 **Comprehensive ATT&CK Data Access**: Query techniques, tactics, groups, software, campaigns, and more
- 🌐 **Multiple Domains**: Support for Enterprise, Mobile, and ICS domains
- 🚀 **HTTP Deployment**: Deploy as a remote HTTP service for network access
- 💻 **Local Development**: Run locally with STDIO transport for development
- 🐳 **Docker Support**: Containerized deployment with Docker and Docker Compose
- ☸️ **Kubernetes Ready**: Production-ready Kubernetes deployment configurations
- 🔐 **Authentication**: Support for secure remote access
- 📊 **Layer Generation**: Generate ATT&CK Navigator layers programmatically
- 🤖 **AI-Powered Prompts**: Pre-built prompt templates for common threat intelligence tasks
- 🎯 **Use Case Examples**: Based on real-world threat intelligence scenarios

## Quick Start

### Local Development

1. **Install dependencies**:
```bash
   poetry install
   ```

2. **Run the server locally**:
   ```bash
   # STDIO transport (for MCP clients)
   python -m mitre_attack_mcp.server
   
   # HTTP transport (for web access)
   python http_server.py
   ```

3. **Test the server**:
   ```bash
   # Test HTTP endpoint
   curl http://localhost:8032/mcp/
   ```

### 🚀 Quick Configuration Reference

| Setting | Environment Variable | Default | Description |
|---------|---------------------|---------|-------------|
| **Data Directory** | `MCP_DATA_DIR` | Auto-detected | Where MITRE ATT&CK data is stored |
| **Workers** | `MCP_WORKERS` | `1` | Number of worker processes |
| **Port** | `MCP_PORT` | `8032` | Server port |
| **Host** | `MCP_HOST` | `0.0.0.0` | Server host |

**Quick Examples:**
```bash
# Development (low memory)
MCP_WORKERS=1 python start_server.py

# Production (high performance)
MCP_WORKERS=4 MCP_DATA_DIR=/shared/data python start_server.py

# Custom data location
MCP_DATA_DIR=/custom/path python start_server.py
```

### HTTP Deployment

1. **Start the HTTP server**:
   ```bash
   python http_server.py
   ```

2. **Access the server**:
   - **MCP Endpoint**: `http://localhost:8032/`
   - **Health Check**: `http://localhost:8032/`

## MCP Client Configuration

### Claude Desktop Configuration

Add this to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "mitre-attack": {
      "command": "python",
      "args": [
        "-m",
        "mitre_attack_mcp.server"
      ],
      "env": {
        "MCP_DATA_DIR": "~/Documents/mitre-attack-data"
      }
    }
  }
}
```

**File locations:**
- **Windows**: `C:\Users\[YourUsername]\AppData\Roaming\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

### Cursor Configuration

For Cursor, use the same configuration format as Claude Desktop.

### Remote HTTP Configuration

For remote HTTP access:

```json
{
  "mcpServers": {
    "mitre-attack-remote": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-everything"
      ],
      "env": {
        "MCP_SERVER_URL": "http://localhost:8032/mcp/"
      }
    }
  }
}
```

## Configuration Examples

### Local Configuration

The server supports various local configuration options:

```python
# examples/local_config.py
python examples/local_config.py
```

**Available local examples**:
1. Basic STDIO Server
2. Custom Data Directory
3. Environment Variables Configuration
4. Async Server Configuration
5. Development Server with Hot Reload

### Remote Configuration

For remote deployment, use the HTTP configuration examples:

```python
# examples/remote_config.py
python examples/remote_config.py
```

**Available remote examples**:
1. Basic HTTP Server
2. Production Server (multiple workers)
3. Docker Deployment
4. Cloud Deployment (Railway, Render, Heroku)
5. Kubernetes Deployment
6. Nginx Reverse Proxy
7. Authentication Server

### MCP Client Configuration Guide

For detailed configuration instructions, see [MCP_CLIENT_CONFIGURATION.md](MCP_CLIENT_CONFIGURATION.md).

## Deployment Options

### 1. Docker Deployment

**Basic Docker**:
```bash
docker build -t mitre-attack-mcp .
docker run -p 8032:8032 mitre-attack-mcp
```

**Docker Compose**:
```bash
# Development
docker-compose up -d

# Production
docker-compose -f examples/docker-compose.production.yml up -d
```

### 2. Kubernetes Deployment

```bash
kubectl apply -f examples/kubernetes-deployment.yaml
```

### 3. Cloud Deployment

**Railway**:
```bash
railway login
railway init
railway up
```

**Render**:
```yaml
# render.yaml
services:
  - type: web
    name: mitre-attack-mcp
    env: python
    buildCommand: pip install -e .
    startCommand: python start_server.py
```

### 4. Nginx Reverse Proxy

```bash
# Copy nginx configuration
cp examples/nginx.conf /etc/nginx/nginx.conf

# Start with SSL
docker-compose -f examples/docker-compose.production.yml up -d
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_HOST` | `0.0.0.0` | Host to bind the server to |
| `MCP_PORT` | `8032` | Port to bind the server to |
| `MCP_PATH` | `/mcp/` | Custom path for the MCP endpoint |
| `MCP_DATA_DIR` | Auto-detected | Path to MITRE ATT&CK data directory |
| `MCP_WORKERS` | `1` | Number of worker processes |
| `MCP_LOG_LEVEL` | `info` | Logging level |
| `MCP_AUTH_TOKEN` | None | Authentication token for secure access |

### 📁 MCP_DATA_DIR - Data Storage Configuration

The `MCP_DATA_DIR` environment variable controls where MITRE ATT&CK STIX data files are stored and loaded from.

#### **Default Behavior:**
- **All Platforms**: `~/Documents/mitre-attack-data`

#### **Data Structure:**
```
{MCP_DATA_DIR}/
└── v{version}/
    ├── enterprise-attack.json
    ├── mobile-attack.json
    └── ics-attack.json
```

#### **Usage Examples:**
```bash
# Use custom data directory
MCP_DATA_DIR=/custom/path python start_server.py

# Docker with persistent data
docker run -v /host/data:/app/data -e MCP_DATA_DIR=/app/data mitre-attack-mcp
```

#### **Important Notes:**
- Data is automatically downloaded on first run if not present
- Each domain (enterprise, mobile, ics) requires ~50-100MB of storage
- Data is stored in your Documents folder for easy access
- Custom paths must be writable by the server process
- Data persists between server restarts

### ⚙️ MCP_WORKERS - Performance Configuration

The `MCP_WORKERS` environment variable controls the number of Uvicorn worker processes for handling concurrent requests.

#### **Performance Characteristics:**

| Workers | Memory Usage | Concurrency | Use Case |
|---------|-------------|-------------|----------|
| `1` | ~500MB | Low | Development, testing |
| `2-4` | ~1-2GB | Medium | Small production |
| `4+` | ~2GB+ | High | Large production |

#### **Usage Examples:**
```bash
# Development (single process)
MCP_WORKERS=1 python start_server.py

# Production (multiple processes)
MCP_WORKERS=4 python start_server.py

# Auto-scale based on CPU cores
MCP_WORKERS=0 python start_server.py
```

#### **⚠️ Important Limitations:**

1. **Memory Overhead**: Each worker loads the full MITRE ATT&CK dataset (~500MB per worker)
2. **No Data Sharing**: Workers operate independently - no coordination
3. **Startup Time**: Each worker downloads/loads data independently
4. **Resource Usage**: Memory usage scales linearly with worker count

#### **Recommended Settings:**

**Development:**
```bash
MCP_WORKERS=1  # Single process, lower memory usage
```

**Production (Small):**
```bash
MCP_WORKERS=2  # Good balance of performance and memory
```

**Production (Large):**
```bash
MCP_WORKERS=4  # High concurrency, requires 2GB+ RAM
```

#### **Memory Requirements:**
- **Minimum**: 1GB RAM (1 worker)
- **Recommended**: 2GB RAM (2-4 workers)
- **High Performance**: 4GB+ RAM (4+ workers)

#### **Monitoring:**
```bash
# Check memory usage
ps aux | grep start_server

# Monitor worker processes
htop -p $(pgrep -f start_server)
```

## Available Tools

The server provides numerous tools for querying MITRE ATT&CK data:

### Basic Object Lookup
- `get_object_by_attack_id` - Get object by ATT&CK ID
- `get_object_by_stix_id` - Get object by STIX ID
- `get_objects_by_name` - Get objects by name
- `get_objects_by_content` - Get objects by description content

### Threat Actor Groups
- `get_groups_by_alias` - Get groups by alias
- `get_techniques_used_by_group` - Get techniques used by group
- `get_software_used_by_group` - Get software used by group
- `get_campaigns_attributed_to_group` - Get campaigns attributed to group

### Software
- `get_software_by_alias` - Get software by alias
- `get_software_using_technique` - Get software using technique
- `get_techniques_used_by_software` - Get techniques used by software

### Techniques
- `get_techniques_by_platform` - Get techniques by platform
- `get_techniques_by_tactic` - Get techniques by tactic
- `get_parent_technique_of_subtechnique` - Get parent technique
- `get_subtechniques_of_technique` - Get subtechniques

### Campaigns
- `get_campaigns_using_technique` - Get campaigns using technique
- `get_techniques_used_by_campaign` - Get techniques used by campaign
- `get_campaigns_by_alias` - Get campaigns by alias

### Data Sources & Detection
- `get_datacomponents_detecting_technique` - Get data components detecting technique
- `get_techniques_detected_by_datacomponent` - Get techniques detected by data component

### Layer Generation
- `generate_layer` - Generate ATT&CK Navigator layer
- `get_layer_metadata` - Get layer metadata

### AI-Powered Prompts
Based on real-world threat intelligence use cases from the [MITRE ATT&CK MCP Server blog](https://www.remyjaspers.com/blog/mitre_attack_mcp_server/):

- `analyze_malware(malware_name)` - Analyze malware and find associated techniques, groups, and campaigns
- `compare_ransomware(ransomware1, ransomware2)` - Compare ransomware families and find overlapping techniques
- `extract_ttps_from_text(text_content)` - Extract TTPs from unstructured text and create ATT&CK Navigator layers
- `threat_actor_analysis(group_name)` - Perform comprehensive threat actor group analysis
- `technique_analysis(technique_id)` - Analyze specific ATT&CK techniques in detail
- `campaign_investigation(campaign_name)` - Investigate campaigns and their TTPs
- `sector_analysis(sector)` - Analyze threats targeting specific sectors
- `rainbow_layer()` - Create colorful rainbow ATT&CK Navigator layers

## Usage Examples

### Local MCP Client

```python
# Connect to local server
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async with stdio_client(StdioServerParameters(
    command="python",
    args=["-m", "mitre_attack_mcp.server"]
)) as (read, write):
    async with ClientSession(read, write) as session:
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {[tool.name for tool in tools.tools]}")
        
        # Get a technique
        result = await session.call_tool(
            "get_object_by_attack_id",
            arguments={
                "attack_id": "T1055",
                "stix_type": "attack-pattern",
                "include_description": True
            }
        )
        print(result.content)
```

### Remote HTTP Client

```python
import requests

# Connect to remote server
response = requests.post(
    "http://your-server.com/mcp/",
    json={
        "method": "tools/call",
        "params": {
            "name": "get_object_by_attack_id",
            "arguments": {
                "attack_id": "T1055",
                "stix_type": "attack-pattern",
                "include_description": True
            }
        }
    }
)
print(response.json())
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd mitre-attack-mcp

# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
poetry run ruff check .
poetry run black .
```

### Adding New Tools

1. Add the tool function to `src/mitre_attack_mcp/server.py`
2. Use the `@mcp.tool()` decorator
3. Document the function with proper docstring
4. Test the tool locally
5. Update documentation

### Testing

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_server.py

# Run with coverage
poetry run pytest --cov=src
```

## Troubleshooting

### Common Issues

1. **Data download fails**:
   ```bash
   # Check internet connection
   # Data will be retried on next startup
   ```

2. **Port already in use**:
   ```bash
   # Use a different port
   python start_server.py --port 8080
   ```

3. **Import errors**:
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate
   pip install -e .
   ```

### MCP_DATA_DIR Issues

4. **Permission denied errors**:
   ```bash
   # Check directory permissions
   ls -la /path/to/data/directory
   
   # Fix permissions
   chmod 755 /path/to/data/directory
   chown $USER:$USER /path/to/data/directory
   ```

5. **Data not loading**:
   ```bash
   # Check if data exists
   ls -la $MCP_DATA_DIR/v*/enterprise-attack.json
   
   # Force re-download
   rm -rf $MCP_DATA_DIR/v*
   python start_server.py
   ```

6. **Custom data directory not working**:
   ```bash
   # Verify path exists and is writable
   mkdir -p /custom/path
   touch /custom/path/test.txt && rm /custom/path/test.txt
   
   # Set environment variable
   export MCP_DATA_DIR=/custom/path
   python start_server.py
   ```

### MCP_WORKERS Issues

7. **High memory usage**:
   ```bash
   # Check memory usage
   ps aux | grep start_server | awk '{print $4, $6}'
   
   # Reduce workers
   MCP_WORKERS=1 python start_server.py
   ```

8. **Server not starting with multiple workers**:
   ```bash
   # Check system resources
   free -h
   nproc
   
   # Start with fewer workers
   MCP_WORKERS=2 python start_server.py
   ```

9. **Slow startup with multiple workers**:
   ```bash
   # Each worker downloads data independently
   # Pre-download data to speed up startup
   MCP_DATA_DIR=/shared/data python start_server.py
   ```

### Performance Optimization

10. **Optimize for production**:
    ```bash
    # Use shared data directory
    MCP_DATA_DIR=/shared/mitre-data
    
    # Start with appropriate worker count
    MCP_WORKERS=2  # For 2GB RAM
    MCP_WORKERS=4  # For 4GB+ RAM
    ```

11. **Monitor resource usage**:
    ```bash
    # Monitor memory
    watch -n 1 'ps aux | grep start_server'
    
    # Monitor CPU
    htop -p $(pgrep -f start_server)
    ```

### Logs and Debugging

```bash
# Run with debug logging
python start_server.py --log-level debug

# Check server status
curl -v http://localhost:8032/mcp/

# Check worker processes
ps aux | grep start_server
```

## Security Considerations

For production deployment:

1. **Use HTTPS**: Deploy behind a reverse proxy with SSL
2. **Authentication**: Add authentication for remote access
3. **Firewall**: Restrict access to necessary ports only
4. **Environment variables**: Store sensitive configuration securely

## Performance Tuning

- **Multiple workers**: Use `--workers 4` for better concurrency
- **Data caching**: MITRE ATT&CK data is cached locally after first download
- **Memory usage**: Each worker process loads the full MITRE ATT&CK dataset

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [MITRE ATT&CK](https://attack.mitre.org/) for the comprehensive threat intelligence framework
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- [FastMCP](https://gofastmcp.com/) for the MCP server framework
# MCP Client Configuration Guide

This guide provides JSON configuration examples for connecting to the MITRE ATT&CK MCP server from various MCP clients like Claude Desktop and Cursor.

## 🖥️ Claude Desktop Configuration

### Local MCP Server (STDIO)

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

### Remote MCP Server (HTTP)

For remote HTTP access, you'll need to use an MCP client that supports HTTP transport:

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

## 🖱️ Cursor Configuration

### Local MCP Server (STDIO)

Add this to your Cursor MCP configuration:

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

### Remote MCP Server (HTTP)

For remote HTTP access in Cursor:

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

## 🚀 Starting the MCP Server

### Local Development (STDIO)

```bash
# Install dependencies
poetry install

# Run the MCP server locally
python -m mitre_attack_mcp.server
```

### Remote Development (HTTP)

```bash
# Start the HTTP server
python start_server.py

# Server will be available at http://localhost:8032/mcp/
```

## 📋 Available Prompts

The MCP server now includes the following prompt functions based on the [blog article examples](https://www.remyjaspers.com/blog/mitre_attack_mcp_server/):

### 1. `analyze_malware(malware_name: str)`
Analyze malware and find associated techniques, groups, and campaigns.

**Example**: "Analyze the malware 'ShellTea'"

### 2. `compare_ransomware(ransomware1: str, ransomware2: str)`
Compare two ransomware families and find overlapping techniques.

**Example**: "Compare Akira and Babuk ransomware"

### 3. `extract_ttps_from_text(text_content: str)`
Extract TTPs from unstructured text and create an ATT&CK Navigator layer.

**Example**: "Extract TTPs from this CISA advisory text"

### 4. `threat_actor_analysis(group_name: str)`
Perform comprehensive threat actor group analysis.

**Example**: "Analyze the Turla threat actor group"

### 5. `technique_analysis(technique_id: str)`
Analyze a specific ATT&CK technique in detail.

**Example**: "Analyze technique T1055"

### 6. `campaign_investigation(campaign_name: str)`
Investigate a specific campaign and its TTPs.

**Example**: "Investigate campaign C0026"

### 7. `sector_analysis(sector: str)`
Analyze threats targeting a specific sector.

**Example**: "Analyze threats to the healthcare sector"

### 8. `rainbow_layer()`
Create a colorful rainbow ATT&CK Navigator layer.

**Example**: "Generate a rainbow-colored ATT&CK layer"

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_DATA_DIR` | `~/Documents/mitre-attack-data` | Path to MITRE ATT&CK data directory |
| `MCP_HOST` | `0.0.0.0` | Host for HTTP server |
| `MCP_PORT` | `8032` | Port for HTTP server |
| `MCP_PATH` | `/mcp/` | Path for MCP endpoint |

### Custom Data Directory

```json
{
  "mcpServers": {
    "mitre-attack": {
      "command": "python",
      "args": [
        "-m",
        "mitre_attack_mcp.server",
        "/path/to/custom/data/directory"
      ]
    }
  }
}
```

## 🌐 Remote Server Setup

### 1. Start the HTTP Server

```bash
# Basic HTTP server
python start_server.py

# With custom configuration
python app.py --host 0.0.0.0 --port 8032 --workers 4
```

### 2. Test the Server

```bash
# Test the MCP endpoint
curl http://localhost:8032/mcp/

# Test with authentication (if configured)
curl -H "Authorization: Bearer your-token" http://localhost:8032/mcp/
```

### 3. Configure Client

Use the remote configuration in your MCP client:

```json
{
  "mcpServers": {
    "mitre-attack-remote": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-everything"
      ],
      "env": {
        "MCP_SERVER_URL": "http://your-server:8032/mcp/"
      }
    }
  }
}
```

## 🔐 Authentication

### Bearer Token Authentication

```bash
# Set authentication token
export MCP_AUTH_TOKEN="your-secret-token"

# Start server with authentication
python start_server.py
```

### OAuth Authentication

```python
# Configure OAuth in your server
from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider

auth = GitHubProvider(
    client_id="your-client-id",
    client_secret="your-client-secret",
    issuer_url="https://your-server.com",
    base_url="https://your-server.com"
)

mcp = FastMCP("MITRE ATT&CK Server", auth=auth)
```

## 🧪 Testing Your Configuration

### Test Local Server

```bash
# Test the MCP server
python test_http_server.py

# Test with examples
python examples/local_config.py
python examples/remote_config.py
```

### Test Remote Server

```bash
# Test HTTP endpoint
curl http://localhost:8032/mcp/

# Test with MCP client
npx @modelcontextprotocol/server-everything --url http://localhost:8032/mcp/
```

## 📚 Use Cases from Blog Article

Based on the [blog article examples](https://www.remyjaspers.com/blog/mitre_attack_mcp_server/), here are the key use cases:

### 1. General Question Answering
- **Question**: "What do you know about ShellTea malware?"
- **Tools Used**: `get_software_by_alias`, `get_object_by_content`
- **Result**: Comprehensive malware analysis with associated groups

### 2. Finding Specifics
- **Question**: "What campaign has overlap with Turla activity?"
- **Tools Used**: `get_groups_by_alias`, `get_all_campaigns`
- **Result**: Campaign C0026 with Turla connections

### 3. Generating ATT&CK Navigator Layers
- **Question**: "Generate a navigator layer for Akira and Babuk ransomware"
- **Tools Used**: `generate_layer`, `get_layer_metadata`
- **Result**: Downloadable JSON layer with overlapping techniques

### 4. Extracting TTPs from Unstructured Data
- **Question**: "Extract TTPs from CISA Advisory on Medusa Ransomware"
- **Tools Used**: Various technique lookup tools
- **Result**: Structured ATT&CK Navigator layer from unstructured text

## 🆘 Troubleshooting

### Common Issues

1. **Server won't start**:
   ```bash
   # Check dependencies
   poetry install
   
   # Check Python path
   which python
   ```

2. **Data download fails**:
   ```bash
   # Check internet connection
   # Data will retry on next startup
   ```

3. **Client can't connect**:
   ```bash
   # Check server is running
   curl http://localhost:8032/mcp/
   
   # Check configuration
   cat ~/.config/claude/claude_desktop_config.json
   ```

4. **Authentication errors**:
   ```bash
   # Check token configuration
   echo $MCP_AUTH_TOKEN
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
1. Check the main README.md for basic usage
2. Run the test suite: `python test_http_server.py`
3. Review the examples in the `examples/` directory
4. Check the troubleshooting section above
5. Refer to the [original blog article](https://www.remyjaspers.com/blog/mitre_attack_mcp_server/) for use case examples

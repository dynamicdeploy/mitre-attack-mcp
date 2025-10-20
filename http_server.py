#!/usr/bin/env python3
"""
HTTP wrapper for MITRE ATT&CK MCP Server
Simple HTTP wrapper around the existing server.py
"""

import uvicorn
from mitre_attack_mcp.server import mcp, load_stix_data, get_default_data_dir
from fastmcp import FastMCP

mcp = FastMCP("mitre-attack")

# Initialize MITRE ATT&CK data
print("Loading MITRE ATT&CK data...")
data_path = get_default_data_dir()
load_stix_data(data_path)
print("MITRE ATT&CK data loaded successfully!")

if __name__ == "__main__":
    print("🚀 Starting MITRE ATT&CK MCP HTTP Server")
    print("📍 Server: http://localhost:8032/mcp/")
    print("🔧 All MITRE ATT&CK tools and prompts available!")
    
    # Use the HTTP app from the mcp server
    # Create ASGI application
    app = mcp.http_app()
    # Run the ASGI application with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8032)

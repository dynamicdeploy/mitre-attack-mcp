#!/usr/bin/env python3
"""
Local MITRE ATT&CK MCP Server Configuration Examples

This file demonstrates various ways to configure and run the MITRE ATT&CK MCP server
for local development and testing.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the parent directory to the path so we can import the server
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mitre_attack_mcp.server import mcp, download_stix_data, load_stix_data


def example_1_stdio_server():
    """
    Example 1: Basic STDIO Server (Local Development)
    
    This is the simplest way to run the MCP server locally.
    Perfect for development and testing with MCP clients.
    """
    print("🚀 Example 1: Basic STDIO Server")
    print("=" * 50)
    
    # The server is already configured in server.py
    # Just run it with STDIO transport
    print("Starting MITRE ATT&CK MCP server with STDIO transport...")
    print("This server will communicate via stdin/stdout")
    print("Press Ctrl+C to stop")
    
    # Run the server
    mcp.run(transport="stdio")


def example_2_custom_data_directory():
    """
    Example 2: Custom Data Directory
    
    Configure the server to use a specific directory for MITRE ATT&CK data.
    """
    print("🚀 Example 2: Custom Data Directory")
    print("=" * 50)
    
    # Set custom data directory
    custom_data_dir = os.path.expanduser("~/Documents/mitre-attack-data")
    
    print(f"Using custom data directory: {custom_data_dir}")
    
    # Download data to custom location
    print("Downloading MITRE ATT&CK data...")
    download_stix_data(custom_data_dir)
    
    # Load data from custom location
    print("Loading MITRE ATT&CK data...")
    loaded_domains = load_stix_data(custom_data_dir)
    
    if loaded_domains:
        print(f"✅ Loaded data for domains: {', '.join(loaded_domains)}")
    else:
        print("❌ Failed to load data")
        return
    
    # Run the server
    print("Starting server...")
    mcp.run(transport="stdio")


def example_3_environment_variables():
    """
    Example 3: Configuration via Environment Variables
    
    Configure the server using environment variables for flexible deployment.
    """
    print("🚀 Example 3: Environment Variables Configuration")
    print("=" * 50)
    
    # Set environment variables
    os.environ["MCP_DATA_DIR"] = os.path.expanduser("~/Documents/mitre-attack-data")
    os.environ["MCP_LOG_LEVEL"] = "DEBUG"
    
    # Get configuration from environment
    data_dir = os.environ.get("MCP_DATA_DIR", "~/Documents/mitre-attack-data")
    log_level = os.environ.get("MCP_LOG_LEVEL", "INFO")
    
    print(f"Data directory: {data_dir}")
    print(f"Log level: {log_level}")
    
    # Initialize data
    print("Initializing MITRE ATT&CK data...")
    download_stix_data(data_dir)
    loaded_domains = load_stix_data(data_dir)
    
    if loaded_domains:
        print(f"✅ Loaded data for domains: {', '.join(loaded_domains)}")
        print("Starting server...")
        mcp.run(transport="stdio")
    else:
        print("❌ Failed to load data")


def example_4_async_server():
    """
    Example 4: Async Server Configuration
    
    Run the server asynchronously for more control over the server lifecycle.
    """
    print("🚀 Example 4: Async Server Configuration")
    print("=" * 50)
    
    async def run_async_server():
        """Run the server asynchronously"""
        print("Starting async MITRE ATT&CK MCP server...")
        
        # Initialize data
        data_dir = os.path.expanduser("~/Documents/mitre-attack-data")
        download_stix_data(data_dir)
        loaded_domains = load_stix_data(data_dir)
        
        if not loaded_domains:
            print("❌ Failed to load MITRE ATT&CK data")
            return
        
        print(f"✅ Loaded data for domains: {', '.join(loaded_domains)}")
        
        # Run the server asynchronously
        await mcp.run_stdio_async()
    
    # Run the async server
    try:
        asyncio.run(run_async_server())
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")


def example_5_development_server():
    """
    Example 5: Development Server with Hot Reload
    
    Configure the server for development with automatic reloading.
    """
    print("🚀 Example 5: Development Server")
    print("=" * 50)
    
    # Development configuration
    dev_config = {
        "data_dir": os.path.expanduser("~/Documents/mitre-attack-data"),
        "log_level": "DEBUG",
        "auto_reload": True,
        "debug": True
    }
    
    print("Development configuration:")
    for key, value in dev_config.items():
        print(f"  {key}: {value}")
    
    # Set up development environment
    os.environ["PYTHONPATH"] = str(Path(__file__).parent.parent)
    os.environ["MCP_DEBUG"] = "true"
    
    # Initialize data
    print("Setting up development data...")
    download_stix_data(dev_config["data_dir"])
    loaded_domains = load_stix_data(dev_config["data_dir"])
    
    if loaded_domains:
        print(f"✅ Development server ready with domains: {', '.join(loaded_domains)}")
        print("Starting development server...")
        print("Note: In a real development setup, you'd use a tool like 'watchdog' for hot reloading")
        mcp.run(transport="stdio")
    else:
        print("❌ Failed to set up development environment")


def main():
    """Main function to run examples"""
    print("MITRE ATT&CK MCP Server - Local Configuration Examples")
    print("=" * 60)
    print()
    
    examples = {
        "1": ("Basic STDIO Server", example_1_stdio_server),
        "2": ("Custom Data Directory", example_2_custom_data_directory),
        "3": ("Environment Variables", example_3_environment_variables),
        "4": ("Async Server", example_4_async_server),
        "5": ("Development Server", example_5_development_server),
    }
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    print()
    choice = input("Select an example to run (1-5) or 'all' to run all: ").strip()
    
    if choice == "all":
        for name, func in examples.values():
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print('='*60)
            try:
                func()
            except KeyboardInterrupt:
                print("\n🛑 Example stopped by user")
            except Exception as e:
                print(f"❌ Error in {name}: {e}")
            print("\nPress Enter to continue to next example...")
            input()
    elif choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}")
        try:
            func()
        except KeyboardInterrupt:
            print("\n🛑 Example stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()

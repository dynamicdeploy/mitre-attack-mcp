#!/usr/bin/env python3
"""
Remote MITRE ATT&CK MCP Server Configuration Examples

This file demonstrates various ways to configure and deploy the MITRE ATT&CK MCP server
for remote access over HTTP.
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path
from typing import Optional

# Add the parent directory to the path so we can import the server
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app


def example_1_basic_http_server():
    """
    Example 1: Basic HTTP Server
    
    The simplest way to deploy the MCP server over HTTP.
    Perfect for internal tools and development.
    """
    print("🚀 Example 1: Basic HTTP Server")
    print("=" * 50)
    
    # Create the ASGI application
    app = create_app()
    
    print("Starting MITRE ATT&CK MCP HTTP server...")
    print("Server will be available at: http://localhost:8032")
    print("MCP endpoint: http://localhost:8032/mcp/")
    print("Press Ctrl+C to stop")
    
    # Run with uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8032,
        log_level="info"
    )


def example_2_production_server():
    """
    Example 2: Production Server Configuration
    
    Configure the server for production deployment with multiple workers,
    custom settings, and environment variables.
    """
    print("🚀 Example 2: Production Server")
    print("=" * 50)
    
    # Production configuration
    config = {
        "host": os.environ.get("MCP_HOST", "0.0.0.0"),
        "port": int(os.environ.get("MCP_PORT", "8032")),
        "workers": int(os.environ.get("MCP_WORKERS", "4")),
        "data_dir": os.environ.get("MCP_DATA_DIR", None),
        "log_level": os.environ.get("MCP_LOG_LEVEL", "info"),
    }
    
    print("Production configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Create the ASGI application
    app = create_app(data_path=config["data_dir"])
    
    print(f"\n🚀 Starting production server...")
    print(f"📍 Host: {config['host']}")
    print(f"🔌 Port: {config['port']}")
    print(f"👥 Workers: {config['workers']}")
    print(f"📁 Data Directory: {config['data_dir'] or 'Default cache directory'}")
    
    # Run with production settings
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        workers=config["workers"],
        log_level=config["log_level"],
        access_log=True,
    )


def example_3_docker_deployment():
    """
    Example 3: Docker Deployment Configuration
    
    Configure the server for Docker deployment with environment variables
    and volume mounts.
    """
    print("🚀 Example 3: Docker Deployment")
    print("=" * 50)
    
    # Docker configuration
    docker_config = {
        "host": "0.0.0.0",
        "port": 8032,
        "data_dir": "/app/data",
        "workers": 1,  # Single worker in container
        "log_level": "info",
    }
    
    print("Docker configuration:")
    for key, value in docker_config.items():
        print(f"  {key}: {value}")
    
    # Create the ASGI application
    app = create_app(data_path=docker_config["data_dir"])
    
    print(f"\n🐳 Starting Docker container...")
    print(f"📁 Data volume: {docker_config['data_dir']}")
    print(f"🔌 Exposed port: {docker_config['port']}")
    
    # Run the server
    uvicorn.run(
        app,
        host=docker_config["host"],
        port=docker_config["port"],
        workers=docker_config["workers"],
        log_level=docker_config["log_level"],
    )


def example_4_cloud_deployment():
    """
    Example 4: Cloud Deployment Configuration
    
    Configure the server for cloud platforms like Railway, Render, or Heroku.
    """
    print("🚀 Example 4: Cloud Deployment")
    print("=" * 50)
    
    # Cloud configuration - use environment variables
    cloud_config = {
        "host": "0.0.0.0",
        "port": int(os.environ.get("PORT", "8032")),  # Cloud platforms set PORT
        "workers": 1,  # Single worker for cloud platforms
        "data_dir": os.environ.get("MCP_DATA_DIR", None),
        "log_level": "info",
    }
    
    print("Cloud configuration:")
    for key, value in cloud_config.items():
        print(f"  {key}: {value}")
    
    # Create the ASGI application
    app = create_app(data_path=cloud_config["data_dir"])
    
    print(f"\n☁️  Starting cloud deployment...")
    print(f"🌐 Port: {cloud_config['port']} (from environment)")
    print(f"📁 Data: {cloud_config['data_dir'] or 'Default cache directory'}")
    
    # Run the server
    uvicorn.run(
        app,
        host=cloud_config["host"],
        port=cloud_config["port"],
        workers=cloud_config["workers"],
        log_level=cloud_config["log_level"],
    )


def example_5_kubernetes_deployment():
    """
    Example 5: Kubernetes Deployment Configuration
    
    Configure the server for Kubernetes deployment with health checks
    and resource limits.
    """
    print("🚀 Example 5: Kubernetes Deployment")
    print("=" * 50)
    
    # Kubernetes configuration
    k8s_config = {
        "host": "0.0.0.0",
        "port": 8032,
        "workers": int(os.environ.get("WORKERS", "2")),
        "data_dir": "/data/mitre-attack",
        "log_level": "info",
    }
    
    print("Kubernetes configuration:")
    for key, value in k8s_config.items():
        print(f"  {key}: {value}")
    
    # Create the ASGI application
    app = create_app(data_path=k8s_config["data_dir"])
    
    print(f"\n☸️  Starting Kubernetes deployment...")
    print(f"👥 Workers: {k8s_config['workers']}")
    print(f"📁 Persistent volume: {k8s_config['data_dir']}")
    print(f"🏥 Health check: http://localhost:{k8s_config['port']}/mcp/")
    
    # Run the server
    uvicorn.run(
        app,
        host=k8s_config["host"],
        port=k8s_config["port"],
        workers=k8s_config["workers"],
        log_level=k8s_config["log_level"],
    )


def example_6_nginx_reverse_proxy():
    """
    Example 6: Nginx Reverse Proxy Configuration
    
    Configure the server to work behind an Nginx reverse proxy.
    """
    print("🚀 Example 6: Nginx Reverse Proxy")
    print("=" * 50)
    
    # Nginx proxy configuration
    proxy_config = {
        "host": "127.0.0.1",  # Bind to localhost only
        "port": 8032,
        "workers": 4,
        "data_dir": None,
        "log_level": "info",
        "forwarded_allow_ips": "*",  # Allow forwarded headers
    }
    
    print("Nginx proxy configuration:")
    for key, value in proxy_config.items():
        print(f"  {key}: {value}")
    
    # Create the ASGI application
    app = create_app(data_path=proxy_config["data_dir"])
    
    print(f"\n🔀 Starting behind Nginx proxy...")
    print(f"🔒 Internal port: {proxy_config['port']}")
    print(f"👥 Workers: {proxy_config['workers']}")
    print(f"🌐 External access: https://your-domain.com/mcp/")
    
    # Run the server
    uvicorn.run(
        app,
        host=proxy_config["host"],
        port=proxy_config["port"],
        workers=proxy_config["workers"],
        log_level=proxy_config["log_level"],
        forwarded_allow_ips=proxy_config["forwarded_allow_ips"],
    )


def example_7_authentication_server():
    """
    Example 7: Server with Authentication
    
    Configure the server with authentication for secure remote access.
    """
    print("🚀 Example 7: Authentication Server")
    print("=" * 50)
    
    # Authentication configuration
    auth_config = {
        "host": "0.0.0.0",
        "port": 8032,
        "workers": 2,
        "data_dir": None,
        "log_level": "info",
        "auth_token": os.environ.get("MCP_AUTH_TOKEN", None),
    }
    
    print("Authentication configuration:")
    for key, value in auth_config.items():
        if key == "auth_token":
            print(f"  {key}: {'***' if value else 'None'}")
        else:
            print(f"  {key}: {value}")
    
    if not auth_config["auth_token"]:
        print("⚠️  Warning: No authentication token set!")
        print("   Set MCP_AUTH_TOKEN environment variable for security")
    
    # Create the ASGI application
    app = create_app(data_path=auth_config["data_dir"])
    
    print(f"\n🔐 Starting authenticated server...")
    print(f"🔑 Auth: {'Enabled' if auth_config['auth_token'] else 'Disabled'}")
    print(f"🌐 Endpoint: http://localhost:{auth_config['port']}/mcp/")
    
    # Run the server
    uvicorn.run(
        app,
        host=auth_config["host"],
        port=auth_config["port"],
        workers=auth_config["workers"],
        log_level=auth_config["log_level"],
    )


def main():
    """Main function to run examples"""
    print("MITRE ATT&CK MCP Server - Remote Configuration Examples")
    print("=" * 60)
    print()
    
    examples = {
        "1": ("Basic HTTP Server", example_1_basic_http_server),
        "2": ("Production Server", example_2_production_server),
        "3": ("Docker Deployment", example_3_docker_deployment),
        "4": ("Cloud Deployment", example_4_cloud_deployment),
        "5": ("Kubernetes Deployment", example_5_kubernetes_deployment),
        "6": ("Nginx Reverse Proxy", example_6_nginx_reverse_proxy),
        "7": ("Authentication Server", example_7_authentication_server),
    }
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    print()
    choice = input("Select an example to run (1-7) or 'all' to run all: ").strip()
    
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

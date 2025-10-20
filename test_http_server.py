#!/usr/bin/env python3
"""
Test script for the MITRE ATT&CK MCP HTTP Server

This script tests the HTTP server functionality and provides examples
of how to interact with the server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app


async def test_server():
    """Test the HTTP server functionality"""
    print("🧪 Testing MITRE ATT&CK MCP HTTP Server")
    print("=" * 50)
    
    # Create the ASGI application
    print("1. Creating ASGI application...")
    app = create_app()
    print("✅ ASGI application created successfully")
    
    # Test that the app has the expected structure
    print("\n2. Testing application structure...")
    
    # Check if it's a valid ASGI app
    if hasattr(app, '__call__'):
        print("✅ Application is callable (ASGI compatible)")
    else:
        print("❌ Application is not callable")
        return False
    
    # Test that we can get the MCP server
    print("\n3. Testing MCP server integration...")
    try:
        from src.mitre_attack_mcp.server import mcp
        print("✅ MCP server imported successfully")
        print(f"   Server name: {mcp.name}")
        
        # List available tools (async method)
        tools = await mcp.list_tools()
        print(f"✅ Available tools: {len(tools)}")
        for tool in tools[:5]:  # Show first 5 tools
            print(f"   - {tool.name}: {tool.description[:50]}...")
        if len(tools) > 5:
            print(f"   ... and {len(tools) - 5} more tools")
            
    except Exception as e:
        print(f"❌ Error importing MCP server: {e}")
        return False
    
    print("\n4. Testing data availability...")
    try:
        from src.mitre_attack_mcp.server import attack_data_sources
        if attack_data_sources:
            print(f"✅ Data sources loaded: {list(attack_data_sources.keys())}")
        else:
            print("⚠️  No data sources loaded")
    except Exception as e:
        print(f"❌ Error checking data sources: {e}")
        return False
    
    print("\n✅ All tests passed! The HTTP server is ready to use.")
    print("\n🚀 To start the server, run:")
    print("   python start_server.py")
    print("\n🌐 The server will be available at:")
    print("   http://localhost:8032/mcp/")
    
    return True


def test_local_examples():
    """Test the local configuration examples"""
    print("\n🧪 Testing Local Configuration Examples")
    print("=" * 50)
    
    try:
        from examples.local_config import example_1_stdio_server
        print("✅ Local configuration examples imported successfully")
        print("   Run 'python examples/local_config.py' to see local examples")
    except Exception as e:
        print(f"❌ Error importing local examples: {e}")
        return False
    
    return True


def test_remote_examples():
    """Test the remote configuration examples"""
    print("\n🧪 Testing Remote Configuration Examples")
    print("=" * 50)
    
    try:
        from examples.remote_config import example_1_basic_http_server
        print("✅ Remote configuration examples imported successfully")
        print("   Run 'python examples/remote_config.py' to see remote examples")
    except Exception as e:
        print(f"❌ Error importing remote examples: {e}")
        return False
    
    return True


async def test_prompts():
    """Test MCP prompt functionality"""
    print("\n🧪 Testing MCP Prompts")
    print("=" * 50)
    try:
        # Import mcp from the server module
        from mitre_attack_mcp.server import mcp
        
        # Test prompt functionality
        prompts = await mcp.list_prompts()
        print(f"✅ Found {len(prompts)} prompts:")
        for prompt in prompts:
            print(f"   - {prompt.name}: {prompt.description}")
        
        # Test rainbow layer prompt (no arguments required)
        rainbow_prompt = await mcp.get_prompt("rainbow_layer")
        print(f"✅ rainbow_layer prompt test successful")
        print(f"   Result length: {len(rainbow_prompt.messages[0].content.text)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing prompts: {e}")
        return False


async def main():
    """Main test function"""
    print("MITRE ATT&CK MCP Server - Test Suite")
    print("=" * 60)
    
    # Test HTTP server
    http_test = await test_server()
    
    # Test examples
    local_test = test_local_examples()
    remote_test = test_remote_examples()
    
    # Test prompts
    prompt_test = await test_prompts()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"HTTP Server: {'✅ PASS' if http_test else '❌ FAIL'}")
    print(f"Local Examples: {'✅ PASS' if local_test else '❌ FAIL'}")
    print(f"Remote Examples: {'✅ PASS' if remote_test else '❌ FAIL'}")
    print(f"MCP Prompts: {'✅ PASS' if prompt_test else '❌ FAIL'}")
    
    if all([http_test, local_test, remote_test, prompt_test]):
        print("\n🎉 All tests passed! The server is ready for deployment.")
        print("\n📚 Next steps:")
        print("   1. Run 'python start_server.py' to start the HTTP server")
        print("   2. Run 'python examples/local_config.py' for local examples")
        print("   3. Run 'python examples/remote_config.py' for remote examples")
        print("   4. Check the README.md for deployment instructions")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

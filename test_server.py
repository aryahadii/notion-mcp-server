#!/usr/bin/env python3
"""
Test script for the Notion MCP SSE Server
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test that required environment variables are set."""
    print("Testing environment configuration...")
    
    notion_token = os.getenv("NOTION_TOKEN")
    if not notion_token:
        print("❌ NOTION_TOKEN not found in environment")
        print("Please copy .env.example to .env and add your Notion token")
        return False
    
    if notion_token == "ntn_your_integration_token_here":
        print("❌ NOTION_TOKEN still has placeholder value")
        print("Please update .env with your actual Notion integration token")
        return False
    
    print("✅ Environment configuration looks good")
    return True

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        from fastmcp import FastMCP, Context
        from notion_client import AsyncClient
        from notion_client.errors import APIResponseError
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

async def test_notion_connection():
    """Test connection to Notion API."""
    print("Testing Notion API connection...")
    
    try:
        from notion_client import AsyncClient
        
        notion_token = os.getenv("NOTION_TOKEN")
        notion = AsyncClient(auth=notion_token)
        
        # Try to list users (basic API test)
        response = await notion.users.list()
        print("✅ Notion API connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Notion API connection failed: {e}")
        print("Please check your NOTION_TOKEN and integration permissions")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Notion MCP SSE Server\n")
    
    tests = [
        test_environment,
        test_imports,
    ]
    
    # Run synchronous tests
    for test in tests:
        if not test():
            print("\n❌ Tests failed. Please fix the issues above.")
            sys.exit(1)
        print()
    
    # Run async test
    try:
        asyncio.run(test_notion_connection())
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        sys.exit(1)
    
    print("\n✅ All tests passed! The server should work correctly.")
    print("\nTo start the server, run:")
    print("  python server.py")
    print("\nOr with Docker:")
    print("  docker-compose up --build")

if __name__ == "__main__":
    main()

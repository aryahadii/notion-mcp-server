#!/usr/bin/env python3
"""
Test script for Notion MCP SSE Server authentication.
This script tests the Bearer token authentication for SSE endpoints.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for the Notion MCP SSE Server
BASE_URL = os.getenv("SERVER_URL", "http://localhost:8000")

def generate_token():
    """Generate an authentication token using the server's endpoint."""
    try:
        response = requests.post(
            f"{BASE_URL}/generate_auth_token",
            json={
                "subject": "test-user",
                "scopes": ["read", "write"],
                "expiry_seconds": 3600
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error generating token: {e}")
        return None

def test_authenticated_request(token):
    """Test an authenticated request to the SSE endpoint."""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream"
        }
        
        # Make a request to the SSE endpoint
        # Using a short timeout to just test authentication, not to receive events
        response = requests.get(
            f"{BASE_URL}/sse",
            headers=headers,
            stream=True,
            timeout=2
        )
        
        print(f"Authenticated request status code: {response.status_code}")
        print(f"Authenticated request headers: {response.headers}")
        
        # Try to get the first few bytes of the response
        try:
            for line in response.iter_lines(chunk_size=1024, decode_unicode=True):
                if line:
                    print(f"Received: {line}")
                    break
        except requests.exceptions.ReadTimeout:
            print("Timeout while reading SSE stream (expected for testing)")
            
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Error making authenticated request: {e}")
        return False

def test_unauthenticated_request():
    """Test an unauthenticated request to the SSE endpoint."""
    try:
        headers = {
            "Accept": "text/event-stream"
        }
        
        # Make a request to the SSE endpoint without authentication
        response = requests.get(
            f"{BASE_URL}/sse",
            headers=headers,
            stream=False,
            timeout=2
        )
        
        print(f"Unauthenticated request status code: {response.status_code}")
        print(f"Unauthenticated request response: {response.text}")
        
        # We expect a 401 Unauthorized response
        return response.status_code == 401
    except requests.RequestException as e:
        print(f"Error making unauthenticated request: {e}")
        return False

def main():
    """Main function to run the tests."""
    print("Testing Notion MCP SSE Server Authentication")
    print(f"Server URL: {BASE_URL}")
    
    # Test unauthenticated request first
    print("\n=== Testing Unauthenticated Request ===")
    unauthenticated_success = test_unauthenticated_request()
    print(f"Unauthenticated test {'PASSED' if unauthenticated_success else 'FAILED'}")
    
    # Generate a token
    print("\n=== Generating Authentication Token ===")
    token_response = generate_token()
    if not token_response:
        print("Failed to generate token. Exiting.")
        sys.exit(1)
    
    token = token_response.get("token")
    print(f"Token generated successfully: {token[:20]}...")
    
    # Test authenticated request
    print("\n=== Testing Authenticated Request ===")
    authenticated_success = test_authenticated_request(token)
    print(f"Authenticated test {'PASSED' if authenticated_success else 'FAILED'}")
    
    # Summary
    print("\n=== Test Summary ===")
    if unauthenticated_success and authenticated_success:
        print("All tests PASSED! Bearer token authentication is working correctly.")
    else:
        print("Some tests FAILED. Bearer token authentication may not be configured correctly.")

if __name__ == "__main__":
    main()

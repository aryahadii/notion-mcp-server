#!/usr/bin/env python3
"""
Notion MCP Client Token Generator
A utility script to generate JWT tokens for authenticating with the Notion MCP SSE Server.
"""

import os
import sys
import time
import argparse
import jwt
from dotenv import load_dotenv
from pydantic import SecretStr

# Load environment variables from .env file if present
load_dotenv()

# Read RSA key pair from environment variables (base64-encoded PEM)
import base64
rsa_private_key_b64 = os.getenv("RSA_PRIVATE_KEY")
rsa_public_key_b64 = os.getenv("RSA_PUBLIC_KEY")

if not rsa_private_key_b64 or not rsa_public_key_b64:
    rsa_private_key = None
    rsa_public_key = None
else:
    rsa_private_key = base64.b64decode(rsa_private_key_b64.encode()).decode("utf-8")
    rsa_public_key = base64.b64decode(rsa_public_key_b64.encode()).decode("utf-8")

if not rsa_private_key or not rsa_public_key:
    print("\033[91m")  # Red color
    print("Error: RSA keys not found in environment variables.")
    print("Make sure RSA_PRIVATE_KEY and RSA_PUBLIC_KEY are set in your .env file.")
    print("You can generate RSA keys using OpenSSL:")
    print("  openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048")
    print("  openssl rsa -pubout -in private_key.pem -out public_key.pem")
    print("\033[0m")
    sys.exit(1)

def generate_client_token(subject, issuer, audience, scopes, expires_in_seconds):
    """
    Generate a JWT token signed with RSA_PRIVATE_KEY.
    
    Args:
        subject: Subject identifier (usually user ID)
        issuer: Token issuer identifier
        audience: Intended audience for the token
        scopes: List of permission scopes to include in the token
        expires_in_seconds: Token validity period in seconds
        
    Returns:
        Signed JWT token string
    """
    now = int(time.time())
    payload = {
        "sub": subject,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + expires_in_seconds
    }
    
    # Add scopes if provided
    if scopes:
        payload["scope"] = " ".join(scopes)
        
    # Sign the token with the private key using RS256 algorithm
    token = jwt.encode(payload, rsa_private_key, algorithm="RS256")
    return token

def validate_token(token):
    """
    Validate a JWT token using the RSA_PUBLIC_KEY.
    
    Args:
        token: JWT token to validate
        
    Returns:
        Decoded token payload if valid
    """
    try:
        decoded = jwt.decode(
            token, 
            rsa_public_key, 
            algorithms=["RS256"],
            audience="notion-mcp"
        )
        return decoded
    except jwt.PyJWTError as e:
        print(f"\033[91mToken validation failed: {e}\033[0m")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a JWT client token for Notion MCP.")
    parser.add_argument('--subject', default="notion-mcp-client", help='JWT subject (default: notion-mcp-client)')
    parser.add_argument('--issuer', default="notion-mcp-auth", help='JWT issuer (default: notion-mcp-auth)')
    parser.add_argument('--audience', default="notion-mcp", help='JWT audience (default: notion-mcp)')
    parser.add_argument('--scopes', default="read", help='Comma-separated scopes (default: read)')
    parser.add_argument('--expires-in', type=int, default=3600*24, help='Token expiry in seconds (default: 86400)')
    parser.add_argument('--validate', action='store_true', help='Validate the generated token')
    
    args = parser.parse_args()

    scopes = [scope.strip() for scope in args.scopes.split(",") if scope.strip()]

    token = generate_client_token(
        subject=args.subject,
        issuer=args.issuer,
        audience=args.audience,
        scopes=scopes,
        expires_in_seconds=args.expires_in
    )
    
    print("\033[92m")  # Green color
    print("Client JWT token:")
    print(f"Bearer {token}")
    print("\033[0m")
    
    if args.validate:
        print("\033[94m")  # Blue color
        print("Validating token...")
        decoded = validate_token(token)
        if decoded:
            print("Token is valid!")
            print("Payload:")
            for key, value in decoded.items():
                print(f"  {key}: {value}")
        print("\033[0m")

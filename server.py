#!/usr/bin/env python3
"""
Notion MCP SSE Server
A simple MCP server that provides read-only access to Notion pages via SSE transport.
Includes Bearer token authentication for SSE endpoints.
"""

import os
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from fastmcp import FastMCP, Context
from fastmcp.server.auth import BearerAuthProvider
from notion_client import AsyncClient
from notion_client.errors import APIResponseError
import jwt

# Load environment variables
load_dotenv()

# Setup Bearer token authentication with RSA keys (base64-encoded PEM)
import base64
rsa_public_key_b64 = os.getenv("RSA_PUBLIC_KEY")
rsa_private_key_b64 = os.getenv("RSA_PRIVATE_KEY")

if not rsa_public_key_b64:
    raise ValueError("RSA_PUBLIC_KEY environment variable is required for authentication")

if rsa_public_key_b64:
    rsa_public_key = base64.b64decode(rsa_public_key_b64.encode()).decode("utf-8")
else:
    rsa_public_key = None

if rsa_private_key_b64:
    rsa_private_key = base64.b64decode(rsa_private_key_b64.encode()).decode("utf-8")
else:
    rsa_private_key = None

# Configure authentication provider with RSA public key
auth_provider = BearerAuthProvider(
    public_key=rsa_public_key,  # RSA public key for token validation
    algorithm="RS256",         # RS256 algorithm for RSA-based signatures
    audience="notion-mcp"      # Expected audience claim in the token
)

# Token generation utility function
def generate_token(subject: str, scopes: Optional[list] = None, expiry_seconds: int = 3600) -> str:
    """
    Generate a JWT token signed with RSA_PRIVATE_KEY.

    Args:
        subject: Subject identifier (usually user ID)
        scopes: List of permission scopes to include in the token
        expiry_seconds: Token validity period in seconds (default: 1 hour)

    Returns:
        Signed JWT token string
    """
    if not rsa_private_key:
        raise ValueError("RSA_PRIVATE_KEY environment variable is required for token generation")

    now = int(time.time())
    payload = {
        "sub": subject,
        "iss": "notion-mcp-auth",
        "aud": "notion-mcp",
        "iat": now,
        "exp": now + expiry_seconds
    }

    # Add scopes if provided
    if scopes:
        payload["scope"] = " ".join(scopes)

    # Sign the token with the private key using RS256 algorithm
    token = jwt.encode(payload, rsa_private_key, algorithm="RS256")
    return token

# Initialize FastMCP server with authentication
mcp = FastMCP(name="notion-mcp-sse", auth=auth_provider)

# Initialize Notion client
notion_token = os.getenv("NOTION_TOKEN")
if not notion_token:
    raise ValueError("NOTION_TOKEN environment variable is required")

notion = AsyncClient(auth=notion_token)


@mcp.tool
async def get_page(page_id: str, ctx: Context) -> Dict[str, Any]:
    """
    Retrieve a Notion page by its ID.

    Args:
        page_id: The Notion page ID (with or without hyphens)
        ctx: MCP context for logging

    Returns:
        Dict containing page information and content
    """
    try:
        await ctx.info(f"Fetching page: {page_id}")

        # Clean page ID (remove hyphens if present)
        clean_page_id = page_id.replace("-", "")

        # Get page info
        page = await notion.pages.retrieve(page_id=clean_page_id)

        # Get page content (blocks)
        blocks_response = await notion.blocks.children.list(block_id=clean_page_id)

        return {
            "page": page,
            "blocks": blocks_response.get("results", []),
            "has_more": blocks_response.get("has_more", False)
        }

    except APIResponseError as e:
        await ctx.error(f"Notion API error: {e}")
        raise NotionAPIError(f"Failed to retrieve page {page_id}: {e}") from e
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise NotionRequestError(f"Failed to retrieve page {page_id}: {e}") from e


@mcp.tool
async def search_pages(query: str, ctx: Context, page_size: int = 10) -> Dict[str, Any]:
    """
    Search for pages in Notion workspace.

    Args:
        ctx: MCP context for logging
        query: Search query string (optional)
        page_size: Number of results to return (default: 10, max: 100)

    Returns:
        Dict containing search results
    """
    try:
        await ctx.info(f"Searching pages with query: '{query}'")

        # Convert and limit page size to prevent excessive API calls
        try:
            page_size = int(page_size)
        except (ValueError, TypeError):
            page_size = 10
        page_size = min(page_size, 100)

        search_params = {
            "page_size": page_size,
            "filter": {
                "property": "object",
                "value": "page"
            }
        }

        # Handle empty query parameter
        if query and query != "all":
            search_params["query"] = query

        results = await notion.search(**search_params)

        return {
            "results": results.get("results", []),
            "has_more": results.get("has_more", False),
            "next_cursor": results.get("next_cursor")
        }

    except APIResponseError as e:
        await ctx.error(f"Notion API error: {e}")
        raise Exception(f"Failed to search pages: {e}") from e
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to search pages: {e}") from e


@mcp.tool
async def get_database(database_id: str, ctx: Context) -> Dict[str, Any]:
    """
    Retrieve a Notion database by its ID.

    Args:
        database_id: The Notion database ID
        ctx: MCP context for logging

    Returns:
        Dict containing database information
    """
    try:
        await ctx.info(f"Fetching database: {database_id}")

        # Clean database ID
        clean_db_id = database_id.replace("-", "")

        # Get database info
        database = await notion.databases.retrieve(database_id=clean_db_id)

        return {
            "database": database
        }

    except APIResponseError as e:
        await ctx.error(f"Notion API error: {e}")
        raise Exception(f"Failed to retrieve database {database_id}: {e}") from e
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to retrieve database {database_id}: {e}") from e


@mcp.tool
async def query_database(database_id: str, page_size: str, ctx: Context) -> Dict[str, Any]:
    """
    Query a Notion database for its pages.

    Args:
        database_id: The Notion database ID
        ctx: MCP context for logging
        page_size: Number of results to return (default: 10, max: 100)

    Returns:
        Dict containing database query results
    """
    try:
        await ctx.info(f"Querying database: {database_id}")

        # Clean database ID and convert/limit page size
        clean_db_id = database_id.replace("-", "")
        try:
            page_size = int(page_size)
        except (ValueError, TypeError):
            page_size = 10
        page_size = min(page_size, 100)

        # Query database
        results = await notion.databases.query(
            database_id=clean_db_id,
            page_size=page_size
        )

        return {
            "results": results.get("results", []),
            "has_more": results.get("has_more", False),
            "next_cursor": results.get("next_cursor")
        }

    except APIResponseError as e:
        await ctx.error(f"Notion API error: {e}")
        raise Exception(f"Failed to query database {database_id}: {e}") from e
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to query database {database_id}: {e}") from e




def generate_auth_token(subject: str, scopes: Optional[list] = None, expiry_seconds: int = 3600) -> Dict[str, Any]:
    """
    Generate an authentication token for testing.

    Args:
        subject: Subject identifier (usually user ID)
        scopes: List of permission scopes (optional)
        expiry_seconds: Token validity period in seconds (default: 1 hour)

    Returns:
        Dict containing the token and its expiry time
    """
    try:
        token = generate_token(subject, scopes, expiry_seconds)
        return {
            "token": token,
            "expires_in": expiry_seconds,
            "token_type": "Bearer"
        }
    except Exception as e:
        # Properly re-raise with context
        raise Exception(f"Failed to generate token: {e}") from e


def main():
    """Main entry point for the server."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting Notion MCP SSE Server on {host}:{port}")
    print(f"Authentication: Enabled (RSA key-based)")

    # Run the server with SSE transport
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()

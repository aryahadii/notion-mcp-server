#!/usr/bin/env python3
"""
Notion MCP SSE Server
A simple MCP server that provides read-only access to Notion pages via SSE transport.
"""

import os
import asyncio
from typing import Dict, Any, List
from dotenv import load_dotenv
from fastmcp import FastMCP, Context
from notion_client import AsyncClient
from notion_client.errors import APIResponseError

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP(name="notion-mcp-sse")

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
        raise Exception(f"Failed to retrieve page {page_id}: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to retrieve page {page_id}: {e}")


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
        raise Exception(f"Failed to search pages: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to search pages: {e}")


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
        raise Exception(f"Failed to retrieve database {database_id}: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to retrieve database {database_id}: {e}")


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
        raise Exception(f"Failed to query database {database_id}: {e}")
    except Exception as e:
        await ctx.error(f"Unexpected error: {e}")
        raise Exception(f"Failed to query database {database_id}: {e}")




def main():
    """Main entry point for the server."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting Notion MCP SSE Server on {host}:{port}")

    # Run the server with SSE transport
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()

# Notion MCP SSE Server

A simple MCP (Model Context Protocol) server that provides read-only access to Notion pages via SSE (Server-Sent Events) transport using FastMCP.

## Features

- **Read-only access** to Notion pages and databases
- **SSE transport** for real-time communication
- **Bearer token authentication** for secure SSE endpoints
- **Docker deployment** ready
- **Simple configuration** via environment variables
- **Comprehensive error handling** and logging

## Available Resources

- `notion://pages/{page_id}` - Get a specific page by ID
- `notion://search/{query}` - Search for pages (use 'all' for all pages)
- `notion://databases/{database_id}` - Get database information
- `notion://databases/{database_id}/query/{page_size}` - Query database pages

## Setup

### 1. Notion Integration Setup

1. Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. Create a new internal integration or select an existing one
3. Configure it as **read-only** by giving only "Read content" access
4. Copy the integration token (starts with `ntn_`)
5. Grant the integration access to the pages/databases you want to expose

### 2. Environment Configuration

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Notion token and **base64-encoded** RSA keys for authentication:

   ```env
   NOTION_TOKEN=ntn_your_integration_token_here
   RSA_PUBLIC_KEY="<base64-encoded-PEM-public-key>"
   RSA_PRIVATE_KEY="<base64-encoded-PEM-private-key>"
   HOST=127.0.0.1
   PORT=8000
   ```

   > **Important:** The keys **must be base64-encoded PEM strings**, not raw PEM. If you do not have base64-encoded keys, you can generate them as follows:
   > ```bash
   > # Generate private key
   > openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
   > # Extract public key
   > openssl rsa -pubout -in private_key.pem -out public_key.pem
   > # Encode keys as base64 (remove newlines for .env compatibility)
   > base64 -w 0 private_key.pem > private_key.b64
   > base64 -w 0 public_key.pem > public_key.b64
   > ```
   > Then copy the contents of `private_key.b64` and `public_key.b64` into your `.env` as shown above.
   >
   > Alternatively, if you start the server or run `python generate_client_token.py` without the keys set, it will print out base64-encoded keys for you to copy into your `.env` file.


   > **Note:** For RSA key generation, you can use OpenSSL:
   > ```bash
   > # Generate private key
   > openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
   > # Extract public key
   > openssl rsa -pubout -in private_key.pem -out public_key.pem
   > ```

### 3. Installation & Running

#### Option 1: Local Python

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
fastmcp run server.py -t sse
```

#### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t notion-mcp .
docker run -p 8000:8000 --env-file .env notion-mcp
```

## Usage

Once running, the server exposes a set of tools that can be used by any MCP-compatible client (e.g., an LLM agent for function-calling). The server listens for SSE connections at `http://localhost:8000/sse/` (or your configured host/port).

### Available Tools

The following tools are available for interacting with Notion:

- `get_page(page_id: str)`: Retrieves a Notion page and its content by its ID.
- `search_pages(query: str, page_size: int = 10)`: Searches for pages in your Notion workspace.
- `get_database(database_id: str)`: Retrieves information about a specific Notion database.
- `query_database(database_id: str, page_size: int = 10)`: Queries a Notion database and returns its pages.

## Authentication

This server implements Bearer token authentication for SSE endpoints using RSA key pairs:

- **JWT Tokens**: Authentication uses JWT tokens signed with RS256 algorithm
- **RSA Key Pairs**: Uses asymmetric cryptography for secure token validation
- **Token Generation**: Includes a utility endpoint to generate tokens for testing

### Using Authentication

1. **Generate a token** using the `/generate_auth_token` endpoint:

   ```bash
   curl -X POST http://localhost:8000/generate_auth_token \
     -H "Content-Type: application/json" \
     -d '{"subject":"user123","scopes":["read"],"expiry_seconds":3600}'
   ```

2. **Use the token** in your SSE requests:

   ```bash
   curl -N http://localhost:8000/sse \
     -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
   ```

### Testing Authentication

A test script is included to verify authentication is working correctly:

```bash
python test_auth.py
```

This will test both authenticated and unauthenticated requests to ensure the Bearer token authentication is functioning properly.

## Security

- This server provides **read-only** access to Notion
- Bearer token authentication secures all SSE endpoints
- Configure your Notion integration with minimal permissions
- Use environment variables for sensitive configuration
- The server only exposes data that your integration has access to

## Dependencies

- `fastmcp>=2.0.0` - FastMCP framework for MCP server implementation
- `notion-client>=2.2.1` - Official Notion API Python client
- `python-dotenv>=1.0.0` - Environment variable management

## License

MIT License

# Quick Setup Guide

## 1. Notion Integration Setup

1. Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. Create a new internal integration
3. Configure it as **read-only** (only "Read content" permission)
4. Copy the integration token (starts with `ntn_`)
5. Grant access to pages/databases you want to expose

## 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your token
NOTION_TOKEN=ntn_your_actual_token_here
HOST=127.0.0.1
PORT=8000
```

## 3. Run Options

### Option A: Local Python (with virtual environment)
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate.fish  # for fish shell
# or: source .venv/bin/activate  # for bash/zsh

# Install dependencies
pip install -r requirements.txt

# Test the setup
python test_server.py

# Run the server
python server.py
```

### Option B: Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or manually
docker build -t notion-mcp-sse .
docker run -p 8000:8000 --env-file .env notion-mcp-sse
```

## 4. Available Resources

Once running at `http://localhost:8000`:

- `notion://pages/{page_id}` - Get page content
- `notion://search/{query}` - Search pages (use 'all' for all pages)
- `notion://databases/{database_id}` - Get database info
- `notion://databases/{database_id}/query/{page_size}` - Query database pages

## 5. Testing

Run the test script to verify everything works:
```bash
python test_server.py
```

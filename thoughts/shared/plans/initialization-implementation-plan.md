# FastMCP GitHub OAuth Example Server Implementation Plan

## Overview

This plan outlines the creation of an example MCP (Model Context Protocol) server that demonstrates GitHub OAuth authentication using FastMCP framework. The server will be structured as a uv project with HTTP-streamable transport capabilities and packaged into Docker containers using GoReleaser, serving as a reference implementation for developers wanting to integrate GitHub OAuth with their MCP servers.

## Current State Analysis

Based on the research, we have identified:
- FastMCP provides built-in GitHubProvider for OAuth authentication
- uv offers fast project initialization and Python packaging
- GoReleaser v2.9+ supports uv Python projects with wheel/sdist building
- GoReleaser provides built artifacts directly in Docker build context
- HTTP-streamable transport is supported via `fastmcp run --transport http`
- Docker containerization is fully supported by GoReleaser with multi-arch builds

### Key Discoveries:
- GitHubProvider handles GitHub's token format and validation automatically
- HTTP transport is required to enable OAuth flows (not stdio)
- uv can initialize projects with `--package` flag for proper distribution structure
- GoReleaser can build Python wheels using `builder: uv` and `buildmode: wheel`
- Built wheels are available directly in Docker build context (no multi-stage build needed)
- Docker images can be built for multiple architectures using GoReleaser's docker configuration

## Desired End State

A complete example project that demonstrates:
1. uv-based Python project with proper packaging
2. FastMCP server with GitHub OAuth authentication
3. HTTP-streamable transport configuration
4. Protected tools that use GitHub user information
5. Docker containerization with multi-arch support leveraging GoReleaser-built wheels
6. Automated builds and releases with GoReleaser
7. Comprehensive documentation and setup instructions

### Verification Criteria:
- Project builds successfully with `uv build`
- GoReleaser builds Docker images successfully using pre-built wheels
- OAuth flow works end-to-end with GitHub
- Protected tools return authenticated user data
- Docker container runs and serves HTTP-streamable MCP
- Documentation is clear and complete

## What We're NOT Doing

- Client implementation (removed per request)
- Production deployment configuration beyond Docker
- Database persistence for user data
- Advanced GitHub API integrations beyond basic user info
- Multiple OAuth provider support
- Custom OAuth implementation (using FastMCP's built-in provider)

## Implementation Approach

We'll create a containerized FastMCP server using uv for Python packaging and GoReleaser for building and Docker image creation. GoReleaser will build the Python wheel and provide it directly to the Docker build context, eliminating the need for multi-stage builds or compilation within Docker.

## Phase 1: Project Structure Setup

### Overview
Initialize the uv project structure with proper packaging configuration, dependencies, and GoReleaser configuration that leverages pre-built wheels.

### Changes Required:

#### 1. Project Initialization
**Commands**: 
```bash
uv init --package fastmcp-github-oauth-example
cd fastmcp-github-oauth-example
```

#### 2. Python Dependencies Configuration
**File**: `pyproject.toml`
**Changes**: Add FastMCP and required dependencies with proper packaging

```toml
[project]
name = "fastmcp-github-oauth-example"
version = "0.1.0"
description = "Example MCP server demonstrating GitHub OAuth authentication with FastMCP"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastmcp>=2.6.0",
    "httpx>=0.25.0",
    "starlette>=0.27.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0"
]

[project.scripts]
github-oauth-server = "fastmcp_github_oauth_example.server:main"

[build-system]
requires = ["uv_build>=0.8.11,<0.9.0"]
build-backend = "uv_build"
```

#### 3. GoReleaser Configuration
**File**: `.goreleaser.yaml`
**Changes**: Configure GoReleaser for Python/uv builds and Docker packaging using pre-built wheels

```yaml
version: 2

project_name: fastmcp-github-oauth-example

before:
  hooks:
    - uv sync

builds:
  - id: wheel
    builder: uv
    buildmode: wheel
    env:
      - UV_BUILD_BACKEND=uv_build

dockers:
  - ids:
      - wheel  # Reference the wheel build artifact
    image_templates:
      - "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}-amd64"
    use: buildx
    dockerfile: Dockerfile
    build_flag_templates:
      - "--platform=linux/amd64"
      - "--label=org.opencontainers.image.created={{.Date}}"
      - "--label=org.opencontainers.image.title={{.ProjectName}}"
      - "--label=org.opencontainers.image.revision={{.FullCommit}}"
      - "--label=org.opencontainers.image.version={{.Version}}"
  - ids:
      - wheel  # Reference the wheel build artifact
    image_templates:
      - "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}-arm64"
    use: buildx
    goarch: arm64
    dockerfile: Dockerfile
    build_flag_templates:
      - "--platform=linux/arm64"
      - "--label=org.opencontainers.image.created={{.Date}}"
      - "--label=org.opencontainers.image.title={{.ProjectName}}"
      - "--label=org.opencontainers.image.revision={{.FullCommit}}"
      - "--label=org.opencontainers.image.version={{.Version}}"

docker_manifests:
  - name_template: "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}"
    image_templates:
      - "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}-amd64"
      - "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}-arm64"
  - name_template: "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:latest"
    image_templates:
      - "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}-amd64"
      - "ghcr.io/{{.Env.GITHUB_REPOSITORY_OWNER}}/{{.ProjectName}}:{{.Version}}-arm64"

release:
  github:
    owner: "{{.Env.GITHUB_REPOSITORY_OWNER}}"
    name: "{{.ProjectName}}"
```

#### 4. Dockerfile (Simplified - Using GoReleaser-built Wheel)
**File**: `Dockerfile`
**Changes**: Single-stage Dockerfile that uses GoReleaser's pre-built wheel

```dockerfile
FROM python:3.11-slim

# Install uv and curl for health checks
RUN pip install uv && \
    apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /app

# Create virtual environment
RUN uv venv

# Copy the wheel from GoReleaser build context (available at root level)
COPY *.whl ./

# Install the wheel and clean up
RUN uv pip install --no-cache-dir *.whl && rm *.whl

# Expose port
EXPOSE 8000

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "fastmcp_github_oauth_example.server"]
```

#### 5. Project Structure
**Directory Structure**:
```
fastmcp-github-oauth-example/
├── src/
│   └── fastmcp_github_oauth_example/
│       ├── __init__.py
│       └── server.py
├── .github/
│   └── workflows/
│       └── release.yml
├── Dockerfile
├── .goreleaser.yaml
├── README.md
├── pyproject.toml
├── uv.lock
└── .gitignore
```

### Success Criteria:

#### Automated Verification:
- [ ] Project initializes successfully: `uv init --package fastmcp-github-oauth-example`
- [ ] Dependencies install cleanly: `uv sync`
- [ ] Project builds successfully: `uv build`
- [ ] GoReleaser config validates: `goreleaser check`
- [ ] Docker image builds locally: `docker build -t test .`
- [ ] Wheel is available in build context: GoReleaser provides wheel at root level

#### Manual Verification:
- [ ] All required files are present
- [ ] Project follows Python packaging conventions
- [ ] GoReleaser configuration references wheel build correctly
- [ ] Dockerfile follows best practices and uses pre-built wheel

---

## Phase 2: Server Implementation

### Overview
Implement the FastMCP server with GitHub OAuth authentication, protected tools, and health check endpoint.

### Changes Required:

#### 1. Core Server Implementation
**File**: `src/fastmcp_github_oauth_example/server.py`
**Changes**: Implement FastMCP server with GitHubProvider and health endpoint

```python
import os
from typing import Dict, Any
from fastmcp import FastMCP
from fastmcp.server.auth.providers.github import GitHubProvider
from fastmcp.server.dependencies import get_access_token
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.requests import Request

def create_health_endpoint():
    """Create health check endpoint for container monitoring."""
    async def health(request: Request):
        return JSONResponse({
            "status": "healthy", 
            "service": "fastmcp-github-oauth",
            "version": "0.1.0"
        })
    
    return Route("/health", health, methods=["GET"])

def create_server():
    """Create and configure the FastMCP server."""
    
    # Validate required environment variables
    required_env_vars = ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    # Initialize GitHub OAuth provider
    auth_provider = GitHubProvider(
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        base_url=os.getenv("BASE_URL", "http://localhost:8000"),
        redirect_path="/auth/callback",
        required_scopes=["user:email"]  # Request email access
    )
    
    # Create FastMCP server with authentication
    mcp = FastMCP(
        name="GitHub OAuth Example Server", 
        auth=auth_provider,
        routes=[create_health_endpoint()]  # Add health check
    )
    
    @mcp.tool
    async def get_user_info() -> Dict[str, Any]:
        """Returns information about the authenticated GitHub user."""
        token = get_access_token()
        return {
            "github_user": token.claims.get("login"),
            "name": token.claims.get("name"),
            "email": token.claims.get("email"),
            "avatar_url": token.claims.get("avatar_url"),
            "company": token.claims.get("company"),
            "location": token.claims.get("location"),
            "public_repos": token.claims.get("public_repos"),
            "followers": token.claims.get("followers"),
            "following": token.claims.get("following"),
            "bio": token.claims.get("bio"),
            "blog": token.claims.get("blog"),
            "created_at": token.claims.get("created_at"),
            "updated_at": token.claims.get("updated_at")
        }
    
    @mcp.tool
    async def get_server_info() -> Dict[str, Any]:
        """Returns information about the MCP server."""
        return {
            "server_name": "FastMCP GitHub OAuth Example",
            "version": "0.1.0",
            "auth_provider": "GitHub OAuth",
            "transport": "HTTP Streamable",
            "container": "Docker Multi-arch",
            "build_system": "GoReleaser + uv",
            "endpoints": {
                "mcp": "/mcp/",
                "health": "/health",
                "oauth_callback": "/auth/callback"
            },
            "supported_architectures": ["linux/amd64", "linux/arm64"]
        }
    
    @mcp.tool
    async def get_oauth_status() -> Dict[str, Any]:
        """Returns OAuth configuration status (without secrets)."""
        token = get_access_token()
        return {
            "authenticated": True,
            "user": token.claims.get("login"),
            "scopes": token.claims.get("scopes", []),
            "token_type": "Bearer",
            "auth_provider": "GitHub",
            "client_id": os.getenv("GITHUB_CLIENT_ID"),
            "base_url": os.getenv("BASE_URL", "http://localhost:8000")
        }
    
    @mcp.tool
    async def ping() -> Dict[str, Any]:
        """Simple ping endpoint for testing connectivity."""
        return {
            "message": "pong",
            "timestamp": "{{ .Date }}",
            "server": "FastMCP GitHub OAuth Example"
        }
    
    return mcp

def main():
    """Entry point for running the server."""
    try:
        mcp = create_server()
        port = int(os.getenv("PORT", "8000"))
        host = os.getenv("HOST", "0.0.0.0")
        
        print("🚀 Starting FastMCP GitHub OAuth Example Server")
        print(f"🌐 Server: http://{host}:{port}")
        print(f"📖 MCP Endpoint: http://{host}:{port}/mcp/")
        print(f"🔒 OAuth Callback: http://{host}:{port}/auth/callback")
        print(f"❤️  Health Check: http://{host}:{port}/health")
        print("📋 Available Tools: get_user_info, get_server_info, get_oauth_status, ping")
        
        mcp.run(transport="http", port=port, host=host)
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Make sure to set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
        exit(1)
    except Exception as e:
        print(f"❌ Server Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
```

#### 2. Package Initialization
**File**: `src/fastmcp_github_oauth_example/__init__.py`
**Changes**: Package initialization with version info

```python
"""
FastMCP GitHub OAuth Example

An example MCP server demonstrating GitHub OAuth authentication using FastMCP.
Packaged with uv and containerized with GoReleaser using pre-built wheels.
"""

__version__ = "0.1.0"
__author__ = "FastMCP Contributors"

from .server import create_server, main

__all__ = ["create_server", "main"]
```

### Success Criteria:

#### Automated Verification:
- [ ] Server starts successfully: `uv run python -m fastmcp_github_oauth_example.server`
- [ ] No import errors: `python -c "from fastmcp_github_oauth_example import create_server"`
- [ ] Package script works: `uv run github-oauth-server`
- [ ] Code passes linting: `uv run ruff check src/`
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] All tools are registered and accessible

#### Manual Verification:
- [ ] Server responds to HTTP requests on port 8000
- [ ] OAuth endpoints are accessible
- [ ] Tools are properly registered and callable
- [ ] Error handling works for missing environment variables
- [ ] Health check returns proper JSON response with version info

---

## Phase 3: Containerization and CI/CD

### Overview
Set up GitHub Actions workflow for automated building and publishing of Docker images using GoReleaser with pre-built wheels.

### Changes Required:

#### 1. GitHub Actions Workflow
**File**: `.github/workflows/release.yml`
**Changes**: Automated release workflow with Docker publishing using GoReleaser

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'
  pull_request:
    branches:
      - main

env:
  REGISTRY: ghcr.io

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        
      - name: Set up Python
        run: uv python install 3.11
        
      - name: Install dependencies
        run: uv sync
        
      - name: Run tests
        run: |
          uv run ruff check src/
          uv run black --check src/
          # uv run pytest  # Add when tests are implemented
          
      - name: Build package
        run: uv build
        
      - name: Test server import
        run: uv run python -c "from fastmcp_github_oauth_example import create_server; print('✅ Server import successful')"

      - name: Test GoReleaser build
        if: github.event_name == 'pull_request'
        uses: goreleaser/goreleaser-action@v5
        with:
          distribution: goreleaser
          version: latest
          args: build --snapshot --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  release:
    needs: test
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
      
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Install uv
        uses: astral-sh/setup-uv@v2
        
      - name: Set up Python  
        run: uv python install 3.11
        
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
        
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Run GoReleaser
        uses: goreleaser/goreleaser-action@v5
        with:
          distribution: goreleaser
          version: latest
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY_OWNER: ${{ github.repository_owner }}
```

#### 2. Environment Configuration Template
**File**: `.env.example`
**Changes**: Template for required environment variables

```bash
# GitHub OAuth Configuration
# Get these values from: https://github.com/settings/applications/new
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# Server Configuration
BASE_URL=http://localhost:8000
PORT=8000
HOST=0.0.0.0

# Optional: FastMCP Configuration
FASTMCP_SERVER_AUTH=GITHUB
FASTMCP_DEBUG=false
```

#### 3. Git Configuration
**File**: `.gitignore`
**Changes**: Appropriate gitignore for Python/uv/Docker projects

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# uv
.uv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
*.log

# GoReleaser
dist/

# Docker
docker-compose.override.yml
```

#### 4. Docker Compose for Development
**File**: `docker-compose.yml`
**Changes**: Development setup with Docker Compose

```yaml
version: '3.8'

services:
  fastmcp-server:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GITHUB_CLIENT_ID=${GITHUB_CLIENT_ID}
      - GITHUB_CLIENT_SECRET=${GITHUB_CLIENT_SECRET}
      - BASE_URL=http://localhost:8000
      - PORT=8000
      - HOST=0.0.0.0
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      - "com.example.service=fastmcp-github-oauth"
      - "com.example.version=0.1.0"
```

### Success Criteria:

#### Automated Verification:
- [ ] Workflow syntax is valid: GitHub Actions validates YAML
- [ ] Environment template is complete: `cat .env.example`
- [ ] Docker Compose starts successfully: `docker-compose up -d`
- [ ] Health check passes in container: `curl http://localhost:8000/health`
- [ ] GoReleaser builds images using pre-built wheels: `goreleaser build --snapshot --clean`
- [ ] Wheel is correctly copied into Docker image during build

#### Manual Verification:
- [ ] CI/CD pipeline runs successfully on tag push
- [ ] Docker images are published to GHCR with correct tags
- [ ] Multi-arch images work on different platforms
- [ ] Container starts and serves requests properly
- [ ] OAuth flow works in containerized environment
- [ ] GoReleaser provides wheel artifact to Docker build context

---

## Phase 4: Documentation and README

### Overview
Create comprehensive documentation for setup, usage, deployment, and troubleshooting with emphasis on the GoReleaser + uv build process.

### Changes Required:

#### 1. Main Documentation
**File**: `README.md`
**Changes**: Complete setup and usage guide

```markdown
# FastMCP GitHub OAuth Example

An example MCP (Model Context Protocol) server demonstrating GitHub OAuth authentication using the FastMCP framework. This project showcases how to build, package, and containerize an authenticated MCP server using modern Python tooling with uv and GoReleaser's wheel-based Docker builds.

## Features

- 🔐 GitHub OAuth 2.0 authentication
- 🌐 HTTP-streamable MCP server
- 🛠️ Protected tools that use GitHub user data
- 📦 Modern Python packaging with uv
- 🐳 Docker containerization with multi-arch support
- 🚀 Automated releases with GoReleaser using pre-built wheels
- 📊 Health monitoring and logging
- 🔧 Development and production ready

## Architecture

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   FastMCP Server     │◄──►│  GitHub OAuth   │
│                 │    │   (Containerized)    │    │                 │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
                               │
                         ┌─────▼─────┐
                         │  Docker   │
                         │  Runtime  │
                         │           │
                         │ Built by  │
                         │GoReleaser │
                         │+ uv wheel │
                         └───────────┘
```

## Build Process

This project uses a modern build pipeline:

1. **uv** builds Python wheel from source
2. **GoReleaser** uses the wheel in Docker build context
3. **Dockerfile** installs the pre-built wheel (no compilation in container)
4. **Multi-arch images** built automatically for AMD64 and ARM64

## Prerequisites

- Python 3.11+
- uv (Python package manager)
- Docker (for containerization)
- GitHub account for OAuth app registration

## Quick Start

### 1. GitHub OAuth App Setup

1. Go to [GitHub Settings > Developer settings > OAuth Apps](https://github.com/settings/applications/new)
2. Create a new OAuth App with:
   - **Application name**: `FastMCP OAuth Example`
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/auth/callback`
3. Note your Client ID and Client Secret

### 2. Local Development

```bash
# Clone the repository
git clone <repository-url>
cd fastmcp-github-oauth-example

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your GitHub OAuth credentials

# Run the server
uv run github-oauth-server
```

### 3. Docker Deployment

#### Using Docker Compose (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Using Published Image

```bash
# Pull and run the published image
docker run -d \
  -p 8000:8000 \
  -e GITHUB_CLIENT_ID=your_client_id \
  -e GITHUB_CLIENT_SECRET=your_client_secret \
  -e BASE_URL=http://localhost:8000 \
  --name fastmcp-server \
  ghcr.io/YOUR_ORG/fastmcp-github-oauth-example:latest
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8000/health

# Check MCP endpoint
curl http://localhost:8000/mcp/

# View server logs
docker logs fastmcp-server
```

## Usage

### Available Tools

The server exposes these protected tools (require GitHub authentication):

- **`get_user_info`**: Returns authenticated user's GitHub profile information
- **`get_server_info`**: Returns information about the MCP server and build
- **`get_oauth_status`**: Returns OAuth authentication status and configuration
- **`ping`**: Simple connectivity test

### Authentication Flow

1. Client connects to MCP server at `http://localhost:8000/mcp/`
2. Server responds with 401 and OAuth discovery information
3. Client opens browser for GitHub authentication
4. User grants permissions to the OAuth app
5. GitHub redirects to server callback with authorization code
6. Server exchanges code for access token
7. Client uses token for subsequent MCP requests

### Example MCP Client Usage

The easiest way to test the server is using the MCP Inspector:

```bash
# Start the MCP server (in one terminal)
uv run github-oauth-server

# Test with MCP Inspector (in another terminal)
npx @modelcontextprotocol/inspector@latest http://localhost:8000/mcp/
```

The MCP Inspector will:
1. Open a web interface for testing MCP servers
2. Handle the GitHub OAuth flow automatically
3. Allow you to test all available tools interactively
4. Show request/response details for debugging

#### Testing Individual Tools

Using the MCP Inspector, you can test each tool:

1. **get_user_info**: View your GitHub profile data
2. **get_server_info**: Check server configuration and build info
3. **get_oauth_status**: Verify authentication status
4. **ping**: Test basic connectivity

## Development

### Project Structure

```
fastmcp-github-oauth-example/
├── src/fastmcp_github_oauth_example/
│   ├── __init__.py          # Package initialization
│   └── server.py            # Main server implementation
├── .github/workflows/       # CI/CD workflows
├── Dockerfile              # Container definition (uses pre-built wheel)
├── .goreleaser.yaml        # Release configuration (builds wheel)
├── docker-compose.yml      # Development setup
├── pyproject.toml          # Python project config
└── README.md               # This file
```

### Build Process Details

1. **Python Wheel Build**: GoReleaser uses `uv` to build the wheel
2. **Docker Context**: GoReleaser provides the wheel in the Docker build context
3. **Container Build**: Dockerfile copies and installs the pre-built wheel
4. **No Compilation**: No source compilation happens inside the container

### Local Development

```bash
# Install development dependencies
uv sync --group dev

# Run with auto-reload (development)
uv run python -m fastmcp_github_oauth_example.server

# Format code
uv run black src/

# Lint code  
uv run ruff check src/

# Build package
uv build

# Test GoReleaser build (no Docker push)
goreleaser build --snapshot --clean
```

### Testing

```bash
# Run linting and formatting checks
uv run ruff check src/
uv run black --check src/

# Test server import
uv run python -c "from fastmcp_github_oauth_example import create_server"

# Test Docker build locally
docker build -t test-image .
docker run --rm -p 8000:8000 \
  -e GITHUB_CLIENT_ID=test \
  -e GITHUB_CLIENT_SECRET=test \
  test-image

# Test GoReleaser snapshot build
goreleaser release --snapshot --clean
```

## Deployment

### Container Registry

Pre-built multi-architecture images are available:

```bash
# Latest release
docker pull ghcr.io/YOUR_ORG/fastmcp-github-oauth-example:latest

# Specific version
docker pull ghcr.io/YOUR_ORG/fastmcp-github-oauth-example:v1.0.0

# Architecture-specific
docker pull ghcr.io/YOUR_ORG/fastmcp-github-oauth-example:v1.0.0-amd64
docker pull ghcr.io/YOUR_ORG/fastmcp-github-oauth-example:v1.0.0-arm64
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_CLIENT_ID` | Yes | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | Yes | GitHub OAuth App Client Secret |
| `BASE_URL` | No | Server base URL (default: http://localhost:8000) |
| `PORT` | No | Server port (default: 8000) |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `FASTMCP_DEBUG` | No | Enable debug logging (default: false) |

### Production Deployment

```bash
# Using Docker with environment file
docker run -d \
  --name fastmcp-server \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  ghcr.io/YOUR_ORG/fastmcp-github-oauth-example:latest

# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **"OAuth app not found"**
   - Verify GitHub Client ID and Secret in environment variables
   - Ensure OAuth app is created in GitHub settings

2. **"Callback URL mismatch"**
   - Check that callback URL in GitHub app matches `BASE_URL/auth/callback`
   - Verify `BASE_URL` environment variable is correct

3. **"Container won't start"**
   - Check Docker logs: `docker logs container_name`
   - Verify all required environment variables are set
   - Ensure port 8000 is not already in use

4. **"Wheel not found during Docker build"**
   - Ensure GoReleaser builds wheel before Docker step
   - Check that `ids: [wheel]` references correct build ID
   - Verify GoReleaser configuration syntax

5. **"Authentication fails"**
   - Clear browser cookies and try again
   - Check GitHub OAuth app permissions and scopes
   - Verify server is accessible at the configured BASE_URL

### Debug Mode

Enable detailed logging:

```bash
# Local development
FASTMCP_DEBUG=true uv run github-oauth-server

# Docker
docker run -e FASTMCP_DEBUG=true -p 8000:8000 fastmcp-github-oauth-example
```

### Health Monitoring

The server includes a comprehensive health check endpoint:

```bash
# Check server health
curl http://localhost:8000/health

# Expected response
{
  "status": "healthy",
  "service": "fastmcp-github-oauth",
  "version": "0.1.0"
}

# Docker health check
docker inspect --format='{{.State.Health.Status}}' container_name
```

### Build Debugging

```bash
# Test GoReleaser configuration
goreleaser check

# Build snapshot without Docker
goreleaser build --snapshot --clean --skip-docker

# Build with verbose output
goreleaser release --snapshot --clean --debug
```

## Contributing

This is an example project for demonstration purposes. For contributions to FastMCP itself, see the main [FastMCP repository](https://github.com/jlowin/fastmcp).

## License

This example is provided under the MIT License.

## Resources

- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP GitHub OAuth Integration](https://gofastmcp.com/integrations/github)  
- [GitHub OAuth Apps Guide](https://docs.github.com/en/apps/oauth-apps)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [uv Python Package Manager](https://github.com/astral-sh/uv)
- [GoReleaser Documentation](https://goreleaser.com)
- [GoReleaser uv Builder](https://goreleaser.com/customization/builds/uv/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
```

### Success Criteria:

#### Automated Verification:
- [ ] README renders correctly in markdown
- [ ] All code examples are syntactically valid
- [ ] Links are accessible (manual verification)
- [ ] Documentation covers GoReleaser wheel-based build process
- [ ] Architecture diagram reflects GoReleaser + uv approach

#### Manual Verification:
- [ ] Setup instructions are clear and complete
- [ ] Examples work as documented using MCP Inspector
- [ ] Troubleshooting section addresses wheel build issues
- [ ] Documentation follows consistent formatting
- [ ] Build process explanation is accurate and helpful

---

## Testing Strategy

### Unit Tests:
- Server initialization and configuration validation
- OAuth provider setup with mock credentials
- Tool registration and response validation
- Error handling for missing environment variables
- Health endpoint functionality

### Integration Tests:
- Full OAuth flow with mock GitHub responses
- MCP protocol compliance testing
- Docker container startup and health checks
- Multi-architecture image compatibility
- GoReleaser wheel build and Docker integration

### Manual Testing Steps:
1. Create GitHub OAuth app and configure environment
2. Build and start server locally with uv
3. Test health endpoint and MCP discovery
4. Test GoReleaser wheel build: `goreleaser build --snapshot --clean`
5. Verify wheel is available in Docker build context
6. Build Docker image and run container
7. Test OAuth flow end-to-end using MCP Inspector
8. Verify all tools return expected authenticated data
9. Test container restart and configuration changes
10. Validate GoReleaser builds and Docker publishing with wheel artifacts

## Performance Considerations

- FastMCP handles HTTP transport efficiently with async/await
- OAuth tokens are cached by clients to minimize auth requests  
- Container uses single-stage build with pre-built wheel for faster startup
- GoReleaser wheel build eliminates compilation time in Docker
- Health checks prevent routing to unhealthy containers
- uv provides fast dependency resolution and installation
- Multi-arch images optimized for their respective platforms

## Security Considerations

- Client secrets must never be committed to version control
- OAuth tokens are handled securely by FastMCP framework
- Container runs as non-root user for security
- HTTPS should be used in production environments
- Callback URLs should be validated and whitelisted
- Regular security updates for base images and dependencies
- Pre-built wheels reduce attack surface by eliminating build tools in runtime

## References

- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP GitHub OAuth Integration](https://gofastmcp.com/integrations/github)  
- [GitHub OAuth Apps](https://docs.github.com/en/apps/oauth-apps)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [uv Python Package Manager](https://github.com/astral-sh/uv)
- [GoReleaser Documentation](https://goreleaser.com)
- [GoReleaser uv Builder](https://goreleaser.com/customization/builds/uv/)
- [GoReleaser Docker Integration](https://goreleaser.com/customization/docker/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
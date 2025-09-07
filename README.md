# FastMCP GitHub OAuth Example

An example MCP (Model Context Protocol) server demonstrating GitHub OAuth authentication using the FastMCP framework. This project showcases how to build, package, and containerize an authenticated MCP server using modern Python tooling with uv and GoReleaser's wheel-based Docker builds.

## Features

- GitHub OAuth 2.0 authentication
- HTTP-streamable MCP server
- Protected tools that use GitHub user data
- Modern Python packaging with uv
- Docker containerization with multi-arch support
- Automated releases with GoReleaser using pre-built wheels
- Health monitoring and logging
- Development and production ready

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
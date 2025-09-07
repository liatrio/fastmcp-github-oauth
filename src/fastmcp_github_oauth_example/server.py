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
        return JSONResponse(
            {"status": "healthy", "service": "fastmcp-github-oauth", "version": "0.1.0"}
        )

    return Route("/health", health, methods=["GET"])


def create_server():
    """Create and configure the FastMCP server."""

    # Validate required environment variables
    required_env_vars = ["GITHUB_CLIENT_ID", "GITHUB_CLIENT_SECRET"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Initialize GitHub OAuth provider
    auth_provider = GitHubProvider(
        client_id=os.getenv("GITHUB_CLIENT_ID"),
        client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
        base_url=os.getenv("BASE_URL", "http://localhost:8000"),
        redirect_path="/auth/callback",
        required_scopes=["user:email"],  # Request email access
    )

    # Create FastMCP server with authentication
    mcp = FastMCP(
        name="GitHub OAuth Example Server",
        auth=auth_provider,
        routes=[create_health_endpoint()],  # Add health check
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
            "updated_at": token.claims.get("updated_at"),
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
                "oauth_callback": "/auth/callback",
            },
            "supported_architectures": ["linux/amd64", "linux/arm64"],
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
            "base_url": os.getenv("BASE_URL", "http://localhost:8000"),
        }

    @mcp.tool
    async def ping() -> Dict[str, Any]:
        """Simple ping endpoint for testing connectivity."""
        return {
            "message": "pong",
            "timestamp": "{{ .Date }}",
            "server": "FastMCP GitHub OAuth Example",
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
        print(
            "📋 Available Tools: get_user_info, get_server_info, get_oauth_status, ping"
        )

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

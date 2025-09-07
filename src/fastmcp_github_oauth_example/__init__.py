"""
FastMCP GitHub OAuth Example

An example MCP server demonstrating GitHub OAuth authentication using FastMCP.
Packaged with uv and containerized with GoReleaser using pre-built wheels.
"""

__version__ = "0.1.0"
__author__ = "FastMCP Contributors"

from .server import create_server, main

__all__ = ["create_server", "main"]

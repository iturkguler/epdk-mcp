"""EPDK MCP — Türk EPDK elektrik piyasası MCP server."""

__version__ = "0.1.0"

from .server import mcp, run

__all__ = ["mcp", "run", "__version__"]

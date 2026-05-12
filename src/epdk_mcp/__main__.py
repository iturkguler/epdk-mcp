"""EPDK MCP entry point — `python -m epdk_mcp` veya `epdk-mcp` komutuyla başlar."""

from __future__ import annotations

from .server import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()

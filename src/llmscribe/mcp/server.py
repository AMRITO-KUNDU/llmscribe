"""LLMScribe MCP server.

Runs the seven deterministic project tools over the Model Context Protocol on
stdio, so local clients such as Claude Desktop and Cursor can use them against a
local project directory.

Local-access configuration: every local path is allowed by default;
``MCP_ALLOWED_ROOTS`` (a list of directories separated by ``os.pathsep``)
restricts access to those, and ``MCP_ALLOW_LOCAL_PATHS=0`` disables local paths.
Run: ``llmscribe-mcp`` or ``python -m llmscribe.mcp``.
"""

from __future__ import annotations

import inspect
import logging
import sys
from typing import Any

from llmscribe import __version__
from llmscribe.mcp.tools import (
    TOOL_FUNCTIONS,
    local_roots_from_env,
    project_dependencies,
    project_diff,
    project_map,
    project_overview,
    read,
    read_many,
    search,
    set_local_roots,
)
from llmscribe.service import TOOLS

logger = logging.getLogger("llmscribe.mcp")

# Official MCP Python SDK: ``MCPServer`` in newer releases, ``FastMCP`` in 1.x.
try:
    from mcp.server import MCPServer as _ServerClass  # type: ignore[attr-defined]

    MCP_BACKEND = "mcp (official SDK, MCPServer)"
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as _ServerClass

        MCP_BACKEND = "mcp (official SDK, FastMCP)"
    except ImportError as exc:  # pragma: no cover - mcp is a required dependency
        raise ImportError("The 'mcp' package is required: pip install mcp") from exc


def _parameters(callable_: Any) -> set[str]:
    try:
        return set(inspect.signature(callable_).parameters)
    except (TypeError, ValueError):  # pragma: no cover
        return set()


def _build_server() -> Any:
    """Create the MCP server and report the package version in the handshake."""
    kwargs: dict[str, Any] = {}
    accepted = _parameters(_ServerClass.__init__)
    if "version" in accepted:
        kwargs["version"] = __version__
    return _ServerClass("llmscribe", **kwargs)


mcp = _build_server()
for _name in TOOLS:
    mcp.tool()(TOOL_FUNCTIONS[_name])


def main() -> None:
    """Entry point for ``llmscribe-mcp``."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", stream=sys.stderr)
    set_local_roots(local_roots_from_env())
    logger.info("Starting LLMScribe MCP %s (stdio)", __version__)
    mcp.run()


__all__ = [
    "main",
    "mcp",
    "project_dependencies",
    "project_diff",
    "project_map",
    "project_overview",
    "read",
    "read_many",
    "search",
]

if __name__ == "__main__":
    main()

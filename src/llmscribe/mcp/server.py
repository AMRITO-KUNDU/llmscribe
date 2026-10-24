"""LLMScribe MCP server.

Transports (``MCP_TRANSPORT``):
  stdio (default)  local clients such as Claude Desktop and Cursor
  http             hosted Streamable HTTP server: ``/mcp``, ``/health``, ``/info``

Hosted configuration: ``HOST`` (default 0.0.0.0), ``PORT`` (default 8000),
``MCP_ALLOWED_HOSTS``, ``MCP_ALLOWED_ORIGINS``, ``MCP_ALLOW_LOCAL_PATHS`` /
``MCP_ALLOWED_ROOTS`` (see README). Run: ``llmscribe-mcp`` or ``python -m llmscribe.mcp``.
"""

from __future__ import annotations

import inspect
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

from llmscribe import __version__
from llmscribe.mcp import asgi as http_layer
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
    """Create the MCP server; the SDK's own host check is off because ``http.SecurityMiddleware`` enforces it."""
    kwargs: dict[str, Any] = {}
    accepted = _parameters(_ServerClass.__init__)
    if "version" in accepted:
        kwargs["version"] = __version__
    if "streamable_http_path" in accepted:
        kwargs["streamable_http_path"] = "/"
    if "transport_security" in accepted:
        try:
            from mcp.server.transport_security import TransportSecuritySettings

            kwargs["transport_security"] = TransportSecuritySettings(enable_dns_rebinding_protection=False)
        except ImportError:  # pragma: no cover - older SDK without the feature
            pass
    return _ServerClass("llmscribe", **kwargs)


mcp = _build_server()
for _name in TOOLS:
    mcp.tool()(TOOL_FUNCTIONS[_name])


def _sdk_http_app() -> tuple[Any, bool]:
    """Return ``(asgi_app, strip_prefix)``: the SDK's Streamable HTTP app and whether it serves at ``/``."""
    factory = mcp.streamable_http_app
    kwargs: dict[str, Any] = {}
    if "streamable_http_path" in _parameters(factory):
        kwargs["streamable_http_path"] = "/"
    app = factory(**kwargs)
    configured = kwargs.get("streamable_http_path") or getattr(getattr(mcp, "settings", None), "streamable_http_path", "/")
    return app, configured == "/"


def create_app() -> Any:
    """Build the hosted ASGI app (call once per process)."""
    sdk_app, strip_prefix = _sdk_http_app()

    @asynccontextmanager
    async def lifespan():
        async with mcp.session_manager.run():
            logger.info("MCP session manager started")
            yield
        logger.info("MCP session manager stopped")

    return http_layer.HttpApp(
        sdk_app,
        version=__version__,
        backend=MCP_BACKEND,
        tools=list(TOOLS),
        allowed_hosts=http_layer.allowed_hosts_from_env(),
        allowed_origins=http_layer.allowed_origins_from_env(),
        lifespan=lifespan,
        strip_prefix=strip_prefix,
    )


_app: Any = None


def _get_app() -> Any:
    global _app
    if _app is None:
        _app = create_app()
    return _app


def __getattr__(name: str) -> Any:
    """``llmscribe.mcp.server.app`` (for ``uvicorn llmscribe.mcp.server:app``) is built on first access."""
    if name == "app":
        return _get_app()
    raise AttributeError(name)


def _transport() -> str:
    raw = os.environ.get("MCP_TRANSPORT", "").strip().lower()
    if raw in ("stdio", "http"):
        return raw
    if raw:
        raise SystemExit(f"llmscribe-mcp: MCP_TRANSPORT must be 'stdio' or 'http', got '{raw}'.")
    if os.environ.get("PORT"):
        print("llmscribe-mcp: PORT is set without MCP_TRANSPORT; using http. Set MCP_TRANSPORT=http explicitly.", file=sys.stderr)
        return "http"
    return "stdio"


def main() -> None:
    """Entry point for ``llmscribe-mcp``."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s", stream=sys.stderr)
    transport = _transport()
    roots = local_roots_from_env(http_mode=transport == "http")
    set_local_roots(roots)

    if transport == "stdio":
        logger.info("Starting LLMScribe MCP %s (stdio)", __version__)
        mcp.run()
        return

    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    try:
        port = int(os.environ.get("PORT", "8000"))
    except ValueError:
        raise SystemExit("llmscribe-mcp: PORT must be an integer.") from None
    logger.info("Starting LLMScribe MCP %s (http) on %s:%s — MCP at /mcp, health at /health", __version__, host, port)
    logger.info("Local path access: %s", "unrestricted" if roots is None else (f"{len(roots)} allowed root(s)" if roots else "disabled"))
    uvicorn.run(
        _get_app(),
        host=host,
        port=port,
        log_level="info",
        timeout_keep_alive=5,
        timeout_graceful_shutdown=10,
    )


__all__ = [
    "main",
    "mcp",
    "create_app",
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

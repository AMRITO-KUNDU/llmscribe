"""Entry point for ``llmscribe-mcp``.

The MCP server lives behind the ``server`` extra, so the core package can be installed
without pulling in `mcp` and its 155 transitive dependencies. This shim exists so a
missing extra produces an instruction instead of a bare ImportError.
"""

from __future__ import annotations

import sys

INSTALL_HINT = (
    "The MCP server is not installed.\n"
    "Install it with:\n"
    "    pip install 'llmscribe[server]'\n"
    "(or `pip install mcp pydantic` if you manage dependencies yourself)"
)


def main() -> int:
    try:
        from llmscribe.mcp.server import main as serve
    except ModuleNotFoundError as exc:
        if exc.name in {"mcp", "pydantic"}:
            print(INSTALL_HINT, file=sys.stderr)
            return 1
        raise
    serve()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

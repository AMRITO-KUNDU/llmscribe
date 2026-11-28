"""Entry point for ``llmscribe-mcp``.

The MCP server lives behind the ``server`` extra, so the core package can be installed
without pulling in `mcp` and its 155 transitive dependencies. This shim exists so a
missing extra produces an instruction instead of a bare ImportError.
"""

from __future__ import annotations

import os
import sys

USAGE = """usage: llmscribe-mcp [--read-only]

  --read-only   serve only the tools that cannot change the filesystem
"""

INSTALL_HINT = (
    "The MCP server is not installed.\n"
    "Install it with:\n"
    "    pip install 'llmscribe[server]'\n"
    "(or `pip install mcp pydantic` if you manage dependencies yourself)"
)


def main() -> int:
    # The server registers its tools at import time, so the flag has to be in the
    # environment before the import below - not after.
    if "--read-only" in sys.argv[1:]:
        os.environ["LLMSCRIBE_READ_ONLY"] = "1"
        sys.argv = [arg for arg in sys.argv if arg != "--read-only"]

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

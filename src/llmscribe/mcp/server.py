"""
LLMScribe MCP Server – Clean FastAPI + MCP implementation

Endpoints:
  GET|HEAD /health   → health check (HEAD for Render / load-balancer probes)
  GET|HEAD /         → root status
  GET      /info     → server info
  /mcp               → MCP Streamable HTTP endpoint (for Cursor, Claude, etc.)

Run modes:
  MCP_TRANSPORT=http  → FastAPI HTTP server (Railway / production)
  MCP_TRANSPORT=stdio → classic stdio (local Cursor / Claude Desktop)
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from llmscribe import __version__

CANONICAL_VERSION = __version__

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("llmscribe.mcp")

# ------------------------------------------------------------------
# MCP import — prefer the official SDK, fall back to standalone fastmcp.
#
# Official SDK (py.sdk.modelcontextprotocol.io):
#   from mcp.server import MCPServer          # canonical name
#   from mcp.server.fastmcp import FastMCP    # older alias, same class
#   ASGI method:  mcp.streamable_http_app()
#
# Standalone fastmcp (PrefectHQ/fastmcp):
#   from fastmcp import FastMCP
#   ASGI method:  mcp.http_app()              # streamable_http_app() is deprecated
# ------------------------------------------------------------------
_MCP_BACKEND: str

try:
    from mcp.server import MCPServer as MCPServerClass  # type: ignore
    _MCP_BACKEND = "mcp.server (official SDK, MCPServer)"
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP as MCPServerClass  # type: ignore
        _MCP_BACKEND = "mcp.server.fastmcp (official SDK, FastMCP)"
    except ImportError:
        try:
            from fastmcp import FastMCP as MCPServerClass  # type: ignore
            _MCP_BACKEND = "fastmcp (standalone)"
        except ImportError as exc:
            raise ImportError(
                "No MCP server library found. Install one of:\n"
                "  pip install mcp        # official SDK\n"
                "  pip install fastmcp    # standalone\n"
            ) from exc

logger.info("Using MCP backend: %s", _MCP_BACKEND)

from llmscribe.core import (
    analyze_dependencies,
    get_git_diff,
    project_map as core_project_map,
    project_overview as core_project_overview,
    read_file,
    read_files,
    search_project,
)
from llmscribe.github.client import parse_github_repo
from llmscribe.github.provider import (
    github_project_diff,
    github_project_get_file,
    github_project_get_files,
    github_project_map,
    github_project_overview,
    github_project_search,
)

# ------------------------------------------------------------------
# Create MCP server
# ------------------------------------------------------------------
# ``streamable_http_path="/"`` makes the MCP endpoint live at the root of
# whatever path the app is mounted at.  Mounting at ``/mcp`` then gives a
# public URL of exactly ``/mcp`` (not ``/mcp/mcp``).  See official docs:
# https://py.sdk.modelcontextprotocol.io/run/asgi/
try:
    mcp = MCPServerClass("llmscribe")
except TypeError:
    # Standalone fastmcp may not accept any constructor args here.
    mcp = MCPServerClass("llmscribe")

MAX_CONTENT_CHARS = 400_000
GET_FILES_MAX_FILES = 50


class ProjectRootError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _resolve_project_root(path: Optional[str] = None) -> Path:
    if path and path.strip():
        resolved = Path(path).resolve()
    else:
        resolved = Path.cwd().resolve()
    if not resolved.exists():
        raise ProjectRootError("invalid_path", f"Directory does not exist: '{resolved}'")
    if not resolved.is_dir():
        raise ProjectRootError("not_a_directory", f"Path is not a directory: '{resolved}'")
    return resolved


def _validate_path_repo_mutual_exclusive(path: Optional[str], repo: Optional[str]) -> None:
    if path and path.strip() and repo and repo.strip():
        raise ProjectRootError(
            "invalid_argument",
            "Cannot specify both 'path' and 'repo'.",
        )


def _parse_repo(repo_str: str) -> tuple[str, str]:
    return parse_github_repo(repo_str)


def _json_ok(tool: str, path: str, data: Any, metadata: Optional[dict[str, Any]] = None) -> str:
    payload: dict[str, Any] = {"ok": True, "tool": tool, "path": path, "data": data}
    if metadata is not None:
        payload["metadata"] = metadata
    return json.dumps(payload, indent=2)


def _json_err(tool: str, code: str, message: str) -> str:
    return json.dumps({"ok": False, "tool": tool, "error": {"code": code, "message": message}}, indent=2)


def _is_json(fmt: str) -> bool:
    return fmt.strip().lower() == "json"


def _md_header(tool: str, path: str) -> str:
    return f"### llmscribe: {tool}\nPath: {path}\n\n"


def _md_error(tool: str, code: str, message: str) -> str:
    return f"### llmscribe: {tool}\nError [{code}]: {message}"


# ------------------------------------------------------------------
# Tools (unchanged)
# ------------------------------------------------------------------

@mcp.tool()
def project_map(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return directory tree structure without file contents."""
    tool = "project_map"
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            owner, name = _parse_repo(repo)
            return github_project_map(owner, name, ref, format)
        root = _resolve_project_root(path)
        result = core_project_map(root)
        if _is_json(format):
            return _json_ok(tool, root.as_posix(), result.to_dict(), {
                "file_count": result.file_count,
                "character_count": result.character_count,
            })
        return f"{_md_header(tool, root.as_posix())}Selected Files Directory Structure:\n\n{result.tree}"
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


@mcp.tool()
def project_overview(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full directory tree + file contents."""
    tool = "project_overview"
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            owner, name = _parse_repo(repo)
            return github_project_overview(owner, name, ref, format)
        root = _resolve_project_root(path)
        result = core_project_overview(root, max_content_chars=MAX_CONTENT_CHARS)
        if _is_json(format):
            meta: dict[str, Any] = {"file_count": result.file_count, "character_count": result.character_count}
            if result.truncated:
                meta["truncated"] = True
                meta["truncation_note"] = result.truncation_note
            return _json_ok(tool, root.as_posix(), result.to_dict(), meta)
        files_md = "\n\n".join(f"--- {f['path']} ---\n{f['content']}" for f in result.files)
        text = f"Selected Files Directory Structure:\n\n{result.tree}\n\nFile Contents:\n{files_md}"
        if result.truncated:
            text += f"\n\n[{result.truncation_note}]"
        return f"{_md_header(tool, root.as_posix())}{text}"
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


@mcp.tool()
def search(
    query: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Search filenames and file contents."""
    tool = "search"
    if not query or not query.strip():
        return _json_err(tool, "empty_query", "Query cannot be empty.") if _is_json(format) else _md_error(tool, "empty_query", "Query cannot be empty.")
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            owner, name = _parse_repo(repo)
            return github_project_search(query, owner, name, ref, format)
        root = _resolve_project_root(path)
        result = search_project(query, root, max_results=1000)
        if _is_json(format):
            return _json_ok(tool, root.as_posix(), result.to_dict(), {
                "query": result.query,
                "file_count": result.file_count,
                "match_count": result.match_count,
                "truncated": result.truncated,
            })
        if not result.matches:
            return f"{_md_header(tool, root.as_posix())}No matches for '{result.query}'"
        by_file: dict[str, list] = {}
        for m in result.matches:
            by_file.setdefault(m.file_path, []).append(m)
        parts = []
        for fp, matches in sorted(by_file.items()):
            entry = [f"File: {fp}"]
            content = [m for m in matches if m.match_type == "content"]
            if any(m.match_type == "filename" for m in matches) and not content:
                entry.append("  (Filename match)")
            for m in content[:10]:
                entry.append(f"  Line {m.line_number}: {m.line_content}")
            if len(content) > 10:
                entry.append(f"  ... ({len(content)-10} more)")
            parts.append("\n".join(entry))
        return f"{_md_header(tool, root.as_posix())}Search results for '{result.query}':\n\n" + "\n\n".join(parts)
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


@mcp.tool()
def read(
    file_path: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Read a single file with path-traversal protection."""
    tool = "read"
    if not file_path or not file_path.strip():
        return _json_err(tool, "invalid_argument", "file_path required.") if _is_json(format) else _md_error(tool, "invalid_argument", "file_path required.")
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            owner, name = _parse_repo(repo)
            return github_project_get_file(file_path, owner, name, ref, format)
        root = _resolve_project_root(path)
        result = read_file(file_path, root, max_content_chars=MAX_CONTENT_CHARS)
        if not result.ok:
            return _json_err(tool, result.error_code, result.error_message) if _is_json(format) else _md_error(tool, result.error_code, result.error_message)
        if _is_json(format):
            return _json_ok(tool, root.as_posix(), result.to_dict(), {"character_count": result.character_count})
        return f"{_md_header(tool, root.as_posix())}--- {result.file_path} ---\n{result.content}"
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


@mcp.tool()
def read_many(
    file_paths: list[str],
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Read multiple files in one call."""
    tool = "read_many"
    if not file_paths:
        return _json_err(tool, "invalid_argument", "file_paths cannot be empty.") if _is_json(format) else _md_error(tool, "invalid_argument", "file_paths cannot be empty.")
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            owner, name = _parse_repo(repo)
            return github_project_get_files(file_paths, owner, name, ref, format)
        root = _resolve_project_root(path)
        result = read_files(file_paths, root, max_files=GET_FILES_MAX_FILES, max_content_chars=MAX_CONTENT_CHARS)
        if _is_json(format):
            meta = {
                "file_count": result.file_count,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "character_count": result.character_count,
            }
            if result.truncated:
                meta["truncated"] = True
            return _json_ok(tool, root.as_posix(), result.to_dict(), meta)
        parts = []
        for fr in result.results:
            if fr.ok:
                parts.append(f"--- {fr.file_path} ---\n{fr.content}")
            else:
                parts.append(f"--- {fr.file_path} ---\nError [{fr.error_code}]: {fr.error_message}")
        out = f"{_md_header(tool, root.as_posix())}" + "\n\n".join(parts)
        if result.truncated:
            out += f"\n\n[{result.truncation_note}]"
        return out
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


@mcp.tool()
def project_dependencies(
    file_path: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Analyze local file dependencies."""
    tool = "project_dependencies"
    if not file_path or not file_path.strip():
        return _json_err(tool, "invalid_argument", "file_path required.") if _is_json(format) else _md_error(tool, "invalid_argument", "file_path required.")
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            msg = "GitHub support for project_dependencies not yet implemented."
            return _json_err(tool, "not_implemented", msg) if _is_json(format) else _md_error(tool, "not_implemented", msg)
        root = _resolve_project_root(path)
        result = analyze_dependencies(file_path, root)
        if _is_json(format):
            unresolved = getattr(result, "all_unresolved_deps", [])
            return _json_ok(tool, root.as_posix(), result.to_dict(), {
                "file_count": len(result.all_local_files),
                "external_dep_count": len(result.all_external_deps),
                "unresolved_count": len(unresolved) if isinstance(unresolved, (list, tuple, set)) else 0,
            })
        md = [f"File: {result.target_file}"]
        fd = result.file_dependencies
        if fd.imports:
            md.append(f"\nImports: {', '.join(fd.imports)}")
        if fd.local_dependencies:
            md.append(f"\nLocal Dependencies: {', '.join(fd.local_dependencies)}")
        if fd.external_dependencies:
            md.append(f"\nExternal Dependencies: {', '.join(fd.external_dependencies)}")
        if result.all_local_files:
            md.append(f"\nFiles that depend on this: {', '.join(result.all_local_files)}")
        return f"{_md_header(tool, root.as_posix())}" + "\n".join(md)
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


@mcp.tool()
def project_diff(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    staged: bool = False,
    commit: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Show git status and unified diff."""
    tool = "project_diff"
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        if repo and repo.strip():
            owner, name = _parse_repo(repo)
            return github_project_diff(commit, staged, owner, name, ref, format)
        root = _resolve_project_root(path)
        result = get_git_diff(root, staged=staged, commit=commit, max_diff_chars=200_000)
        if _is_json(format):
            return _json_ok(tool, root.as_posix(), {
                "staged": result.staged,
                "commit": result.commit,
                "changed_files": result.changed_files,
                "diff": result.diff,
                "truncated": result.truncated,
            }, {
                "changed_file_count": len(result.changed_files),
                "character_count": len(result.diff),
                "truncated": result.truncated,
            })
        md = [f"{_md_header(tool, root.as_posix())}### Git Status & Diff"]
        if result.changed_files:
            md.append("Changed Files:\n" + "\n".join(f"- {f}" for f in result.changed_files))
        else:
            md.append("No changed files.")
        if result.diff.strip():
            md.append(f"\nDiff:\n```diff\n{result.diff}\n```")
        else:
            md.append("\nDiff is empty.")
        return "\n\n".join(md)
    except ProjectRootError as e:
        return _json_err(tool, e.code, e.message) if _is_json(format) else _md_error(tool, e.code, e.message)
    except RuntimeError as e:
        code = "git_unavailable" if "git" in str(e).lower() else "internal_error"
        return _json_err(tool, code, str(e)) if _is_json(format) else _md_error(tool, code, str(e))
    except Exception as e:
        return _json_err(tool, "internal_error", str(e)) if _is_json(format) else _md_error(tool, "internal_error", str(e))


# Backward compatibility aliases for older tool import references
project_get_file = read
project_get_files = read_many
project_search = search
project_list_files = project_map


# ------------------------------------------------------------------
# ASGI app construction
#
# Feature-detection is used instead of a blind try/except chain so that a
# missing method is never re-called, and the error message names what the
# installed class actually offers.
# ------------------------------------------------------------------

def _build_transport_security() -> Optional[Any]:
    """
    Build TransportSecuritySettings for production.

    Without this, the MCP SDK rejects non-localhost requests with:
      - 421 Invalid Host header
      - 403 Invalid Origin header

    Env:
      MCP_ALLOWED_HOSTS              comma-separated Host values
      MCP_ALLOWED_ORIGINS            comma-separated Origin values
      MCP_DISABLE_DNS_REBINDING=1    turn protection off entirely (last resort)
    """
    try:
        from mcp.server.transport_security import TransportSecuritySettings
    except ImportError:
        logger.warning("mcp.server.transport_security not available; skipping host allowlist")
        return None

    if os.environ.get("MCP_DISABLE_DNS_REBINDING", "").strip().lower() in ("1", "true", "yes"):
        logger.warning("DNS rebinding protection DISABLED via MCP_DISABLE_DNS_REBINDING")
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)

    raw_hosts = os.environ.get("MCP_ALLOWED_HOSTS", "").strip()
    if raw_hosts:
        allowed_hosts = [h.strip() for h in raw_hosts.split(",") if h.strip()]
    else:
        allowed_hosts = [
            "localhost",
            "localhost:*",
            "127.0.0.1",
            "127.0.0.1:*",
            "[::1]",
            "[::1]:*",
            "0.0.0.0",
            "0.0.0.0:*",
            "llmscribe.onrender.com",
            "llmscribe.onrender.com:*",
        ]
        for env_key in (
            "RENDER_EXTERNAL_HOSTNAME",
            "RAILWAY_PUBLIC_DOMAIN",
            "RAILWAY_STATIC_URL",
            "HOST",
        ):
            val = os.environ.get(env_key, "").strip()
            # Strip scheme if present (RAILWAY_STATIC_URL is a full URL)
            if val.startswith("http://") or val.startswith("https://"):
                val = val.split("://", 1)[1].split("/")[0]
            if val and val not in allowed_hosts:
                allowed_hosts.append(val)
                allowed_hosts.append(f"{val}:*")

    raw_origins = os.environ.get("MCP_ALLOWED_ORIGINS", "").strip()
    if raw_origins:
        allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
    else:
        # Broad but practical defaults for public MCP + common clients.
        # "*" is included because some SDK versions honour it; explicit
        # origins cover those that do not.
        allowed_origins = [
            "*",
            "https://llmscribe.onrender.com",
            "http://llmscribe.onrender.com",
            "https://claude.ai",
            "https://www.claude.ai",
            "https://cursor.com",
            "https://www.cursor.com",
            "http://localhost",
            "http://localhost:*",
            "http://127.0.0.1",
            "http://127.0.0.1:*",
            "null",  # some clients send Origin: null
        ]

    logger.info("MCP transport_security hosts=%s origins=%s", allowed_hosts, allowed_origins)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def _build_mcp_asgi_app() -> Any:
    """
    Return the ASGI app for the mounted MCP server.

    Forces streamable_http_path="/" so the public URL is /mcp (not /mcp/mcp).
    Passes transport_security so production Host/Origin headers are accepted.
    """
    security = _build_transport_security()
    kwargs: dict[str, Any] = {"streamable_http_path": "/"}
    if security is not None:
        kwargs["transport_security"] = security

    def _call_with_fallback(fn: Any, label: str) -> Any:
        for attempt in (kwargs, {"streamable_http_path": "/"}, {}):
            try:
                result = fn(**attempt) if attempt else fn()
                logger.info("Using %s (kwargs=%s)", label, list(attempt.keys()) or "none")
                return result
            except TypeError:
                continue
        return fn()

    http_app = getattr(mcp, "http_app", None)
    if callable(http_app):
        return _call_with_fallback(http_app, "mcp.http_app() (standalone fastmcp)")

    streamable = getattr(mcp, "streamable_http_app", None)
    if callable(streamable):
        return _call_with_fallback(streamable, "mcp.streamable_http_app() (official SDK)")

    sse = getattr(mcp, "sse_app", None)
    if callable(sse):
        logger.info("Using mcp.sse_app() (legacy SSE transport)")
        return sse()

    raise RuntimeError(
        "The installed MCP server class exposes no ASGI app method. "
        "Expected one of: http_app, streamable_http_app, sse_app. "
        f"Got: {type(mcp).__module__}.{type(mcp).__name__}"
    )


class _McpPathDispatch:
    """
    Top-level ASGI dispatcher: route /mcp and /mcp/* to the MCP app,
    everything else to FastAPI.

    Does not rely on Starlette Mount matching (which 404s on exact /mcp
    when redirect_slashes=False). Both /mcp and /mcp/ become path "/" for
    the Streamable HTTP sub-app.
    """

    def __init__(self, fastapi_app: Any, mcp_app: Any, prefix: str = "/mcp") -> None:
        self.fastapi_app = fastapi_app
        self.mcp_app = mcp_app
        self.prefix = prefix.rstrip("/") or "/mcp"

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        # Lifespan must reach FastAPI so mcp.session_manager.run() starts.
        if scope["type"] == "lifespan":
            await self.fastapi_app(scope, receive, send)
            return

        if scope["type"] in ("http", "websocket"):
            path = scope.get("path") or ""
            prefix = self.prefix
            if path == prefix or path.startswith(prefix + "/"):
                rest = path[len(prefix):] or "/"
                if not rest.startswith("/"):
                    rest = "/" + rest
                mcp_scope = dict(scope)
                mcp_scope["path"] = rest
                mcp_scope["raw_path"] = rest.encode("utf-8")
                await self.mcp_app(mcp_scope, receive, send)
                return

        await self.fastapi_app(scope, receive, send)


def create_app() -> Any:
    """Create ASGI app: FastAPI health routes + MCP at /mcp and /mcp/."""

    mcp_asgi = _build_mcp_asgi_app()

    # Host app lifespan MUST enter mcp.session_manager.run().
    # See: https://py.sdk.modelcontextprotocol.io/run/asgi/
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        session_mgr = getattr(mcp, "session_manager", None)
        if session_mgr is None:
            logger.warning(
                "mcp.session_manager not found. Tool calls will fail with "
                "'Task group is not initialized'. This usually means the "
                "ASGI app was not built before the lifespan ran."
            )
            yield
            return

        async with AsyncExitStack() as stack:
            await stack.enter_async_context(session_mgr.run())
            logger.info("MCP session manager started")
            yield
        logger.info("MCP session manager stopped")

    fastapi_app = FastAPI(
        title="LLMScribe MCP Server",
        description="Deterministic code-context tools for AI agents",
        version=CANONICAL_VERSION,
        lifespan=lifespan,
        redirect_slashes=False,
    )

    _root_body = {
        "status": "healthy",
        "server": "LLMScribe MCP Server",
        "version": CANONICAL_VERSION,
        "mcp_backend": _MCP_BACKEND,
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "mcp": "/mcp",
        },
    }

    _health_body = {
        "status": "healthy",
        "server": "LLMScribe MCP",
        "version": CANONICAL_VERSION,
        "mcp_backend": _MCP_BACKEND,
        "tools": [
            "project_map", "project_overview", "search",
            "read", "read_many", "project_dependencies", "project_diff",
        ],
    }

    @fastapi_app.api_route("/", methods=["GET", "HEAD"])
    async def root(request: Request):
        if request.method == "HEAD":
            return JSONResponse(content=None, status_code=200)
        return JSONResponse(_root_body)

    @fastapi_app.api_route("/health", methods=["GET", "HEAD"])
    async def health(request: Request):
        if request.method == "HEAD":
            return JSONResponse(content=None, status_code=200)
        return JSONResponse(_health_body)

    @fastapi_app.get("/info")
    async def info():
        return JSONResponse({
            "name": "LLMScribe",
            "description": "Code context infrastructure for AI agents",
            "version": CANONICAL_VERSION,
            "mcp_backend": _MCP_BACKEND,
            "mcp_endpoint": "/mcp",
            "tools": 7,
        })

    # Dispatch /mcp and /mcp/* to MCP; all other paths to FastAPI.
    return _McpPathDispatch(fastapi_app, mcp_asgi, prefix="/mcp")


app = create_app()


def main() -> None:
    raw_transport = os.environ.get("MCP_TRANSPORT", "").lower().strip()

    # Auto-detect cloud environment (Railway, Render, Heroku, Docker)
    is_cloud_env = bool(
        raw_transport in ("http", "sse")
        or os.environ.get("PORT")
        or os.environ.get("RAILWAY_SERVICE_ID")
        or os.environ.get("RAILWAY_STATIC_URL")
    )

    if is_cloud_env:
        host = os.environ.get("HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", "8000"))

        logger.info("=" * 50)
        logger.info("Starting LLMScribe MCP Server")
        logger.info("Backend   : %s", _MCP_BACKEND)
        logger.info("Mode      : HTTP (FastAPI + Streamable MCP)")
        logger.info("Listening : http://%s:%s", host, port)
        logger.info("Health    : http://%s:%s/health", host, port)
        logger.info("MCP URL   : http://%s:%s/mcp", host, port)
        logger.info("=" * 50)

        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
        )
    else:
        logger.info("Starting LLMScribe MCP in stdio mode")
        mcp.run()


if __name__ == "__main__":
    main()
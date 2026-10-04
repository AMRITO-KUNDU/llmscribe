"""
LLMScribe MCP Server – Clean FastAPI + MCP implementation

Endpoints:
  GET  /health   → health check
  GET  /info     → server info
  /mcp           → MCP Streamable HTTP endpoint (for Cursor, Claude, etc.)

Run modes:
  MCP_TRANSPORT=http  → FastAPI HTTP server (Railway / production)
  MCP_TRANSPORT=stdio → classic stdio (local Cursor / Claude Desktop)
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("llmscribe.mcp")

# ------------------------------------------------------------------
# MCP import (works with both official mcp and fastmcp packages)
# ------------------------------------------------------------------
try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    try:
        from fastmcp import FastMCP
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP  # type: ignore
        except ImportError:
            from mcp.server import FastMCP  # type: ignore

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
mcp = FastMCP("llmscribe")

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
# Tools
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
            meta = {"file_count": result.file_count, "character_count": result.character_count}
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
# FastAPI app + proper MCP mounting
# ------------------------------------------------------------------

def create_app() -> FastAPI:
    """Create FastAPI app with MCP mounted at /mcp."""

    # Get the MCP ASGI app
    try:
        mcp_asgi = mcp.streamable_http_app()
    except Exception:
        try:
            mcp_asgi = mcp.http_app(path="/")
        except Exception:
            mcp_asgi = mcp.http_app()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if hasattr(mcp, "session_manager"):
            async with mcp.session_manager.run():
                logger.info("MCP session manager started")
                yield
        else:
            yield

    app = FastAPI(
        title="LLMScribe MCP Server",
        description="Deterministic code-context tools for AI agents",
        version="1.2.0",
        lifespan=lifespan,
    )

    @app.get("/")
    async def root():
        return JSONResponse({
            "status": "healthy",
            "server": "LLMScribe MCP Server",
            "version": "1.2.0",
            "endpoints": {
                "health": "/health",
                "info": "/info",
                "mcp": "/mcp",
            },
        })

    @app.get("/health")
    async def health():
        return JSONResponse({
            "status": "healthy",
            "server": "LLMScribe MCP",
            "version": "1.2.0",
            "tools": [
                "project_map", "project_overview", "search",
                "read", "read_many", "project_dependencies", "project_diff",
            ],
        })

    @app.get("/info")
    async def info():
        return JSONResponse({
            "name": "LLMScribe",
            "description": "Code context infrastructure for AI agents",
            "version": "1.2.0",
            "mcp_endpoint": "/mcp",
            "tools": 7,
        })

    # Mount MCP at /mcp
    app.mount("/mcp", mcp_asgi)
    return app


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

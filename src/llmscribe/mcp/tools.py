"""The seven public LLMScribe tools as plain Python functions.

These functions contain no MCP-SDK code; ``server.py`` registers them. Each
returns a string (markdown by default, JSON with ``format="json"``) and never
raises: failures are returned as structured ``{"ok": false, "error": {...}}``
(or ``Error [code]: message`` in markdown).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any, Optional

from pydantic import Field

from llmscribe import service
from llmscribe.core.errors import LLMScribeError

# ``None`` = any local path (default); a list restricts local access (empty = disabled).
_local_roots: Optional[list[Path]] = None


def set_local_roots(roots: Optional[list[Path]]) -> None:
    """Restrict which local directories the tools may read (``None`` removes the restriction)."""
    global _local_roots
    _local_roots = None if roots is None else [Path(r).resolve() for r in roots]


def local_roots_from_env() -> Optional[list[Path]]:
    """Local-access policy, from the environment.

    By default every local path is allowed (LLMScribe runs on your own machine).
    ``MCP_ALLOWED_ROOTS`` (directories separated by ``os.pathsep``) restricts
    access to those directories; ``MCP_ALLOW_LOCAL_PATHS=0`` disables local
    paths entirely.
    """
    raw = os.environ.get("MCP_ALLOWED_ROOTS", "")
    if raw.strip():
        return [Path(p).resolve() for p in raw.split(os.pathsep) if p.strip()]
    if os.environ.get("MCP_ALLOW_LOCAL_PATHS", "").strip().lower() in ("0", "false", "no", "off"):
        return []
    return None


PathArg = Annotated[
    Optional[str],
    Field(description="Local project directory. Defaults to the server's working directory."),
]
FormatArg = Annotated[
    str,
    Field(description="Output format: 'markdown' (default) or 'json' (structured envelope)."),
]


def _run(tool: str, fmt: str, **kwargs: Any) -> str:
    fmt_clean = (fmt or "markdown").strip().lower()
    if fmt_clean not in ("markdown", "json"):
        return service.render_error(
            tool, LLMScribeError("invalid_argument", "format must be 'markdown' or 'json'."), as_json=False
        )
    return service.run(tool, fmt_clean == "json", allowed_roots=_local_roots, **kwargs)


def project_map(path: PathArg = None, format: FormatArg = "markdown") -> str:
    """Directory tree and the list of supported text files, without file contents.

    Respects default ignores and .gitignore files. Symlinks are not followed.
    """
    return _run("project_map", format, path=path)


def project_overview(path: PathArg = None, format: FormatArg = "markdown") -> str:
    """Directory tree plus the contents of supported text files.

    Output is capped at 400,000 characters of file content; when capped, the
    result says so and lists the omitted files.
    """
    return _run("project_overview", format, path=path)


def search(
    query: Annotated[str, Field(description="Text to find (case-insensitive substring) in file paths and file contents.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Deterministic substring search over file names and file contents.

    Results are ordered by path then line number and limited to 1,000 matches.
    Binary and oversized files are skipped. This is plain text matching, not semantic search.
    """
    return _run("search", format, path=path, query=query)


def read(
    file_path: Annotated[str, Field(description="Path of the file relative to the project root.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Read one text file. Paths cannot leave the root; binary and oversized files are rejected."""
    return _run("read", format, path=path, file_path=file_path)


def read_many(
    file_paths: Annotated[list[str], Field(description="Paths relative to the root. At most 50 are processed per call.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Read several text files in one call. A bad path yields an error entry; other files are still read."""
    return _run("read_many", format, path=path, file_paths=file_paths)


def project_dependencies(
    file_path: Annotated[str, Field(description="Source file to analyze, relative to the root.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Imports of one file (local, standard-library, external, unresolved) and the files that import it.

    Supports Python, JavaScript/TypeScript, Java, Go, Rust and C/C++.
    """
    return _run("project_dependencies", format, path=path, file_path=file_path)


def project_diff(
    path: PathArg = None,
    staged: Annotated[bool, Field(description="Show staged changes only.")] = False,
    commit: Annotated[Optional[str], Field(description="Revision to compare the working tree against.")] = None,
    format: FormatArg = "markdown",
) -> str:
    """Git status and unified diff of the working tree (vs HEAD, vs 'commit', or staged only)."""
    return _run("project_diff", format, path=path, staged=staged, commit=commit)


TOOL_FUNCTIONS = {
    "project_map": project_map,
    "project_overview": project_overview,
    "search": search,
    "read": read,
    "read_many": read_many,
    "project_dependencies": project_dependencies,
    "project_diff": project_diff,
}

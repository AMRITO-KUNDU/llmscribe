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

# ``None`` = any local path (stdio default); a list restricts local access (empty = disabled).
_local_roots: Optional[list[Path]] = None


def set_local_roots(roots: Optional[list[Path]]) -> None:
    """Restrict which local directories the tools may read (``None`` removes the restriction)."""
    global _local_roots
    _local_roots = None if roots is None else [Path(r).resolve() for r in roots]


def local_roots_from_env(http_mode: bool) -> Optional[list[Path]]:
    """Local-access policy: unrestricted over stdio; over HTTP disabled unless configured.

    ``MCP_ALLOW_LOCAL_PATHS=1`` allows any path; ``MCP_ALLOWED_ROOTS`` (a list of
    directories separated by ``os.pathsep``) allows only those.
    """
    if not http_mode:
        return None
    if os.environ.get("MCP_ALLOW_LOCAL_PATHS", "").strip().lower() in ("1", "true", "yes"):
        return None
    raw = os.environ.get("MCP_ALLOWED_ROOTS", "")
    return [Path(p).resolve() for p in raw.split(os.pathsep) if p.strip()]


PathArg = Annotated[
    Optional[str],
    Field(description="Local project directory. Defaults to the server's working directory. Mutually exclusive with 'repo'."),
]
RepoArg = Annotated[
    Optional[str],
    Field(description="Public GitHub repository ('owner/repo' or a github.com URL) instead of a local path."),
]
RefArg = Annotated[
    Optional[str],
    Field(description="Branch, tag or commit SHA for 'repo'. Defaults to the default branch. Only valid with 'repo'."),
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


def project_map(path: PathArg = None, repo: RepoArg = None, ref: RefArg = None, format: FormatArg = "markdown") -> str:
    """Directory tree and the list of supported text files, without file contents.

    Respects default ignores and .gitignore files. Symlinks are not followed.
    Works on a local directory or a public GitHub repository.
    """
    return _run("project_map", format, path=path, repo=repo, ref=ref)


def project_overview(path: PathArg = None, repo: RepoArg = None, ref: RefArg = None, format: FormatArg = "markdown") -> str:
    """Directory tree plus the contents of supported text files.

    Output is capped at 400,000 characters of file content; when capped, the
    result says so and lists the omitted files.
    """
    return _run("project_overview", format, path=path, repo=repo, ref=ref)


def search(
    query: Annotated[str, Field(description="Text to find (case-insensitive substring) in file paths and file contents.")],
    path: PathArg = None,
    repo: RepoArg = None,
    ref: RefArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Deterministic substring search over file names and file contents.

    Results are ordered by path then line number and limited to 1,000 matches.
    Binary and oversized files are skipped. This is plain text matching, not semantic search.
    """
    return _run("search", format, path=path, repo=repo, ref=ref, query=query)


def read(
    file_path: Annotated[str, Field(description="Path of the file relative to the project or repository root.")],
    path: PathArg = None,
    repo: RepoArg = None,
    ref: RefArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Read one text file. Paths cannot leave the root; binary and oversized files are rejected."""
    return _run("read", format, path=path, repo=repo, ref=ref, file_path=file_path)


def read_many(
    file_paths: Annotated[list[str], Field(description="Paths relative to the root. At most 50 are processed per call.")],
    path: PathArg = None,
    repo: RepoArg = None,
    ref: RefArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Read several text files in one call. A bad path yields an error entry; other files are still read."""
    return _run("read_many", format, path=path, repo=repo, ref=ref, file_paths=file_paths)


def project_dependencies(
    file_path: Annotated[str, Field(description="Source file to analyze, relative to the root.")],
    path: PathArg = None,
    repo: RepoArg = None,
    ref: RefArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Imports of one file (local, standard-library, external, unresolved) and the files that import it.

    Supports Python, JavaScript/TypeScript, Java, Go, Rust and C/C++. Works on a
    local directory or a public GitHub repository.
    """
    return _run("project_dependencies", format, path=path, repo=repo, ref=ref, file_path=file_path)


def project_diff(
    path: PathArg = None,
    repo: RepoArg = None,
    ref: RefArg = None,
    staged: Annotated[bool, Field(description="Local only: show staged changes only.")] = False,
    commit: Annotated[
        Optional[str],
        Field(description="Local: revision to compare the working tree against. GitHub: required base branch, tag or SHA."),
    ] = None,
    format: FormatArg = "markdown",
) -> str:
    """Git status and unified diff.

    Local: working tree vs HEAD (or vs 'commit', or staged only). GitHub: the
    changes from 'commit' to 'ref' (default branch) via the compare API.
    """
    return _run("project_diff", format, path=path, repo=repo, ref=ref, staged=staged, commit=commit)


TOOL_FUNCTIONS = {
    "project_map": project_map,
    "project_overview": project_overview,
    "search": search,
    "read": read,
    "read_many": read_many,
    "project_dependencies": project_dependencies,
    "project_diff": project_diff,
}

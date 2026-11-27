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


def project_map(
    path: PathArg = None,
    format: FormatArg = "markdown",
    depth: int | None = None,
    sizes: bool = False,
) -> str:
    """Directory tree and the list of supported text files, without file contents.

    Respects default ignores and .gitignore files. Symlinks are not followed.
    Set ``depth`` to list only the first N levels, like ``tree -L N``.
    """
    return _run("project_map", format, path=path, max_depth=depth, include_sizes=sizes)


def project_overview(
    path: PathArg = None,
    format: FormatArg = "markdown",
    depth: int | None = None,
    sizes: bool = False,
    max_tokens: Annotated[
        int | None,
        Field(description="Stop after roughly this many tokens (~4 characters each), taking files in path order."),
    ] = None,
    compress: Annotated[
        bool,
        Field(description="Reduce Python files to signatures and docstrings, dropping bodies. Default false."),
    ] = False,
) -> str:
    """Directory tree plus the contents of supported text files.

    Output is capped at 400,000 characters of file content; when capped, the
    result says so and lists the omitted files. Set ``depth`` to include only
    files within the first N levels, like ``tree -L N``. Set ``max_tokens`` to stop at
    a context budget instead; files are taken in path order, never by relevance.
    """
    return _run(
        "project_overview",
        format,
        path=path,
        max_depth=depth,
        include_sizes=sizes,
        max_tokens=max_tokens,
        compress=compress,
    )


def search(
    query: Annotated[str, Field(description="Text to find (case-insensitive substring) in file paths and file contents.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Substring search over file names and file contents.

    Results are ordered by path then line number and limited to 1,000 matches.
    Binary and oversized files are skipped. This is plain text matching, not semantic search.
    """
    return _run("search", format, path=path, query=query)


def read(
    file_path: Annotated[str, Field(description="Path of the file relative to the project root.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
    binary: Annotated[
        bool,
        Field(description="Read any file as base64 with its media type (images, PDFs). Default false."),
    ] = False,
    compress: Annotated[
        bool,
        Field(description="For .py files, return signatures and docstrings only. Default false."),
    ] = False,
    start_line: Annotated[
        int | None,
        Field(description="First line to return, 1-based. Use with end_line to read part of a large file."),
    ] = None,
    end_line: Annotated[
        int | None,
        Field(description="Last line to return, inclusive. Defaults to the end of the file."),
    ] = None,
) -> str:
    """Read one file. Paths cannot leave the root; oversized files are rejected.

    By default only recognised text files are read. Set ``binary`` to fetch any file
    as base64 with its guessed media type - use it when you specifically need to look
    at an image or a PDF, not to pull binaries into context.
    """
    return _run(
        "read",
        format,
        path=path,
        file_path=file_path,
        binary=binary,
        compress=compress,
        start_line=start_line,
        end_line=end_line,
    )


def read_many(
    file_paths: Annotated[list[str], Field(description="Paths relative to the root. At most 50 are processed per call.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
    start_line: Annotated[
        int | None,
        Field(description="First line to return from every file, 1-based."),
    ] = None,
    end_line: Annotated[
        int | None,
        Field(description="Last line to return from every file, inclusive. Defaults to the end."),
    ] = None,
) -> str:
    """Read several text files in one call. A bad path yields an error entry; other files are still read.

    ``start_line``/``end_line`` apply to every file in the batch.
    """
    return _run(
        "read_many",
        format,
        path=path,
        file_paths=file_paths,
        start_line=start_line,
        end_line=end_line,
    )


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



def write_file(
    file_path: Annotated[str, Field(description="Path of the file relative to the project root.")],
    content: Annotated[str, Field(description="Full new contents of the file.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
    overwrite: Annotated[
        bool, Field(description="Replace the file if it already exists. Default true.")
    ] = True,
    encoding: Annotated[
        str | None,
        Field(
            description=(
                "Force an output encoding, e.g. 'utf-8' to convert a cp1252 file. "
                "Omit to keep the existing file's encoding."
            )
        ),
    ] = None,
) -> str:
    """Create or replace a file. Writes are atomic: a crash leaves the original intact."""
    return _run(
        "write_file",
        format,
        path=path,
        file_path=file_path,
        content=content,
        overwrite=overwrite,
        encoding=encoding,
    )


def edit_file(
    file_path: Annotated[str, Field(description="Path of the file relative to the project root.")],
    old_text: Annotated[str, Field(description="Exact text to replace. Must appear in the file.")],
    new_text: Annotated[str, Field(description="Replacement text. May be empty to delete the match.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
    replace_all: Annotated[
        bool, Field(description="Replace every occurrence. Default false, which requires exactly one.")
    ] = False,
) -> str:
    """Replace an exact substring.

    Exact match rather than a regex or line range: unambiguous, and it fails loudly when
    the file has moved on instead of rewriting the wrong place.
    """
    return _run(
        "edit_file",
        format,
        path=path,
        file_path=file_path,
        old_text=old_text,
        new_text=new_text,
        replace_all=replace_all,
    )


def create_directory(
    directory_path: Annotated[str, Field(description="Directory to create, relative to the project root.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Create a directory, including any missing parents."""
    return _run("create_directory", format, path=path, directory_path=directory_path)


def move_file(
    source_path: Annotated[str, Field(description="Existing file to move, relative to the project root.")],
    destination_path: Annotated[str, Field(description="New path, relative to the project root.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
    overwrite: Annotated[
        bool, Field(description="Replace the destination if it exists. Default false.")
    ] = False,
) -> str:
    """Move or rename a file inside the project."""
    return _run(
        "move_file",
        format,
        path=path,
        source_path=source_path,
        destination_path=destination_path,
        overwrite=overwrite,
    )


def delete_file(
    file_path: Annotated[str, Field(description="File to delete, relative to the project root.")],
    path: PathArg = None,
    format: FormatArg = "markdown",
) -> str:
    """Delete one file. Directories are refused."""
    return _run("delete_file", format, path=path, file_path=file_path)


TOOL_FUNCTIONS = {
    "project_map": project_map,
    "project_overview": project_overview,
    "search": search,
    "read": read,
    "read_many": read_many,
    "project_dependencies": project_dependencies,
    "project_diff": project_diff,
    "write_file": write_file,
    "edit_file": edit_file,
    "create_directory": create_directory,
    "move_file": move_file,
    "delete_file": delete_file,
}

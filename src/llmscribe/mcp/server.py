"""MCP server for LLMScribe exposing project structure, search, and file tools for AI agents."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

from llmscribe.core.file_reader import is_text_file
from llmscribe.core.tree_builder import DEFAULT_IGNORE, IgnoreMatcher, load_gitignore
from llmscribe.core.writer import build_project_summary

mcp = MCPServer("llmscribe")


def _resolve_project_root(path: Optional[str] = None) -> Path:
    """Resolve project root directory defaulting to current working directory."""
    if path and path.strip():
        resolved = Path(path).resolve()
    else:
        resolved = Path.cwd().resolve()

    if not resolved.exists():
        raise FileNotFoundError(f"Directory does not exist: '{resolved}'")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Path is not a directory: '{resolved}'")
    return resolved


@mcp.tool()
def project_overview(path: Optional[str] = None) -> str:
    """Return full directory tree and all text file contents for a project."""
    try:
        root = _resolve_project_root(path)
        return build_project_summary(root, tree_only=False)
    except Exception as exc:
        return f"Error building project overview: {exc}"


@mcp.tool()
def project_map(path: Optional[str] = None) -> str:
    """Return directory tree structure without file contents."""
    try:
        root = _resolve_project_root(path)
        return build_project_summary(root, tree_only=True)
    except Exception as exc:
        return f"Error building project map: {exc}"


@mcp.tool()
def project_search(query: str, path: Optional[str] = None) -> str:
    """Search for a keyword query in filenames and file contents."""
    if not query:
        return "Error: Query string cannot be empty."
    try:
        root = _resolve_project_root(path)
        ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
        matcher = IgnoreMatcher(root, ignore_patterns)

        matches: list[str] = []
        query_lower = query.lower()

        for file_path in sorted(root.rglob("*")):
            if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
                continue

            try:
                rel_path = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_path = file_path.as_posix()

            path_matched = query_lower in rel_path.lower()
            content_matches: list[str] = []

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if query_lower in line.lower():
                        content_matches.append(f"  Line {line_idx}: {line.strip()}")
            except OSError:
                pass

            if path_matched or content_matches:
                match_entry = [f"File: {rel_path}"]
                if path_matched and not content_matches:
                    match_entry.append("  (Filename match)")
                if content_matches:
                    match_entry.extend(content_matches[:10])
                    if len(content_matches) > 10:
                        match_entry.append(f"  ... ({len(content_matches) - 10} more line matches)")
                matches.append("\n".join(match_entry))

        if not matches:
            return f"No matches found for query: '{query}'"

        return f"Search results for '{query}' in {root}:\n\n" + "\n\n".join(matches)
    except Exception as exc:
        return f"Error performing search: {exc}"


@mcp.tool()
def project_get_file(file_path: str, path: Optional[str] = None) -> str:
    """Return full content of a specific file, with path traversal prevention."""
    if not file_path or not file_path.strip():
        return "Error: file_path must be provided."
    try:
        root = _resolve_project_root(path)
        target_path = (root / file_path).resolve()

        try:
            target_path.relative_to(root)
        except ValueError:
            return f"Error: Path traversal attempt detected. '{file_path}' is outside root directory."

        if not target_path.exists():
            return f"Error: File does not exist: '{file_path}'"
        if not target_path.is_file():
            return f"Error: Path is not a file: '{file_path}'"
        if not is_text_file(target_path):
            return f"Error: File '{file_path}' is not a recognized text file."

        content = target_path.read_text(encoding="utf-8", errors="ignore")
        return f"--- {file_path} ---\n{content}"
    except Exception as exc:
        return f"Error reading file '{file_path}': {exc}"


@mcp.tool()
def project_list_files(path: Optional[str] = None, extension: Optional[str] = None) -> str:
    """List all supported text files in the project, optionally filtered by extension."""
    try:
        root = _resolve_project_root(path)
        ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
        matcher = IgnoreMatcher(root, ignore_patterns)

        ext_filter: Optional[str] = None
        if extension and extension.strip():
            ext = extension.strip().lower()
            ext_filter = ext if ext.startswith(".") else f".{ext}"

        file_list: list[str] = []
        for file_path in sorted(root.rglob("*")):
            if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
                continue

            if ext_filter and file_path.suffix.lower() != ext_filter:
                continue

            try:
                rel_path = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_path = file_path.as_posix()

            file_list.append(rel_path)

        if not file_list:
            filter_msg = f" matching extension '{extension}'" if extension else ""
            return f"No text files found in {root}{filter_msg}."

        return "\n".join(file_list)
    except Exception as exc:
        return f"Error listing files: {exc}"


def main() -> None:
    """Run the LLMScribe MCP server."""
    mcp.run()

"""MCP server for LLMScribe exposing project structure, search, diff, and file tools for AI agents.

This server provides the following tools:
- project_map: Show project directory structure
- project_overview: Generate full project overview with tree and contents
- search: Search project code for specific patterns
- read: Read a specific file
- read_many: Read multiple files
- project_dependencies: Analyze file dependencies
- project_diff: Show git diff and status
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

from llmscribe.core import (
    analyze_dependencies,
    get_git_diff,
    list_files,
    project_map as core_project_map,
    project_overview as core_project_overview,
    read_file,
    read_files,
    search_project,
)
from llmscribe.github.client import parse_github_repo
from llmscribe.github.provider import (
    github_project_get_file,
    github_project_get_files,
    github_project_map,
    github_project_overview,
    github_project_search,
    github_project_diff,
)

mcp = MCPServer("llmscribe")

MAX_CONTENT_CHARS = 400_000
GET_FILES_MAX_FILES = 50


class ProjectRootError(Exception):
    """Exception raised when project root resolution fails."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _resolve_project_root(path: Optional[str] = None) -> Path:
    """Resolve project root directory defaulting to current working directory."""
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
    """Validate that path and repo are mutually exclusive."""
    if path and path.strip() and repo and repo.strip():
        raise ProjectRootError("path_and_repo_mutually_exclusive", "Cannot specify both 'path' and 'repo'. Use one or the other, not both.")


def _parse_repo(repo_str: str) -> tuple[str, str]:
    """Parse repo string into owner and repo, returning tuple."""
    return parse_github_repo(repo_str)


def _json_ok(tool: str, path: str, data: Any, metadata: Optional[dict[str, Any]] = None) -> str:
    """Generate standard successful JSON envelope."""
    payload: dict[str, Any] = {
        "ok": True,
        "tool": tool,
        "path": path,
        "data": data,
    }
    if metadata is not None:
        payload["metadata"] = metadata
    return json.dumps(payload, indent=2)


def _json_err(tool: str, code: str, message: str) -> str:
    """Generate standard error JSON envelope."""
    return json.dumps({
        "ok": False,
        "tool": tool,
        "error": {
            "code": code,
            "message": message,
        },
    }, indent=2)


def _is_json_format(format: str) -> bool:
    """Return True if format parameter specifies JSON."""
    return format.strip().lower() == "json"


def _md_header(tool: str, path: str) -> str:
    """Generate consistent Markdown header."""
    return f"### llmscribe: {tool}\nPath: {path}\n\n"


def _md_error(tool: str, code: str, message: str) -> str:
    """Generate consistent Markdown error string."""
    return f"### llmscribe: {tool}\nError [{code}]: {message}"


@mcp.tool()
def project_map(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return directory tree structure without file contents.
    
    Supports both local paths and GitHub repositories.
    Use 'path' for local directories, 'repo' for GitHub repositories (owner/repo or URL).
    """
    tool_name = "project_map"
    
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # GitHub repository mode
            owner, repo_name = _parse_repo(repo)
            return github_project_map(owner, repo_name, ref, format)
        
        # Local path mode
        root = _resolve_project_root(path)
        result = core_project_map(root)
        
        if _is_json_format(format):
            return _json_ok(tool_name, root.as_posix(), result.to_dict(), {
                "file_count": result.file_count,
                "character_count": result.character_count,
            })
        
        summary_md = f"Selected Files Directory Structure:\n\n{result.tree}"
        return f"{_md_header(tool_name, root.as_posix())}{summary_md}"

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_overview(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full directory tree and all text file contents for a project.
    
    Supports both local paths and GitHub repositories.
    Use 'path' for local directories, 'repo' for GitHub repositories (owner/repo or URL).
    """
    tool_name = "project_overview"
    
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # GitHub repository mode
            owner, repo_name = _parse_repo(repo)
            return github_project_overview(owner, repo_name, ref, format)
        
        # Local path mode
        root = _resolve_project_root(path)
        result = core_project_overview(root, max_content_chars=MAX_CONTENT_CHARS)
        
        if _is_json_format(format):
            metadata: dict[str, Any] = {
                "file_count": result.file_count,
                "character_count": result.character_count,
            }
            if result.truncated:
                metadata["truncated"] = True
                metadata["truncation_note"] = result.truncation_note
                metadata["truncation_limit"] = result.truncation_limit
            
            return _json_ok(tool_name, root.as_posix(), result.to_dict(), metadata)
        
        files_md = "\n\n".join([f"--- {f['path']} ---\n{f['content']}" for f in result.files])
        summary_md = (
            f"Selected Files Directory Structure:\n\n"
            f"{result.tree}\n\n"
            f"File Contents:\n{files_md}"
        )
        if result.truncated:
            summary_md += f"\n\n[{result.truncation_note}]"
        
        return f"{_md_header(tool_name, root.as_posix())}{summary_md}"

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def search(
    query: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Search for a keyword query in filenames and file contents.
    
    Supports both local paths and GitHub repositories.
    Use 'path' for local directories, 'repo' for GitHub repositories (owner/repo or URL).
    
    This is the main discovery primitive for AI agents. Results include:
    - file path
    - matching line/range  
    - relevant context
    - match type (filename, content)
    - deterministic ordering
    - sensible result limits (max 1000 matches)
    """
    tool_name = "search"
    if not query or not query.strip():
        if _is_json_format(format):
            return _json_err(tool_name, "empty_query", "Query string cannot be empty.")
        return _md_error(tool_name, "empty_query", "Query string cannot be empty.")

    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # GitHub repository mode
            owner, repo_name = _parse_repo(repo)
            return github_project_search(query, owner, repo_name, ref, format)
        
        # Local path mode
        root = _resolve_project_root(path)
        result = search_project(query, root, max_results=1000)
        
        if _is_json_format(format):
            metadata = {
                "query": result.query,
                "root_path": result.root_path,
                "file_count": result.file_count,
                "match_count": result.match_count,
                "truncated": result.truncated,
                "truncation_limit": result.truncation_limit,
            }
            return _json_ok(tool_name, root.as_posix(), result.to_dict(), metadata)
        
        if not result.matches:
            return f"{_md_header(tool_name, root.as_posix())}No matches found for query: '{result.query}'"
        
        # Group matches by file
        matches_by_file: dict[str, list[Any]] = {}
        for match in result.matches:
            if match.file_path not in matches_by_file:
                matches_by_file[match.file_path] = []
            matches_by_file[match.file_path].append(match)
        
        # Build markdown output
        md_parts = []
        for file_path, file_matches in sorted(matches_by_file.items()):
            match_entry = [f"File: {file_path}"]
            
            # Check if we have filename matches
            filename_matches = [m for m in file_matches if m.match_type == "filename"]
            if filename_matches and not any(m.match_type == "content" for m in file_matches):
                match_entry.append("  (Filename match)")
            
            # Add content matches
            content_matches = [m for m in file_matches if m.match_type == "content"]
            for content_match in content_matches[:10]:  # Limit to first 10 content matches per file
                match_entry.append(f"  Line {content_match.line_number}: {content_match.line_content}")
            
            if len(content_matches) > 10:
                match_entry.append(f"  ... ({len(content_matches) - 10} more line matches)")
            
            md_parts.append("\n".join(match_entry))
        
        return f"{_md_header(tool_name, root.as_posix())}Search results for '{result.query}':\n\n" + "\n\n".join(md_parts)

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def read(
    file_path: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full content of a specific file, with path traversal prevention.
    
    Supports both local paths and GitHub repositories.
    Use 'path' for local directories, 'repo' for GitHub repositories (owner/repo or URL).
    """
    tool_name = "read"
    if not file_path or not file_path.strip():
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_path must be provided.")
        return _md_error(tool_name, "invalid_argument", "file_path must be provided.")

    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # GitHub repository mode
            owner, repo_name = _parse_repo(repo)
            return github_project_get_file(file_path, owner, repo_name, ref, format)
        
        # Local path mode
        root = _resolve_project_root(path)
        result = read_file(file_path, root, max_content_chars=MAX_CONTENT_CHARS)
        
        if not result.ok:
            if _is_json_format(format):
                return _json_err(tool_name, result.error_code, result.error_message)
            return _md_error(tool_name, result.error_code, result.error_message)
        
        if _is_json_format(format):
            return _json_ok(tool_name, root.as_posix(), result.to_dict(), {
                "character_count": result.character_count,
            })
        
        return f"{_md_header(tool_name, root.as_posix())}--- {result.file_path} ---\n{result.content}"

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def read_many(
    file_paths: list[str],
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full content of multiple files in one call, handling partial success and path traversal.
    
    Supports both local paths and GitHub repositories.
    Use 'path' for local directories, 'repo' for GitHub repositories (owner/repo or URL).
    """
    tool_name = "read_many"
    if not file_paths:
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_paths list cannot be empty.")
        return _md_error(tool_name, "invalid_argument", "file_paths list cannot be empty.")

    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # GitHub repository mode
            owner, repo_name = _parse_repo(repo)
            return github_project_get_files(file_paths, owner, repo_name, ref, format)
        
        # Local path mode
        root = _resolve_project_root(path)
        result = read_files(file_paths, root, max_files=GET_FILES_MAX_FILES, max_content_chars=MAX_CONTENT_CHARS)
        
        if _is_json_format(format):
            metadata: dict[str, Any] = {
                "file_count": result.file_count,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "character_count": result.character_count,
            }
            if result.truncated:
                metadata["truncated"] = True
                metadata["truncation_note"] = result.truncation_note
            
            return _json_ok(tool_name, root.as_posix(), result.to_dict(), metadata)
        
        # Build markdown output
        md_parts = []
        for file_result in result.results:
            if file_result.ok:
                md_parts.append(f"--- {file_result.file_path} ---\n{file_result.content}")
            else:
                md_parts.append(f"--- {file_result.file_path} ---\nError [{file_result.error_code}]: {file_result.error_message}")
        
        out_md = f"{_md_header(tool_name, root.as_posix())}" + "\n\n".join(md_parts)
        if result.truncated:
            out_md += f"\n\n[{result.truncation_note}]"
        return out_md

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_dependencies(
    file_path: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Analyze dependencies for a specific file.
    
    Supports local paths only for now. GitHub support planned (TODO).
    
    Answers the questions:
    - What files does this file depend on/import?
    - What files depend on/use this file?
    - Which dependencies are local?
    - Which are external or unresolved?
    
    Currently uses a basic AST-based analysis, with CodeGraph support planned
    for the future via a dependency provider abstraction layer.
    """
    tool_name = "project_dependencies"
    if not file_path or not file_path.strip():
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_path must be provided.")
        return _md_error(tool_name, "invalid_argument", "file_path must be provided.")

    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # TODO: Add GitHub support for project_dependencies
            if _is_json_format(format):
                return _json_err(tool_name, "not_implemented", "GitHub repository support for project_dependencies is not yet implemented.")
            return _md_error(tool_name, "not_implemented", "GitHub repository support for project_dependencies is not yet implemented.")
        
        # Local path mode
        root = _resolve_project_root(path)
        result = analyze_dependencies(file_path, root)
        
        if _is_json_format(format):
            return _json_ok(tool_name, root.as_posix(), result.to_dict(), {
                "file_count": len(result.all_local_files),
                "external_dep_count": len(result.all_external_deps),
                "unresolved_count": len(result.all_unresolved),
            })
        
        # Build markdown output
        md_parts = [f"File: {result.target_file}"]
        
        file_deps = result.file_dependencies
        
        if file_deps.imports:
            md_parts.append(f"\nImports: {', '.join(file_deps.imports)}")
        
        if file_deps.local_dependencies:
            md_parts.append(f"\nLocal Dependencies: {', '.join(file_deps.local_dependencies)}")
        
        if file_deps.external_dependencies:
            md_parts.append(f"\nExternal Dependencies: {', '.join(file_deps.external_dependencies)}")
        
        if file_deps.unresolved_dependencies:
            md_parts.append(f"\nUnresolved Dependencies: {', '.join(file_deps.unresolved_dependencies)}")
        
        if result.all_local_files:
            md_parts.append(f"\nFiles that depend on this file: {', '.join(result.all_local_files)}")
        
        return f"{_md_header(tool_name, root.as_posix())}" + "\n".join(md_parts)

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_diff(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    staged: bool = False,
    commit: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return git status and diff for a project, requiring a git repository.
    
    Supports local paths only for now. GitHub support planned (TODO).
    Use 'path' for local directories, 'repo' for GitHub repositories (owner/repo or URL).
    """
    tool_name = "project_diff"
    
    try:
        _validate_path_repo_mutual_exclusive(path, repo)
        
        if repo and repo.strip():
            # TODO: Add GitHub support for project_diff
            # For now, use the existing GitHub provider function
            owner, repo_name = _parse_repo(repo)
            return github_project_diff(commit, staged, owner, repo_name, ref, format)
        
        # Local path mode
        root = _resolve_project_root(path)
        result = get_git_diff(root, staged=staged, commit=commit, max_diff_chars=200_000)
        
        if _is_json_format(format):
            return _json_ok(
                tool_name,
                root.as_posix(),
                {
                    "staged": result.staged,
                    "commit": result.commit,
                    "changed_files": result.changed_files,
                    "status_lines": result.status_lines,
                    "diff": result.diff,
                    "truncated": result.truncated,
                },
                {
                    "changed_file_count": len(result.changed_files),
                    "character_count": result.character_count,
                    "truncated": result.truncated,
                },
            )
        
        md_output = [f"{_md_header(tool_name, root.as_posix())}### Git Status & Diff"]
        if result.changed_files:
            md_output.append("Changed Files:\n" + "\n".join(f"- {f}" for f in result.changed_files))
        else:
            md_output.append("No changed files.")

        if result.diff.strip():
            md_output.append(f"\nDiff:\n```diff\n{result.diff}\n```")
        else:
            md_output.append("\nDiff is empty.")

        return "\n\n".join(md_output)

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except RuntimeError as exc:
        # Handle git-specific errors
        if "git" in str(exc).lower() or "not a git repository" in str(exc):
            if _is_json_format(format):
                return _json_err(tool_name, "git_unavailable", str(exc))
            return _md_error(tool_name, "git_unavailable", str(exc))
        else:
            if _is_json_format(format):
                return _json_err(tool_name, "internal_error", str(exc))
            return _md_error(tool_name, "internal_error", str(exc))
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def main() -> None:
    """Run the LLMScribe MCP server.
    
    Supports both stdio and HTTP transport via environment variables.
    Default: stdio (for local llmscribe-mcp compatibility)
    Set MCP_TRANSPORT=http to use HTTP transport.
    """
    # Check for transport preference
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    
    if transport == "http":
        # Use HTTP transport
        mcp.run(transport="http")
    else:
        # Default to stdio transport
        mcp.run()
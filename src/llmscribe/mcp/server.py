"""MCP server for LLMScribe exposing project structure, search, diff, and file tools for AI agents."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

from llmscribe.core.file_reader import is_text_file
from llmscribe.core.tree_builder import DEFAULT_IGNORE, IgnoreMatcher, generate_tree, load_gitignore
from llmscribe.github import (
    GitHubError,
    github_project_diff,
    github_project_get_file,
    github_project_get_files,
    github_project_list_files,
    github_project_map,
    github_project_overview,
    github_project_search,
    parse_github_repo,
)

mcp = MCPServer("llmscribe")

DIFF_MAX_CHARS = 200_000
GET_FILES_MAX_FILES = 50
MAX_CONTENT_CHARS = 400_000


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


def _md_header(tool: str, path: Path) -> str:
    """Generate consistent Markdown header."""
    return f"### llmscribe: {tool}\nPath: {path.as_posix()}\n\n"


def _md_error(tool: str, code: str, message: str) -> str:
    """Generate consistent Markdown error string."""
    return f"### llmscribe: {tool}\nError [{code}]: {message}"


def _json_ok(tool: str, path: Path, data: Any, metadata: Optional[dict[str, Any]] = None) -> str:
    """Generate standard successful JSON envelope."""
    payload: dict[str, Any] = {
        "ok": True,
        "tool": tool,
        "path": path.as_posix(),
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


def _parse_porcelain_path(line: str) -> str:
    """Extract clean relative file path from git status --porcelain line."""
    path_part = line[3:].strip() if len(line) > 3 else line.strip()
    if " -> " in path_part:
        path_part = path_part.split(" -> ")[-1].strip()
    return path_part.strip('"')


def _validate_routing(path: Optional[str], repo: Optional[str]) -> Optional[tuple[str, str]]:
    """Validate path vs repo parameters.

    Returns:
        None if local routing, or (owner, repo_name) if github routing.
    Raises:
        ProjectRootError if both path and repo are specified.
    """
    has_path = bool(path and path.strip())
    has_repo = bool(repo and repo.strip())

    if has_path and has_repo:
        raise ProjectRootError("invalid_argument", "Cannot specify both 'path' and 'repo'.")

    if has_repo:
        try:
            return parse_github_repo(repo)  # type: ignore
        except GitHubError as exc:
            raise ProjectRootError(exc.code, exc.message)

    return None


@mcp.tool()
def project_overview(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full directory tree and all text file contents for a project."""
    tool_name = "project_overview"
    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_overview(gh_target[0], gh_target[1], ref, format)

        root = _resolve_project_root(path)
        ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
        matcher = IgnoreMatcher(root, ignore_patterns)

        tree_str = generate_tree(root, ignore_patterns)

        files_json: list[dict[str, str]] = []
        md_contents: list[str] = []
        total_chars = 0
        truncated = False
        truncation_note = ""

        for file_path in sorted(root.rglob("*")):
            if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
                continue

            try:
                rel_path = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_path = file_path.as_posix()

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                content = f"[Error reading file: {exc}]"

            content_len = len(content)

            if total_chars + content_len > MAX_CONTENT_CHARS:
                remaining_budget = max(0, MAX_CONTENT_CHARS - total_chars)
                truncated_content = content[:remaining_budget] + "\n[Content truncated]"
                files_json.append({"path": rel_path, "content": truncated_content})
                md_contents.append(f"\n--- {rel_path} ---\n{truncated_content}")
                total_chars += len(truncated_content)
                truncated = True
                truncation_note = f"Content output capped at {MAX_CONTENT_CHARS:,} characters."
                break

            files_json.append({"path": rel_path, "content": content})
            md_contents.append(f"\n--- {rel_path} ---\n{content}")
            total_chars += content_len

        metadata: dict[str, Any] = {
            "file_count": len(files_json),
            "character_count": total_chars + len(tree_str),
        }
        if truncated:
            metadata["truncated"] = True
            metadata["truncation_note"] = truncation_note

        if _is_json_format(format):
            return _json_ok(tool_name, root, {"tree": tree_str, "files": files_json}, metadata)

        summary_md = (
            f"Selected Files Directory Structure:\n\n"
            f"{tree_str}\n\n"
            f"File Contents:\n{''.join(md_contents)}"
        )
        if truncated:
            summary_md += f"\n\n[{truncation_note}]"

        return f"{_md_header(tool_name, root)}{summary_md}"

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_map(
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return directory tree structure without file contents."""
    tool_name = "project_map"
    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_map(gh_target[0], gh_target[1], ref, format)

        root = _resolve_project_root(path)
        ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
        matcher = IgnoreMatcher(root, ignore_patterns)

        tree_str = generate_tree(root, ignore_patterns)

        files_json: list[dict[str, str]] = []
        for file_path in sorted(root.rglob("*")):
            if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
                continue
            try:
                rel_path = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_path = file_path.as_posix()
            files_json.append({"path": rel_path})

        metadata = {"file_count": len(files_json)}

        if _is_json_format(format):
            return _json_ok(tool_name, root, {"tree": tree_str, "files": files_json}, metadata)

        summary_md = f"Selected Files Directory Structure:\n\n{tree_str}"
        return f"{_md_header(tool_name, root)}{summary_md}"

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_search(
    query: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Search for a keyword query in filenames and file contents."""
    tool_name = "project_search"
    if not query:
        if _is_json_format(format):
            return _json_err(tool_name, "empty_query", "Query string cannot be empty.")
        return _md_error(tool_name, "empty_query", "Query string cannot be empty.")

    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_search(query, gh_target[0], gh_target[1], ref, format)

        root = _resolve_project_root(path)
        ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
        matcher = IgnoreMatcher(root, ignore_patterns)

        json_matches: list[dict[str, Any]] = []
        md_matches: list[str] = []
        query_lower = query.lower()

        for file_path in sorted(root.rglob("*")):
            if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
                continue

            try:
                rel_path = file_path.relative_to(root).as_posix()
            except ValueError:
                rel_path = file_path.as_posix()

            path_matched = query_lower in rel_path.lower()
            content_matches: list[dict[str, Any]] = []
            md_content_lines: list[str] = []

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    if query_lower in line.lower():
                        content_matches.append({"line": line_idx, "content": line.strip()})
                        md_content_lines.append(f"  Line {line_idx}: {line.strip()}")
            except OSError:
                pass

            if path_matched or content_matches:
                json_matches.append({
                    "file": rel_path,
                    "path_match": path_matched,
                    "line_matches": content_matches,
                })

                match_entry = [f"File: {rel_path}"]
                if path_matched and not content_matches:
                    match_entry.append("  (Filename match)")
                if md_content_lines:
                    match_entry.extend(md_content_lines[:10])
                    if len(md_content_lines) > 10:
                        match_entry.append(f"  ... ({len(md_content_lines) - 10} more line matches)")
                md_matches.append("\n".join(match_entry))

        metadata = {"match_count": len(json_matches)}

        if _is_json_format(format):
            return _json_ok(tool_name, root, {"query": query, "matches": json_matches}, metadata)

        if not md_matches:
            return f"{_md_header(tool_name, root)}No matches found for query: '{query}'"

        return f"{_md_header(tool_name, root)}Search results for '{query}':\n\n" + "\n\n".join(md_matches)

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_get_file(
    file_path: str,
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full content of a specific file, with path traversal prevention."""
    tool_name = "project_get_file"
    if not file_path or not file_path.strip():
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_path must be provided.")
        return _md_error(tool_name, "invalid_argument", "file_path must be provided.")

    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_get_file(file_path, gh_target[0], gh_target[1], ref, format)

        root = _resolve_project_root(path)
        target_path = (root / file_path).resolve()

        try:
            target_path.relative_to(root)
        except ValueError:
            msg = f"Path traversal attempt detected. '{file_path}' is outside root directory."
            if _is_json_format(format):
                return _json_err(tool_name, "path_traversal", msg)
            return _md_error(tool_name, "path_traversal", msg)

        if not target_path.exists():
            msg = f"File does not exist: '{file_path}'"
            if _is_json_format(format):
                return _json_err(tool_name, "file_not_found", msg)
            return _md_error(tool_name, "file_not_found", msg)

        if not target_path.is_file():
            msg = f"Path is not a file: '{file_path}'"
            if _is_json_format(format):
                return _json_err(tool_name, "not_a_file", msg)
            return _md_error(tool_name, "not_a_file", msg)

        if not is_text_file(target_path):
            msg = f"File '{file_path}' is not a recognized text file."
            if _is_json_format(format):
                return _json_err(tool_name, "not_text_file", msg)
            return _md_error(tool_name, "not_text_file", msg)

        content = target_path.read_text(encoding="utf-8", errors="ignore")
        rel_posix = target_path.relative_to(root).as_posix()

        metadata = {"character_count": len(content)}

        if _is_json_format(format):
            return _json_ok(tool_name, root, {"file_path": rel_posix, "content": content}, metadata)

        return f"{_md_header(tool_name, root)}--- {rel_posix} ---\n{content}"

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except OSError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "read_error", str(exc))
        return _md_error(tool_name, "read_error", str(exc))
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


@mcp.tool()
def project_get_files(
    file_paths: list[str],
    path: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return full content of multiple files in one call, handling partial success and path traversal."""
    tool_name = "project_get_files"
    if not file_paths:
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_paths list cannot be empty.")
        return _md_error(tool_name, "invalid_argument", "file_paths list cannot be empty.")

    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_get_files(file_paths, gh_target[0], gh_target[1], ref, format)

        root = _resolve_project_root(path)

        truncated_batch = False
        if len(file_paths) > GET_FILES_MAX_FILES:
            target_paths_list = file_paths[:GET_FILES_MAX_FILES]
            truncated_batch = True
        else:
            target_paths_list = file_paths

        results: list[dict[str, Any]] = []
        md_chunks: list[str] = []
        success_count = 0
        error_count = 0
        total_chars = 0
        truncated_chars = False

        for fp in target_paths_list:
            if not fp or not fp.strip():
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "invalid_argument", "message": "Empty file path provided."},
                })
                md_chunks.append("--- [empty path] ---\nError [invalid_argument]: Empty file path provided.")
                continue

            target_path = (root / fp).resolve()
            try:
                target_path.relative_to(root)
            except ValueError:
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "path_traversal", "message": f"Path traversal attempt: '{fp}' is outside root."},
                })
                md_chunks.append(f"--- {fp} ---\nError [path_traversal]: Path traversal attempt: '{fp}' is outside root.")
                continue

            if not target_path.exists():
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "file_not_found", "message": f"File does not exist: '{fp}'"},
                })
                md_chunks.append(f"--- {fp} ---\nError [file_not_found]: File does not exist: '{fp}'")
                continue

            if not target_path.is_file():
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "not_a_file", "message": f"Path is not a file: '{fp}'"},
                })
                md_chunks.append(f"--- {fp} ---\nError [not_a_file]: Path is not a file: '{fp}'")
                continue

            if not is_text_file(target_path):
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "not_text_file", "message": f"File '{fp}' is not a recognized text file."},
                })
                md_chunks.append(f"--- {fp} ---\nError [not_text_file]: File '{fp}' is not a recognized text file.")
                continue

            try:
                content = target_path.read_text(encoding="utf-8", errors="ignore")
                rel_posix = target_path.relative_to(root).as_posix()
                content_len = len(content)

                if total_chars + content_len > MAX_CONTENT_CHARS:
                    remaining = max(0, MAX_CONTENT_CHARS - total_chars)
                    truncated_content = content[:remaining] + "\n[Content truncated]"
                    total_chars += len(truncated_content)
                    success_count += 1
                    truncated_chars = True
                    results.append({
                        "file_path": rel_posix,
                        "ok": True,
                        "content": truncated_content,
                    })
                    md_chunks.append(f"--- {rel_posix} ---\n{truncated_content}")
                    break

                total_chars += content_len
                success_count += 1
                results.append({
                    "file_path": rel_posix,
                    "ok": True,
                    "content": content,
                })
                md_chunks.append(f"--- {rel_posix} ---\n{content}")
            except OSError as exc:
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "read_error", "message": str(exc)},
                })
                md_chunks.append(f"--- {fp} ---\nError [read_error]: {exc}")

        metadata: dict[str, Any] = {
            "file_count": len(file_paths),
            "success_count": success_count,
            "error_count": error_count,
            "character_count": total_chars,
        }

        if truncated_batch or truncated_chars:
            metadata["truncated"] = True
            notes = []
            if truncated_batch:
                notes.append(f"Processed first {GET_FILES_MAX_FILES} files out of {len(file_paths)} requested.")
            if truncated_chars:
                notes.append(f"Total file content capped at {MAX_CONTENT_CHARS:,} characters.")
            metadata["truncation_note"] = " ".join(notes)

        if _is_json_format(format):
            return _json_ok(tool_name, root, {"results": results}, metadata)

        out_md = f"{_md_header(tool_name, root)}" + "\n\n".join(md_chunks)
        if truncated_batch or truncated_chars:
            out_md += f"\n\n[{metadata['truncation_note']}]"
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
def project_list_files(
    path: Optional[str] = None,
    extension: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """List all supported text files in the project, optionally filtered by extension."""
    tool_name = "project_list_files"
    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_list_files(extension, gh_target[0], gh_target[1], ref, format)

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

        metadata = {"file_count": len(file_list)}

        if _is_json_format(format):
            return _json_ok(tool_name, root, {"files": file_list, "extension_filter": extension}, metadata)

        if not file_list:
            filter_msg = f" matching extension '{extension}'" if extension else ""
            return f"{_md_header(tool_name, root)}No text files found in {root}{filter_msg}."

        return f"{_md_header(tool_name, root)}" + "\n".join(file_list)

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
    staged: bool = False,
    commit: Optional[str] = None,
    repo: Optional[str] = None,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    """Return git status and diff for a project, requiring a git repository."""
    tool_name = "project_diff"
    try:
        gh_target = _validate_routing(path, repo)
        if gh_target:
            return github_project_diff(commit, staged, gh_target[0], gh_target[1], ref, format)

        root = _resolve_project_root(path)

        # Check if git is available and root is inside a git work tree
        try:
            check_git = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if check_git.returncode != 0:
                msg = f"Directory '{root}' is not a git repository."
                if _is_json_format(format):
                    return _json_err(tool_name, "git_unavailable", msg)
                return _md_error(tool_name, "git_unavailable", msg)
        except (OSError, subprocess.SubprocessError) as exc:
            msg = f"Git executable is unavailable or failed: {exc}"
            if _is_json_format(format):
                return _json_err(tool_name, "git_unavailable", msg)
            return _md_error(tool_name, "git_unavailable", msg)

        # Validate commit parameter if provided
        if commit is not None and commit.strip():
            commit_clean = commit.strip()
            if not re.match(r"^[a-zA-Z0-9_\-./~^@]+$", commit_clean):
                msg = f"Invalid commit ref format: '{commit}'"
                if _is_json_format(format):
                    return _json_err(tool_name, "invalid_ref", msg)
                return _md_error(tool_name, "invalid_ref", msg)
            diff_cmd = ["git", "diff", commit_clean]
        elif staged:
            diff_cmd = ["git", "diff", "--cached"]
        else:
            diff_cmd = ["git", "diff", "HEAD"]

        diff_proc = subprocess.run(
            diff_cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        raw_diff = diff_proc.stdout or ""
        raw_status = status_proc.stdout or ""

        changed_files: list[str] = []
        status_lines: list[str] = []
        for line in raw_status.splitlines():
            if line.strip():
                status_lines.append(line)
                clean_p = _parse_porcelain_path(line)
                if clean_p and clean_p not in changed_files:
                    changed_files.append(clean_p)

        truncated = False
        diff_text = raw_diff
        if len(diff_text) > DIFF_MAX_CHARS:
            diff_text = diff_text[:DIFF_MAX_CHARS] + f"\n\n[Diff truncated after {DIFF_MAX_CHARS:,} characters]"
            truncated = True

        metadata = {
            "changed_file_count": len(changed_files),
            "character_count": len(diff_text),
            "truncated": truncated,
        }

        if _is_json_format(format):
            return _json_ok(
                tool_name,
                root,
                {
                    "staged": staged,
                    "commit": commit,
                    "changed_files": changed_files,
                    "status_lines": status_lines,
                    "diff": diff_text,
                    "truncated": truncated,
                },
                metadata,
            )

        md_output = [f"{_md_header(tool_name, root)}### Git Status & Diff"]
        if changed_files:
            md_output.append("Changed Files:\n" + "\n".join(f"- {f}" for f in changed_files))
        else:
            md_output.append("No changed files.")

        if diff_text.strip():
            md_output.append(f"\nDiff:\n```diff\n{diff_text}\n```")
        else:
            md_output.append("\nDiff is empty.")

        return "\n\n".join(md_output)

    except ProjectRootError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def main() -> None:
    """Run the LLMScribe MCP server."""
    mcp.run()

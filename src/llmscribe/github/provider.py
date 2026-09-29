"""GitHub provider handlers for LLMScribe MCP tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from llmscribe.core.file_reader import is_text_file
from llmscribe.core.tree_builder import DEFAULT_IGNORE, IgnoreMatcher
from llmscribe.github.client import (
    GitHubError,
    GitHubSnapshot,
    fetch_github_diff,
    fetch_github_snapshot,
)

DIFF_MAX_CHARS = 200_000
GET_FILES_MAX_FILES = 50
MAX_CONTENT_CHARS = 400_000


def _is_json_format(format: str) -> bool:
    return format.strip().lower() == "json"


def _md_header(tool: str, logical_path: str) -> str:
    return f"### llmscribe: {tool}\nPath: {logical_path}\n\n"


def _md_error(tool: str, code: str, message: str) -> str:
    return f"### llmscribe: {tool}\nError [{code}]: {message}"


def _json_ok(tool: str, logical_path: str, data: Any, metadata: Optional[dict[str, Any]] = None) -> str:
    payload: dict[str, Any] = {
        "ok": True,
        "tool": tool,
        "path": logical_path,
        "data": data,
    }
    if metadata is not None:
        payload["metadata"] = metadata
    return json.dumps(payload, indent=2)


def _json_err(tool: str, code: str, message: str) -> str:
    return json.dumps({
        "ok": False,
        "tool": tool,
        "error": {
            "code": code,
            "message": message,
        },
    }, indent=2)


def generate_github_tree(snapshot: GitHubSnapshot, matcher: IgnoreMatcher) -> str:
    """Build visual directory tree from in-memory snapshot file paths."""
    # Build tree structure
    dir_tree: dict[str, Any] = {}
    for rel_path in sorted(snapshot.files.keys()):
        parts = rel_path.split("/")
        curr = dir_tree
        # Check if any parent or file is ignored
        sub_path = ""
        ignored = False
        for i, part in enumerate(parts):
            sub_path = f"{sub_path}/{part}" if sub_path else part
            if matcher.is_ignored(Path(sub_path)):
                ignored = True
                break
        if ignored:
            continue

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                curr[part] = None  # file
            else:
                if part not in curr or not isinstance(curr[part], dict):
                    curr[part] = {}
                curr = curr[part]

    lines = [f"{snapshot.repo}/"]

    def walk(node: dict[str, Any], prefix: str = "") -> None:
        items = sorted(node.keys(), key=lambda k: (node[k] is None, k.lower()))
        for idx, key in enumerate(items):
            connector = "└── " if idx == len(items) - 1 else "├── "
            lines.append(prefix + connector + key)
            if isinstance(node[key], dict):
                ext = "    " if idx == len(items) - 1 else "│   "
                walk(node[key], prefix + ext)

    walk(dir_tree)
    return "\n".join(lines)


def github_project_overview(
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_overview"
    try:
        snapshot = fetch_github_snapshot(owner, repo, ref)
        ignore_patterns = [*DEFAULT_IGNORE, *snapshot.load_gitignore()]
        matcher = IgnoreMatcher(Path("/"), ignore_patterns)

        tree_str = generate_github_tree(snapshot, matcher)

        files_json: list[dict[str, str]] = []
        md_contents: list[str] = []
        total_chars = 0
        truncated = False
        truncation_note = ""

        for rel_path in sorted(snapshot.files.keys()):
            p = Path(rel_path)
            if matcher.is_ignored(p) or not is_text_file(p):
                continue

            content = snapshot.get_text_content(rel_path)
            content_len = len(content)

            if total_chars + content_len > MAX_CONTENT_CHARS:
                remaining = max(0, MAX_CONTENT_CHARS - total_chars)
                truncated_content = content[:remaining] + "\n[Content truncated]"
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
            return _json_ok(tool_name, snapshot.logical_path, {"tree": tree_str, "files": files_json}, metadata)

        summary_md = (
            f"Selected Files Directory Structure:\n\n"
            f"{tree_str}\n\n"
            f"File Contents:\n{''.join(md_contents)}"
        )
        if truncated:
            summary_md += f"\n\n[{truncation_note}]"

        return f"{_md_header(tool_name, snapshot.logical_path)}{summary_md}"

    except GitHubError as exc:
        logical_path = f"github.com/{owner}/{repo}"
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def github_project_map(
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_map"
    try:
        snapshot = fetch_github_snapshot(owner, repo, ref)
        ignore_patterns = [*DEFAULT_IGNORE, *snapshot.load_gitignore()]
        matcher = IgnoreMatcher(Path("/"), ignore_patterns)

        tree_str = generate_github_tree(snapshot, matcher)

        files_json: list[dict[str, str]] = []
        for rel_path in sorted(snapshot.files.keys()):
            p = Path(rel_path)
            if matcher.is_ignored(p) or not is_text_file(p):
                continue
            files_json.append({"path": rel_path})

        metadata = {"file_count": len(files_json)}

        if _is_json_format(format):
            return _json_ok(tool_name, snapshot.logical_path, {"tree": tree_str, "files": files_json}, metadata)

        summary_md = f"Selected Files Directory Structure:\n\n{tree_str}"
        return f"{_md_header(tool_name, snapshot.logical_path)}{summary_md}"

    except GitHubError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def github_project_search(
    query: str,
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_search"
    if not query:
        if _is_json_format(format):
            return _json_err(tool_name, "empty_query", "Query string cannot be empty.")
        return _md_error(tool_name, "empty_query", "Query string cannot be empty.")

    try:
        snapshot = fetch_github_snapshot(owner, repo, ref)
        ignore_patterns = [*DEFAULT_IGNORE, *snapshot.load_gitignore()]
        matcher = IgnoreMatcher(Path("/"), ignore_patterns)

        json_matches: list[dict[str, Any]] = []
        md_matches: list[str] = []
        query_lower = query.lower()

        for rel_path in sorted(snapshot.files.keys()):
            p = Path(rel_path)
            if matcher.is_ignored(p) or not is_text_file(p):
                continue

            path_matched = query_lower in rel_path.lower()
            content_matches: list[dict[str, Any]] = []
            md_content_lines: list[str] = []

            content = snapshot.get_text_content(rel_path)
            for line_idx, line in enumerate(content.splitlines(), start=1):
                if query_lower in line.lower():
                    content_matches.append({"line": line_idx, "content": line.strip()})
                    md_content_lines.append(f"  Line {line_idx}: {line.strip()}")

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
            return _json_ok(tool_name, snapshot.logical_path, {"query": query, "matches": json_matches}, metadata)

        if not md_matches:
            return f"{_md_header(tool_name, snapshot.logical_path)}No matches found for query: '{query}'"

        return f"{_md_header(tool_name, snapshot.logical_path)}Search results for '{query}':\n\n" + "\n\n".join(md_matches)

    except GitHubError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def github_project_get_file(
    file_path: str,
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_get_file"
    if not file_path or not file_path.strip():
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_path must be provided.")
        return _md_error(tool_name, "invalid_argument", "file_path must be provided.")

    try:
        snapshot = fetch_github_snapshot(owner, repo, ref)
        clean_fp = file_path.strip().lstrip("/")

        # Path traversal check
        if ".." in clean_fp.split("/"):
            msg = f"Path traversal attempt detected. '{file_path}' is outside root directory."
            if _is_json_format(format):
                return _json_err(tool_name, "path_traversal", msg)
            return _md_error(tool_name, "path_traversal", msg)

        if clean_fp not in snapshot.files:
            msg = f"File does not exist: '{file_path}'"
            if _is_json_format(format):
                return _json_err(tool_name, "file_not_found", msg)
            return _md_error(tool_name, "file_not_found", msg)

        if not is_text_file(Path(clean_fp)):
            msg = f"File '{file_path}' is not a recognized text file."
            if _is_json_format(format):
                return _json_err(tool_name, "not_text_file", msg)
            return _md_error(tool_name, "not_text_file", msg)

        content = snapshot.get_text_content(clean_fp)
        metadata = {"character_count": len(content)}

        if _is_json_format(format):
            return _json_ok(tool_name, snapshot.logical_path, {"file_path": clean_fp, "content": content}, metadata)

        return f"{_md_header(tool_name, snapshot.logical_path)}--- {clean_fp} ---\n{content}"

    except GitHubError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def github_project_get_files(
    file_paths: list[str],
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_get_files"
    if not file_paths:
        if _is_json_format(format):
            return _json_err(tool_name, "invalid_argument", "file_paths list cannot be empty.")
        return _md_error(tool_name, "invalid_argument", "file_paths list cannot be empty.")

    try:
        snapshot = fetch_github_snapshot(owner, repo, ref)

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

            clean_fp = fp.strip().lstrip("/")
            if ".." in clean_fp.split("/"):
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "path_traversal", "message": f"Path traversal attempt: '{fp}' is outside root."},
                })
                md_chunks.append(f"--- {fp} ---\nError [path_traversal]: Path traversal attempt: '{fp}' is outside root.")
                continue

            if clean_fp not in snapshot.files:
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "file_not_found", "message": f"File does not exist: '{fp}'"},
                })
                md_chunks.append(f"--- {fp} ---\nError [file_not_found]: File does not exist: '{fp}'")
                continue

            if not is_text_file(Path(clean_fp)):
                error_count += 1
                results.append({
                    "file_path": fp,
                    "ok": False,
                    "error": {"code": "not_text_file", "message": f"File '{fp}' is not a recognized text file."},
                })
                md_chunks.append(f"--- {fp} ---\nError [not_text_file]: File '{fp}' is not a recognized text file.")
                continue

            content = snapshot.get_text_content(clean_fp)
            content_len = len(content)

            if total_chars + content_len > MAX_CONTENT_CHARS:
                remaining = max(0, MAX_CONTENT_CHARS - total_chars)
                truncated_content = content[:remaining] + "\n[Content truncated]"
                total_chars += len(truncated_content)
                success_count += 1
                truncated_chars = True
                results.append({
                    "file_path": clean_fp,
                    "ok": True,
                    "content": truncated_content,
                })
                md_chunks.append(f"--- {clean_fp} ---\n{truncated_content}")
                break

            total_chars += content_len
            success_count += 1
            results.append({
                "file_path": clean_fp,
                "ok": True,
                "content": content,
            })
            md_chunks.append(f"--- {clean_fp} ---\n{content}")

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
            return _json_ok(tool_name, snapshot.logical_path, {"results": results}, metadata)

        out_md = f"{_md_header(tool_name, snapshot.logical_path)}" + "\n\n".join(md_chunks)
        if truncated_batch or truncated_chars:
            out_md += f"\n\n[{metadata['truncation_note']}]"
        return out_md

    except GitHubError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def github_project_list_files(
    extension: Optional[str],
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_list_files"
    try:
        snapshot = fetch_github_snapshot(owner, repo, ref)
        ignore_patterns = [*DEFAULT_IGNORE, *snapshot.load_gitignore()]
        matcher = IgnoreMatcher(Path("/"), ignore_patterns)

        ext_filter: Optional[str] = None
        if extension and extension.strip():
            ext = extension.strip().lower()
            ext_filter = ext if ext.startswith(".") else f".{ext}"

        file_list: list[str] = []
        for rel_path in sorted(snapshot.files.keys()):
            p = Path(rel_path)
            if matcher.is_ignored(p) or not is_text_file(p):
                continue
            if ext_filter and p.suffix.lower() != ext_filter:
                continue
            file_list.append(rel_path)

        metadata = {"file_count": len(file_list)}

        if _is_json_format(format):
            return _json_ok(tool_name, snapshot.logical_path, {"files": file_list, "extension_filter": extension}, metadata)

        if not file_list:
            filter_msg = f" matching extension '{extension}'" if extension else ""
            return f"{_md_header(tool_name, snapshot.logical_path)}No text files found in {snapshot.logical_path}{filter_msg}."

        return f"{_md_header(tool_name, snapshot.logical_path)}" + "\n".join(file_list)

    except GitHubError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))


def github_project_diff(
    commit: Optional[str],
    staged: bool,
    owner: str,
    repo: str,
    ref: Optional[str] = None,
    format: str = "markdown",
) -> str:
    tool_name = "project_diff"
    logical_path = f"github.com/{owner}/{repo}@{ref}" if ref else f"github.com/{owner}/{repo}"
    try:
        base_ref = commit.strip() if commit and commit.strip() else None
        head_ref = ref.strip() if ref and ref.strip() else "HEAD"

        if not base_ref:
            # If no base commit ref is supplied for GitHub diff
            msg = "GitHub diff requires a commit ref or base branch (e.g. commit='main')."
            if _is_json_format(format):
                return _json_err(tool_name, "invalid_ref", msg)
            return _md_error(tool_name, "invalid_ref", msg)

        diff_data = fetch_github_diff(owner, repo, base=base_ref, head=head_ref)

        changed_files: list[str] = []
        diff_patches: list[str] = []
        for file_info in diff_data.get("files", []):
            fname = file_info.get("filename", "")
            if fname:
                changed_files.append(fname)
                patch = file_info.get("patch", "")
                if patch:
                    diff_patches.append(f"--- a/{fname}\n+++ b/{fname}\n{patch}")

        raw_diff = "\n\n".join(diff_patches)
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
                logical_path,
                {
                    "staged": staged,
                    "commit": commit,
                    "changed_files": changed_files,
                    "status_lines": [f"M {f}" for f in changed_files],
                    "diff": diff_text,
                    "truncated": truncated,
                },
                metadata,
            )

        md_output = [f"{_md_header(tool_name, logical_path)}### GitHub Diff ({base_ref}...{head_ref})"]
        if changed_files:
            md_output.append("Changed Files:\n" + "\n".join(f"- {f}" for f in changed_files))
        else:
            md_output.append("No changed files.")

        if diff_text.strip():
            md_output.append(f"\nDiff:\n```diff\n{diff_text}\n```")
        else:
            md_output.append("\nDiff is empty.")

        return "\n\n".join(md_output)

    except GitHubError as exc:
        if _is_json_format(format):
            return _json_err(tool_name, exc.code, exc.message)
        return _md_error(tool_name, exc.code, exc.message)
    except Exception as exc:
        if _is_json_format(format):
            return _json_err(tool_name, "internal_error", str(exc))
        return _md_error(tool_name, "internal_error", str(exc))

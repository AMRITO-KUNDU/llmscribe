"""One implementation of every LLMScribe tool, shared by the MCP server and the CLI.

``execute`` resolves a source (local directory or GitHub repository), runs the
operation and returns a ``ToolResponse``. ``render_json`` / ``render_markdown`` /
``render_error`` produce the public output, so local and GitHub results always
have the same schema and the same error contract.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from llmscribe.core import (
    LLMScribeError,
    LocalRepository,
    RepositorySource,
    analyze_source_dependencies,
    get_git_diff,
    map_source,
    overview_source,
    read_from_source,
    read_many_from_source,
    search_source,
)
from llmscribe.core.diff import DiffResult, GitStatusEntry
from llmscribe.core.errors import redact
from llmscribe.core.limits import MAX_DIFF_CHARS, MAX_SEARCH_RESULTS
from llmscribe.github.client import fetch_github_diff, fetch_github_snapshot, parse_github_repo, validate_github_ref

logger = logging.getLogger("llmscribe")

TOOLS = (
    "project_map",
    "project_overview",
    "search",
    "read",
    "read_many",
    "project_dependencies",
    "project_diff",
)

_SEARCH_LINES_PER_FILE = 10
_GITHUB_COMPARE_FILE_LIMIT = 300
_GITHUB_STATUS = {"added": "A", "removed": "D", "modified": "M", "renamed": "R", "copied": "C", "changed": "M"}


@dataclass
class ToolResponse:
    """A successful tool result in source-independent form."""

    tool: str
    path: str
    source: str  # "local" or "github"
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""  # markdown body


# --------------------------------------------------------------------------- sources

def open_source(
    path: str | None = None,
    repo: str | None = None,
    ref: str | None = None,
    allowed_roots: Sequence[Path] | None = None,
) -> RepositorySource:
    """Resolve ``path`` (local) or ``repo`` (GitHub) to a ``RepositorySource``.

    ``allowed_roots`` restricts local access (``None`` = unrestricted, empty =
    local access disabled), which hosted deployments use to avoid exposing the server's disk.
    """
    has_path = bool(path and path.strip())
    has_repo = bool(repo and repo.strip())
    if has_path and has_repo:
        raise LLMScribeError("invalid_argument", "Cannot specify both 'path' and 'repo'.")
    if ref and ref.strip() and not has_repo:
        raise LLMScribeError("invalid_argument", "'ref' can only be used together with 'repo'.")
    if has_repo:
        owner, name = parse_github_repo(repo or "")
        return fetch_github_snapshot(owner, name, ref)
    return _open_local(path if has_path else None, allowed_roots)


def _open_local(path: str | None, allowed_roots: Sequence[Path] | None) -> LocalRepository:
    if allowed_roots is not None:
        if not allowed_roots:
            raise LLMScribeError(
                "unsupported_operation",
                "Local paths are disabled on this server. Use the 'repo' argument for GitHub repositories.",
            )
        source = LocalRepository(path)
        if not any(source.root == r or r in source.root.parents for r in allowed_roots):
            raise LLMScribeError("invalid_path", "That path is outside the directories this server may read.")
        return source
    return LocalRepository(path)


# --------------------------------------------------------------------------- diff

def _github_diff(repo: str, ref: str | None, staged: bool, commit: str | None, max_chars: int) -> tuple[DiffResult, str]:
    owner, name = parse_github_repo(repo)
    if staged:
        raise LLMScribeError("unsupported_operation", "'staged' is not available for GitHub repositories.")
    if not commit or not commit.strip():
        raise LLMScribeError("invalid_argument", "GitHub diffs need 'commit' (the base branch, tag or SHA).")
    base = validate_github_ref(commit)
    head = validate_github_ref(ref) if ref and ref.strip() else "HEAD"
    payload = fetch_github_diff(owner, name, base, head)

    files = [f for f in payload.get("files", []) if isinstance(f, dict) and f.get("filename")]
    changes: list[GitStatusEntry] = []
    patches: list[str] = []
    without_patch = 0
    for item in files:
        filename = str(item["filename"])
        status = _GITHUB_STATUS.get(str(item.get("status", "")), "M")
        previous = item.get("previous_filename")
        changes.append(GitStatusEntry(status, filename, str(previous) if previous else None))
        patch = item.get("patch")
        if patch:
            patches.append(f"--- a/{previous or filename}\n+++ b/{filename}\n{patch}")
        else:
            without_patch += 1
    text = "\n\n".join(patches)
    truncated = len(text) > max_chars
    if truncated:
        text = text[:max_chars] + f"\n\n[Diff truncated after {max_chars:,} characters]"
    notes = []
    if without_patch:
        notes.append(f"{without_patch} file(s) have no textual patch (binary or too large).")
    if len(files) >= _GITHUB_COMPARE_FILE_LIMIT:
        notes.append(f"GitHub lists at most {_GITHUB_COMPARE_FILE_LIMIT} changed files; the list may be incomplete.")
    logical = f"github.com/{owner}/{name}" + (f"@{ref.strip()}" if ref and ref.strip() else "")
    result = DiffResult(
        root_path=logical,
        staged=False,
        commit=base,
        changed_files=[c.file_path for c in changes],
        status_lines=[f"{c.status} {c.original_path + ' -> ' if c.original_path else ''}{c.file_path}" for c in changes],
        changes=changes,
        diff=text,
        truncated=truncated,
        truncation_limit=max_chars,
        character_count=len(text),
        note=" ".join(notes),
    )
    return result, logical


# --------------------------------------------------------------------------- execute

def execute(
    tool: str,
    *,
    path: str | None = None,
    repo: str | None = None,
    ref: str | None = None,
    allowed_roots: Sequence[Path] | None = None,
    query: str | None = None,
    file_path: str | None = None,
    file_paths: list[str] | None = None,
    staged: bool = False,
    commit: str | None = None,
) -> ToolResponse:
    """Run ``tool`` and return its result; raises ``LLMScribeError`` on any expected failure."""
    if tool not in TOOLS:
        raise LLMScribeError("invalid_argument", f"Unknown tool: '{tool}'.")

    if tool == "project_diff":
        if repo and repo.strip():
            if path and path.strip():
                raise LLMScribeError("invalid_argument", "Cannot specify both 'path' and 'repo'.")
            result, logical = _github_diff(repo, ref, staged, commit, MAX_DIFF_CHARS)
            return _diff_response(result, logical, "github")
        if ref and ref.strip():
            raise LLMScribeError("invalid_argument", "'ref' can only be used together with 'repo'.")
        source = _open_local(path if path and path.strip() else None, allowed_roots)
        return _diff_response(get_git_diff(source.root, staged=staged, commit=commit), source.logical_path, "local")

    source = open_source(path, repo, ref, allowed_roots)
    kind = source.kind
    logical = source.logical_path

    if tool == "project_map":
        pm = map_source(source)
        meta = {"file_count": pm.file_count, "character_count": pm.character_count, "truncated": pm.truncated}
        if pm.truncated:
            meta["truncation_note"] = pm.truncation_note
        return ToolResponse(tool, logical, kind, pm.to_dict(), meta, _md_map(pm))

    if tool == "project_overview":
        ov = overview_source(source)
        meta = {"file_count": ov.file_count, "character_count": ov.character_count, "truncated": ov.truncated}
        if ov.truncated:
            meta["truncation_note"] = ov.truncation_note
        return ToolResponse(tool, logical, kind, ov.to_dict(), meta, _md_overview(ov))

    if tool == "search":
        sr = search_source(source, query or "", MAX_SEARCH_RESULTS)
        meta = {
            "query": sr.query,
            "file_count": sr.file_count,
            "match_count": sr.match_count,
            "truncated": sr.truncated,
            "skipped_count": sr.skipped_count,
        }
        return ToolResponse(tool, logical, kind, sr.to_dict(), meta, _md_search(sr))

    if tool == "read":
        fr = read_from_source(source, file_path or "")
        if not fr.ok:
            raise LLMScribeError(fr.error_code, fr.error_message)
        meta = {"character_count": fr.character_count, "truncated": fr.truncated, "encoding": fr.encoding}
        return ToolResponse(tool, logical, kind, fr.to_dict(), meta, f"--- {fr.file_path} ---\n{fr.content}")

    if tool == "read_many":
        rm = read_many_from_source(source, list(file_paths or []))
        if not rm.ok:
            raise LLMScribeError(rm.error_code, rm.error_message)
        meta = {
            "file_count": rm.file_count,
            "success_count": rm.success_count,
            "error_count": rm.error_count,
            "character_count": rm.character_count,
            "truncated": rm.truncated,
        }
        if rm.truncated:
            meta["truncation_note"] = rm.truncation_note
        return ToolResponse(tool, logical, kind, rm.to_dict(), meta, _md_read_many(rm))

    dr = analyze_source_dependencies(source, file_path or "")
    fd = dr.file_dependencies
    meta = {
        "local_count": len(fd.local_dependencies),
        "external_count": len(fd.external_dependencies),
        "stdlib_count": len(fd.stdlib_dependencies),
        "unresolved_count": len(fd.unresolved_dependencies),
        "used_by_count": len(dr.used_by),
    }
    return ToolResponse(tool, logical, kind, dr.to_dict(), meta, _md_dependencies(dr))


def _diff_response(result: DiffResult, logical: str, kind: str) -> ToolResponse:
    meta = {
        "changed_file_count": len(result.changed_files),
        "character_count": result.character_count,
        "truncated": result.truncated,
    }
    if result.note:
        meta["note"] = result.note
    return ToolResponse("project_diff", logical, kind, result.to_dict(), meta, _md_diff(result))


# --------------------------------------------------------------------------- markdown bodies

def _md_map(pm: Any) -> str:
    text = f"Selected Files Directory Structure:\n\n{pm.tree}"
    if pm.truncated:
        text += f"\n\n[{pm.truncation_note}]"
    return text


def _md_overview(ov: Any) -> str:
    files = "\n\n".join(f"--- {f['path']} ---\n{f['content']}" for f in ov.files)
    text = f"Selected Files Directory Structure:\n\n{ov.tree}\n\nFile Contents:\n{files}"
    if ov.skipped_count:
        text += f"\n\n[{ov.skipped_count} file(s) skipped: unreadable, binary or too large]"
    if ov.truncated:
        text += f"\n\n[{ov.truncation_note}]"
    return text


def _md_search(sr: Any) -> str:
    if not sr.matches:
        return f"No matches for '{sr.query}'"
    by_file: dict[str, list[Any]] = {}
    for match in sr.matches:
        by_file.setdefault(match.file_path, []).append(match)
    blocks = []
    for file_path in sorted(by_file):
        lines = [f"File: {file_path}"]
        content = [m for m in by_file[file_path] if m.match_type == "content"]
        if any(m.match_type == "filename" for m in by_file[file_path]):
            lines.append("  (Filename match)")
        lines.extend(f"  Line {m.line_number}: {m.line_content}" for m in content[:_SEARCH_LINES_PER_FILE])
        if len(content) > _SEARCH_LINES_PER_FILE:
            lines.append(f"  ... ({len(content) - _SEARCH_LINES_PER_FILE} more)")
        blocks.append("\n".join(lines))
    text = f"Search results for '{sr.query}':\n\n" + "\n\n".join(blocks)
    if sr.truncated:
        text += f"\n\n[Results limited to {sr.truncation_limit:,} matches]"
    return text


def _md_read_many(rm: Any) -> str:
    parts = []
    for item in rm.results:
        if item.ok:
            parts.append(f"--- {item.file_path} ---\n{item.content}")
        else:
            parts.append(f"--- {item.file_path} ---\nError [{item.error_code}]: {item.error_message}")
    text = "\n\n".join(parts)
    if rm.omitted_files:
        text += f"\n\nNot read: {', '.join(rm.omitted_files[:20])}" + (" ..." if len(rm.omitted_files) > 20 else "")
    if rm.truncated:
        text += f"\n\n[{rm.truncation_note}]"
    return text


def _md_dependencies(dr: Any) -> str:
    fd = dr.file_dependencies
    lines = [f"File: {dr.target_file}"]
    for title, items in (
        ("Local dependencies", fd.local_dependencies),
        ("Standard library", fd.stdlib_dependencies),
        ("External dependencies", fd.external_dependencies),
        ("Unresolved", fd.unresolved_dependencies),
        ("Used by", dr.used_by),
    ):
        if items:
            lines.append(f"\n{title}:\n" + "\n".join(f"- {i}" for i in items))
    if len(lines) == 1:
        lines.append("\nNo dependencies and no dependents found.")
    return "\n".join(lines)


def _md_diff(result: DiffResult) -> str:
    parts = ["### Changes"]
    if result.changes:
        parts.append("Changed Files:\n" + "\n".join(f"- {line}" for line in result.status_lines))
    else:
        parts.append("No changed files.")
    if result.note:
        parts.append(f"Note: {result.note}")
    parts.append(f"Diff:\n```diff\n{result.diff}\n```" if result.diff.strip() else "Diff is empty.")
    return "\n\n".join(parts)


# --------------------------------------------------------------------------- rendering

def _dumps(payload: dict[str, Any]) -> str:
    return redact(json.dumps(payload, indent=2, ensure_ascii=False))


def envelope(response: ToolResponse) -> dict[str, Any]:
    """The JSON success envelope (identical shape for every tool and source)."""
    return {
        "ok": True,
        "tool": response.tool,
        "source": response.source,
        "path": response.path,
        "data": response.data,
        "metadata": response.metadata,
    }


def error_envelope(tool: str, error: LLMScribeError) -> dict[str, Any]:
    """The JSON error envelope."""
    return {"ok": False, "tool": tool, "error": error.to_dict()}


def render_json(response: ToolResponse) -> str:
    return _dumps(envelope(response))


def render_markdown(response: ToolResponse) -> str:
    return redact(f"### llmscribe: {response.tool}\nPath: {response.path}\n\n{response.text}")


def render_error(tool: str, error: LLMScribeError, as_json: bool) -> str:
    if as_json:
        return _dumps(error_envelope(tool, error))
    return redact(f"### llmscribe: {tool}\nError [{error.code}]: {error.message}")


def redact_text(text: str) -> str:
    """Strip any GitHub token from ``text`` before it is printed."""
    return redact(text)


def to_error(exc: Exception) -> LLMScribeError:
    """Map any exception to a safe ``LLMScribeError`` (no tracebacks or internals leak)."""
    if isinstance(exc, LLMScribeError):
        return exc
    logger.error("Unexpected error in tool execution", exc_info=exc)
    return LLMScribeError("internal_error", "An unexpected error occurred while running the tool.")


def run(tool: str, as_json: bool, **kwargs: Any) -> str:
    """Execute ``tool`` and return the final text; failures become structured errors."""
    try:
        response = execute(tool, **kwargs)
    except Exception as exc:  # noqa: BLE001 - every failure is converted to a structured error
        return render_error(tool, to_error(exc), as_json)
    return render_json(response) if as_json else render_markdown(response)

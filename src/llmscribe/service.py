"""One implementation of every LLMScribe tool, shared by the MCP server and the CLI.

``execute`` resolves a local project, runs the operation and returns a
``ToolResponse``. ``render_json`` / ``render_markdown`` / ``render_error``
produce the public output, so every surface has the same schema and the same
error contract.
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
    analyze_source_impact,
    get_git_diff,
    map_source,
    overview_source,
    read_from_source,
    read_many_from_source,
    search_source,
)
from llmscribe.core.diff import DiffResult
from llmscribe.core.limits import MAX_SEARCH_RESULTS

logger = logging.getLogger("llmscribe")

TOOLS = (
    "project_map",
    "project_overview",
    "search",
    "read",
    "read_many",
    "project_dependencies",
    "project_diff",
    "project_impact",
)

_SEARCH_LINES_PER_FILE = 10


@dataclass
class ToolResponse:
    """A successful tool result."""

    tool: str
    path: str
    source: str  # always "local"
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    text: str = ""  # markdown body


# --------------------------------------------------------------------------- sources

def open_source(
    path: str | None = None,
    allowed_roots: Sequence[Path] | None = None,
) -> RepositorySource:
    """Resolve ``path`` to a local ``RepositorySource``.

    ``allowed_roots`` restricts local access (``None`` = unrestricted, empty =
    local access disabled), which deployments use to limit which directories the
    server may read.
    """
    return _open_local(path if path and path.strip() else None, allowed_roots)


def _open_local(path: str | None, allowed_roots: Sequence[Path] | None) -> LocalRepository:
    if allowed_roots is not None:
        if not allowed_roots:
            raise LLMScribeError("unsupported_operation", "Local paths are disabled on this server.")
        source = LocalRepository(path)
        if not any(source.root == r or r in source.root.parents for r in allowed_roots):
            raise LLMScribeError("invalid_path", "That path is outside the directories this server may read.")
        return source
    return LocalRepository(path)


# --------------------------------------------------------------------------- execute

def execute(
    tool: str,
    *,
    path: str | None = None,
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
        source = _open_local(path if path and path.strip() else None, allowed_roots)
        return _diff_response(get_git_diff(source.root, staged=staged, commit=commit), source.logical_path)

    source = open_source(path, allowed_roots)
    kind = source.kind
    logical = source.logical_path

    if tool == "project_impact":
        seeds = list(file_paths or [])
        if not seeds:
            seeds = get_git_diff(source.root, staged=staged, commit=commit).changed_files
        ir = analyze_source_impact(source, seeds)
        meta = {
            "changed_count": len(ir.changed),
            "affected_count": len(ir.affected),
            "not_in_graph_count": len(ir.not_in_graph),
            "max_depth": ir.max_depth,
            "truncated": ir.truncated,
        }
        if ir.note:
            meta["note"] = ir.note
        return ToolResponse(tool, logical, kind, ir.to_dict(), meta, _md_impact(ir))

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

    if tool != "project_dependencies":
        raise LLMScribeError("invalid_argument", f"Unknown tool: '{tool}'.")

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


def _diff_response(result: DiffResult, logical: str) -> ToolResponse:
    meta = {
        "changed_file_count": len(result.changed_files),
        "character_count": result.character_count,
        "truncated": result.truncated,
    }
    if result.note:
        meta["note"] = result.note
    return ToolResponse("project_diff", logical, "local", result.to_dict(), meta, _md_diff(result))


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


def _md_impact(ir: Any) -> str:
    parts = ["### Changed"]
    parts.append("\n".join(f"- {p}" for p in ir.changed) if ir.changed else "No changed files.")

    if ir.not_in_graph:
        parts.append(
            "Outside the import graph (config, docs, data — no callers to trace):\n"
            + "\n".join(f"- {p}" for p in ir.not_in_graph)
        )

    parts.append("### Affected")
    if ir.affected:
        entries = []
        for entry in ir.affected:
            chain = " -> ".join(entry.via)
            entries.append(f"- {entry.file_path} (depth {entry.depth})\n  {chain}")
        parts.append("\n\n".join(entries))
    else:
        parts.append("No file imports the changed files.")

    if ir.note:
        parts.append(f"Note: {ir.note}")
    return "\n\n".join(parts)


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
    return json.dumps(payload, indent=2, ensure_ascii=False)


def envelope(response: ToolResponse) -> dict[str, Any]:
    """The JSON success envelope (identical shape for every tool)."""
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
    return f"### llmscribe: {response.tool}\nPath: {response.path}\n\n{response.text}"


def render_error(tool: str, error: LLMScribeError, as_json: bool) -> str:
    if as_json:
        return _dumps(error_envelope(tool, error))
    return f"### llmscribe: {tool}\nError [{error.code}]: {error.message}"


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

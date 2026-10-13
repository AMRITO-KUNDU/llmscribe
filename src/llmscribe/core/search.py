"""Deterministic substring search over filenames and file contents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LLMScribeError
from .file_reader import decode_text
from .limits import MAX_FILE_SIZE, MAX_LINE_CHARS, MAX_SEARCH_RESULTS
from .source import LocalRepository, RepositorySource


@dataclass
class SearchMatch:
    """A single match: a filename match (line 0) or a matching line."""

    file_path: str
    line_number: int
    line_content: str
    match_type: str = "content"  # "content" or "filename"
    matched_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "match_type": self.match_type,
            "matched_text": self.matched_text,
        }


@dataclass
class SearchResult:
    """All matches for one query. Order: filename matches, then content matches, each by path/line."""

    query: str
    root_path: str
    matches: list[SearchMatch] = field(default_factory=list)
    file_count: int = 0
    match_count: int = 0
    truncated: bool = False
    truncation_limit: int = MAX_SEARCH_RESULTS
    skipped_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "root_path": self.root_path,
            "matches": [m.to_dict() for m in self.matches],
            "file_count": self.file_count,
            "match_count": self.match_count,
            "truncated": self.truncated,
            "truncation_limit": self.truncation_limit,
            "skipped_count": self.skipped_count,
        }


def search_source(
    source: RepositorySource, query: str, max_results: int = MAX_SEARCH_RESULTS
) -> SearchResult:
    """Case-insensitive substring search over file paths and text content.

    Binary and oversized files are skipped (counted in ``skipped_count``). The
    repository is listed once and files are visited in sorted path order.
    """
    if query is None or not str(query).strip():
        raise LLMScribeError("invalid_argument", "Query cannot be empty.")
    if max_results < 1:
        raise LLMScribeError("invalid_argument", "max_results must be at least 1.")
    needle = str(query).strip().lower()
    result = SearchResult(query=str(query), root_path=source.logical_path, truncation_limit=max_results)

    files = source.text_files()
    matched_files: set[str] = set()

    for entry in files:
        if entry.path and needle in entry.path.lower():
            if len(result.matches) >= max_results:
                result.truncated = True
                break
            result.matches.append(SearchMatch(entry.path, 0, "", "filename", entry.path))
            matched_files.add(entry.path)

    for entry in files:
        if len(result.matches) >= max_results and result.truncated:
            break
        if entry.size > MAX_FILE_SIZE:
            result.skipped_count += 1
            continue
        try:
            text, _encoding = decode_text(source.read_bytes(entry.path), entry.path)
        except LLMScribeError:
            result.skipped_count += 1
            continue
        if needle not in text.lower():
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            position = line.lower().find(needle)
            if position == -1:
                continue
            if len(result.matches) >= max_results:
                result.truncated = True
                break
            clipped = line.rstrip()
            if len(clipped) > MAX_LINE_CHARS:
                clipped = clipped[:MAX_LINE_CHARS] + "…"
            result.matches.append(
                SearchMatch(entry.path, line_number, clipped, "content", line[position : position + len(needle)])
            )
            matched_files.add(entry.path)

    result.match_count = len(result.matches)
    result.file_count = len(matched_files)
    return result


def search_project(
    query: str,
    root: Path | None = None,
    max_results: int = MAX_SEARCH_RESULTS,
    ignore_patterns: list[str] | None = None,
) -> SearchResult:
    """Search a local project. Raises ``LLMScribeError`` for an empty query or bad root."""
    if query is None or not str(query).strip():
        raise LLMScribeError("invalid_argument", "Query cannot be empty.")
    return search_source(LocalRepository(root, ignore_patterns), query, max_results)


def search_project_simple(
    query: str,
    root: Path | None = None,
    max_results: int = MAX_SEARCH_RESULTS,
    ignore_patterns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Convenience wrapper returning the matches as plain dictionaries."""
    return [m.to_dict() for m in search_project(query, root, max_results, ignore_patterns).matches]

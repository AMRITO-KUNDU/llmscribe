"""Project map, overview and file listing for any repository source."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LLMScribeError
from .file_ops import TRUNCATION_MARKER, load_text
from .limits import MAX_CONTENT_CHARS, MAX_MAP_ENTRIES
from .source import LocalRepository, RepositorySource
from .tree_builder import render_tree

MAX_SKIPPED_REPORTED = 100


@dataclass
class ProjectMapResult:
    """Directory tree plus the list of supported text files."""

    root_path: str
    tree: str
    files: list[str] = field(default_factory=list)
    file_count: int = 0
    character_count: int = 0
    truncated: bool = False
    truncation_note: str = ""
    truncation_limit: int = MAX_MAP_ENTRIES
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "tree": self.tree,
            "files": self.files,
            "file_count": self.file_count,
            "character_count": self.character_count,
            "truncated": self.truncated,
            "truncation_note": self.truncation_note,
            "truncation_limit": self.truncation_limit,
            "warnings": self.warnings,
        }


@dataclass
class ProjectOverviewResult:
    """Tree plus the contents of supported text files, bounded by a character budget."""

    root_path: str
    tree: str
    files: list[dict[str, str]] = field(default_factory=list)
    file_count: int = 0
    character_count: int = 0
    truncated: bool = False
    truncation_note: str = ""
    truncation_limit: int = MAX_CONTENT_CHARS
    omitted_files: list[str] = field(default_factory=list)
    skipped_files: list[dict[str, str]] = field(default_factory=list)
    skipped_count: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "tree": self.tree,
            "files": self.files,
            "file_count": self.file_count,
            "character_count": self.character_count,
            "truncated": self.truncated,
            "truncation_note": self.truncation_note,
            "truncation_limit": self.truncation_limit,
            "omitted_files": self.omitted_files,
            "skipped_files": self.skipped_files,
            "skipped_count": self.skipped_count,
            "warnings": self.warnings,
        }


def map_source(source: RepositorySource) -> ProjectMapResult:
    """Build the tree and file list of ``source`` (bounded to ``MAX_MAP_ENTRIES`` entries)."""
    scan = source.scan()
    entries = scan.entries
    notes: list[str] = []
    truncated = scan.truncated
    if scan.truncated:
        notes.append("Repository scan stopped at the maximum entry count.")
    if len(entries) > MAX_MAP_ENTRIES:
        notes.append(f"Listing limited to the first {MAX_MAP_ENTRIES:,} of {len(entries):,} entries.")
        entries = entries[:MAX_MAP_ENTRIES]
        truncated = True
    from .file_reader import is_text_file

    tree = render_tree(source.name, ((e.path, e.is_dir) for e in entries))
    files = [e.path for e in entries if not e.is_dir and is_text_file(e.path)]
    return ProjectMapResult(
        root_path=source.logical_path,
        tree=tree,
        files=files,
        file_count=len(files),
        character_count=len(tree),
        truncated=truncated,
        truncation_note=" ".join(notes),
        warnings=list(scan.warnings),
    )


def overview_source(source: RepositorySource, max_content_chars: int = MAX_CONTENT_CHARS) -> ProjectOverviewResult:
    """Tree plus file contents. Files that cannot be read are listed in ``skipped_files``."""
    project = map_source(source)
    result = ProjectOverviewResult(
        root_path=project.root_path,
        tree=project.tree,
        truncated=project.truncated,
        truncation_note=project.truncation_note,
        truncation_limit=max_content_chars,
        warnings=project.warnings,
    )
    remaining = max_content_chars
    total = 0
    exhausted = False
    for path in project.files:
        if not exhausted and remaining <= 0:
            exhausted = True
        if exhausted:
            result.omitted_files.append(path)
            continue
        try:
            rel, text, _encoding = load_text(source, path)
        except LLMScribeError as exc:
            result.skipped_count += 1
            if len(result.skipped_files) < MAX_SKIPPED_REPORTED:
                result.skipped_files.append({"path": path, "error_code": exc.code})
            continue
        if len(text) > remaining:
            text = text[:remaining] + TRUNCATION_MARKER
            exhausted = True
        remaining -= len(text) if not exhausted else 0
        total += len(text)
        result.files.append({"path": rel, "content": text})
    if exhausted:
        result.truncated = True
        note = f"File content capped at {max_content_chars:,} characters"
        if result.omitted_files:
            note += f"; {len(result.omitted_files)} file(s) omitted"
        result.truncation_note = " ".join(filter(None, [result.truncation_note, note + "."]))
    result.file_count = len(result.files)
    result.character_count = len(project.tree) + total
    return result


def list_source_files(source: RepositorySource, extension: str | None = None) -> list[str]:
    """Supported text files of ``source``, optionally filtered by extension."""
    wanted = None
    if extension and extension.strip():
        ext = extension.strip().lower()
        wanted = ext if ext.startswith(".") else f".{ext}"
    paths = [e.path for e in source.text_files()]
    if wanted:
        paths = [p for p in paths if p.lower().endswith(wanted)]
    return paths


def project_map(root: Path | None = None, ignore_patterns: list[str] | None = None) -> ProjectMapResult:
    """Generate the directory tree and file list of a local project.

    Raises ``LLMScribeError`` (``invalid_path``) when ``root`` is not a directory.
    """
    return map_source(LocalRepository(root, ignore_patterns))


def project_overview(
    root: Path | None = None,
    ignore_patterns: list[str] | None = None,
    max_content_chars: int = MAX_CONTENT_CHARS,
) -> ProjectOverviewResult:
    """Generate the tree plus contents of a local project."""
    return overview_source(LocalRepository(root, ignore_patterns), max_content_chars)


def list_files(
    root: Path | None = None,
    extension: str | None = None,
    ignore_patterns: list[str] | None = None,
) -> list[str]:
    """List supported text files of a local project, optionally filtered by extension."""
    return list_source_files(LocalRepository(root, ignore_patterns), extension)

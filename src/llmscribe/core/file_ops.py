"""Reading files: one file, or many, with structured per-file errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LLMScribeError
from .file_reader import decode_text, is_text_file
from .limits import MAX_CONTENT_CHARS, MAX_FILE_SIZE, MAX_READ_MANY_FILES
from .source import LocalRepository, RepositorySource, normalize_rel_path

TRUNCATION_MARKER = "\n[Content truncated]"


@dataclass
class FileReadResult:
    """Result of reading a single file."""

    file_path: str
    content: str = ""
    character_count: int = 0
    ok: bool = True
    error_code: str = ""
    error_message: str = ""
    encoding: str = ""
    truncated: bool = False

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"file_path": self.file_path, "ok": self.ok}
        if self.ok:
            result["content"] = self.content
            result["character_count"] = self.character_count
            result["encoding"] = self.encoding
            result["truncated"] = self.truncated
        else:
            result["error"] = {"code": self.error_code, "message": self.error_message}
        return result


@dataclass
class ReadManyResult:
    """Result of reading several files. ``ok`` is False only for call-level errors."""

    root_path: str = ""
    results: list[FileReadResult] = field(default_factory=list)
    file_count: int = 0
    success_count: int = 0
    error_count: int = 0
    character_count: int = 0
    truncated: bool = False
    truncation_limit: int = MAX_READ_MANY_FILES
    truncation_note: str = ""
    omitted_files: list[str] = field(default_factory=list)
    ok: bool = True
    error_code: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "root_path": self.root_path,
            "results": [r.to_dict() for r in self.results],
            "file_count": self.file_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "character_count": self.character_count,
            "truncated": self.truncated,
            "truncation_limit": self.truncation_limit,
            "truncation_note": self.truncation_note,
            "omitted_files": self.omitted_files,
        }
        if not self.ok:
            data["ok"] = False
            data["error"] = {"code": self.error_code, "message": self.error_message}
        return data


def _failure(file_path: str, error: LLMScribeError) -> FileReadResult:
    return FileReadResult(file_path="" if file_path is None else str(file_path), ok=False, error_code=error.code, error_message=error.message)


def load_text(source: RepositorySource, raw_path: str) -> tuple[str, str, str]:
    """Validate, read and decode one file. Returns ``(rel_path, text, encoding)``.

    Raises ``LLMScribeError`` with a stable code for every failure mode.
    """
    rel = normalize_rel_path(raw_path)
    entry = source.info(rel)
    if not is_text_file(rel):
        raise LLMScribeError("unsupported_file_type", f"'{rel}' is not a recognized text file type.")
    if entry.size > MAX_FILE_SIZE:
        raise LLMScribeError("file_too_large", f"File exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'.")
    text, encoding = decode_text(source.read_bytes(rel), rel)
    return rel, text, encoding


def _clip(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit] + TRUNCATION_MARKER, True


def read_from_source(
    source: RepositorySource, file_path: str, max_content_chars: int = MAX_CONTENT_CHARS
) -> FileReadResult:
    """Read one file from any source. Never raises for per-file problems."""
    try:
        rel, text, encoding = load_text(source, file_path)
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    content, truncated = _clip(text, max_content_chars)
    return FileReadResult(rel, content, len(content), True, encoding=encoding, truncated=truncated)


def read_many_from_source(
    source: RepositorySource,
    file_paths: list[str],
    max_files: int = MAX_READ_MANY_FILES,
    max_content_chars: int = MAX_CONTENT_CHARS,
) -> ReadManyResult:
    """Read several files; one bad file never affects the others."""
    result = ReadManyResult(root_path=source.logical_path, truncation_limit=max_files)
    if not file_paths:
        result.ok = False
        result.error_code = "invalid_argument"
        result.error_message = "file_paths must contain at least one path."
        return result

    result.file_count = len(file_paths)
    notes: list[str] = []
    batch = file_paths
    if len(file_paths) > max_files:
        batch = file_paths[:max_files]
        result.omitted_files = [str(p) for p in file_paths[max_files:]]
        notes.append(f"Processed the first {max_files} of {len(file_paths)} requested files.")

    remaining = max_content_chars
    for index, raw in enumerate(batch):
        if remaining <= 0:
            result.omitted_files.extend(str(p) for p in batch[index:])
            notes.append(f"Total content capped at {max_content_chars:,} characters.")
            break
        item = read_from_source(source, raw, max_content_chars=remaining)
        result.results.append(item)
        if not item.ok:
            result.error_count += 1
            continue
        result.success_count += 1
        remaining -= item.character_count
        result.character_count += item.character_count
        if item.truncated:
            notes.append(f"Content of '{item.file_path}' was truncated at the size limit.")
            remaining = 0

    if notes:
        result.truncated = True
        result.truncation_note = " ".join(dict.fromkeys(notes))
    return result


def read_file(
    file_path: str, root: Path | None = None, max_content_chars: int = MAX_CONTENT_CHARS
) -> FileReadResult:
    """Read one file below ``root`` (default: current directory)."""
    try:
        source = LocalRepository(root)
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    return read_from_source(source, file_path, max_content_chars)


def read_files(
    file_paths: list[str],
    root: Path | None = None,
    max_files: int = MAX_READ_MANY_FILES,
    max_content_chars: int = MAX_CONTENT_CHARS,
) -> ReadManyResult:
    """Read several files below ``root``. Always returns a ``ReadManyResult``."""
    try:
        source = LocalRepository(root)
    except LLMScribeError as exc:
        return ReadManyResult(
            root_path=str(root) if root is not None else "",
            file_count=len(file_paths or []),
            ok=False,
            error_code=exc.code,
            error_message=exc.message,
        )
    return read_many_from_source(source, file_paths, max_files, max_content_chars)

"""Reading files: one file, or many, with structured per-file errors."""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .compress import compress_python, is_compressible
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
    byte_size: int = 0
    line_count: int = 0
    modified: str = ""
    media_type: str = ""
    compressed: bool = False
    line_start: int = 0
    line_end: int = 0
    returned_lines: int = 0
    replaced_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"file_path": self.file_path, "ok": self.ok}
        if self.ok:
            result["content"] = self.content
            result["character_count"] = self.character_count
            result["byte_size"] = self.byte_size
            result["line_count"] = self.line_count
            result["modified"] = self.modified
            if self.compressed:
                result["compressed"] = True
            if self.replaced_bytes:
                # the file has bytes its encoding does not define; they were shown as U+FFFD
                result["lossy"] = True
                result["replaced_bytes"] = self.replaced_bytes
            if self.line_start:
                # present only for a ranged read, so the default shape is unchanged
                result["line_start"] = self.line_start
                result["line_end"] = self.line_end
                result["returned_lines"] = self.returned_lines
            if self.media_type:
                # binary payload: content is base64, not text
                result["media_type"] = self.media_type
                result["base64"] = True
            else:
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


def _iso_utc(epoch: float) -> str:
    """Modified time as an ISO 8601 UTC string, or '' when the source has none."""
    if not epoch:
        return ""
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="seconds")


def read_from_source(
    source: RepositorySource,
    file_path: str,
    max_content_chars: int = MAX_CONTENT_CHARS,
    binary: bool = False,
    compress: bool = False,
    start_line: int | None = None,
    end_line: int | None = None,
) -> FileReadResult:
    """Read one file from any source. Never raises for per-file problems.

    ``binary=True`` skips decoding: ``content`` is base64 and ``media_type`` carries
    the guessed MIME type. That exists for an explicit request to look at an image or
    a PDF - binaries stay excluded from overview and read_many, which is where context
    would otherwise be wasted.

    ``start_line`` and ``end_line`` are 1-based and inclusive. Asking for lines 200-250
    of a 5,000-line file returns 51 lines, not 5,000 - the cheapest way to keep a large
    file out of a context window. ``line_count`` always reports the whole file, so the
    caller can tell there is more.
    """
    if binary:
        return _read_binary(source, file_path, max_content_chars)
    try:
        rel, text, encoding = load_text(source, file_path)
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    # Whole-file line count, before any range, compression or clipping, so it always
    # answers the question `wc -l` answers.
    line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)

    ranged = start_line is not None or end_line is not None
    if ranged and compress:
        raise LLMScribeError(
            "invalid_argument",
            "start_line/end_line cannot be combined with compress: compression rewrites "
            "the file, so line numbers would no longer refer to what you asked for.",
        )

    line_start = line_end = returned_lines = 0
    if ranged:
        first = 1 if start_line is None else start_line
        if first < 1:
            raise LLMScribeError("invalid_argument", "start_line must be 1 or greater.")
        if end_line is not None and end_line < first:
            raise LLMScribeError("invalid_argument", "end_line must be greater than or equal to start_line.")
        lines = text.splitlines(keepends=True)
        last = len(lines) if end_line is None else end_line
        selected = lines[first - 1 : last]
        text = "".join(selected)
        line_start, line_end, returned_lines = first, last, len(selected)

    was_compressed = False
    if compress and is_compressible(rel):
        squeezed = compress_python(text)
        if squeezed is not None:
            text, was_compressed = squeezed, True

    content, truncated = _clip(text, max_content_chars)
    entry = source.info(rel)
    # cp1252 is the only decoder that substitutes, so a U+FFFD in its output means a
    # byte in the file has no mapping. Say so rather than showing a replacement char
    # and letting the reader believe that is the file's content.
    replaced = text.count("\ufffd") if encoding == "cp1252" else 0
    return FileReadResult(
        rel,
        content,
        len(content),
        True,
        encoding=encoding,
        replaced_bytes=replaced,
        truncated=truncated,
        byte_size=entry.size,
        line_count=line_count,
        modified=_iso_utc(entry.mtime),
        compressed=was_compressed,
        line_start=line_start,
        line_end=line_end,
        returned_lines=returned_lines,
    )


def _read_binary(source: RepositorySource, raw_path: str, max_content_chars: int) -> FileReadResult:
    """Read any regular file as base64, regardless of extension."""
    try:
        rel = normalize_rel_path(raw_path)
        entry = source.info(rel)
    except LLMScribeError as exc:
        return _failure(raw_path, exc)
    if entry.size > MAX_FILE_SIZE:
        return _failure(rel, LLMScribeError("file_too_large", f"File exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'."))
    try:
        raw = source.read_bytes(rel)
    except LLMScribeError as exc:
        return _failure(rel, exc)
    encoded = base64.b64encode(raw).decode("ascii")
    clipped = encoded[:max_content_chars]
    return FileReadResult(
        rel,
        clipped,
        len(clipped),
        True,
        truncated=len(clipped) < len(encoded),
        byte_size=entry.size,
        line_count=0,
        modified=_iso_utc(entry.mtime),
        media_type=mimetypes.guess_type(rel)[0] or "application/octet-stream",
    )


def read_many_from_source(
    source: RepositorySource,
    file_paths: list[str],
    max_files: int = MAX_READ_MANY_FILES,
    max_content_chars: int = MAX_CONTENT_CHARS,
    start_line: int | None = None,
    end_line: int | None = None,
) -> ReadManyResult:
    """Read several files; one bad file never affects the others.

    ``start_line``/``end_line`` apply to *every* file in the batch - the useful shape
    when you want the top of each file rather than all of them.
    """
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
        item = read_from_source(
            source, raw, max_content_chars=remaining, start_line=start_line, end_line=end_line
        )
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
    file_path: str,
    root: Path | None = None,
    max_content_chars: int = MAX_CONTENT_CHARS,
    binary: bool = False,
    compress: bool = False,
    start_line: int | None = None,
    end_line: int | None = None,
) -> FileReadResult:
    """Read one file below ``root`` (default: current directory)."""
    try:
        source = LocalRepository(root)
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    return read_from_source(
        source, file_path, max_content_chars, binary, compress, start_line, end_line
    )


def read_files(
    file_paths: list[str],
    root: Path | None = None,
    max_files: int = MAX_READ_MANY_FILES,
    max_content_chars: int = MAX_CONTENT_CHARS,
    start_line: int | None = None,
    end_line: int | None = None,
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
    return read_many_from_source(
        source, file_paths, max_files, max_content_chars, start_line, end_line
    )

"""Operations that change the working tree.

A filesystem layer an agent cannot write through is a reader, not a layer. These exist so
an agent doing real code work — creating a file, replacing a function body, renaming a
module, making a directory, removing a dead file — does not have to shell out to a
different command on every operating system.

They are held to the same standards as the read side: every path goes through the same
traversal and symlink checks, writes are atomic, and every result reports exactly what
changed. A write that would land outside the project is refused, not sanitised.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import LLMScribeError
from .limits import MAX_FILE_SIZE
from .source import LocalRepository, normalize_rel_path


@dataclass
class WriteResult:
    """What a write operation did."""

    path: str
    ok: bool = True
    action: str = ""
    existed: bool = False
    byte_size: int = 0
    bytes_written: int = 0
    replacements: int = 0
    destination: str = ""
    error_code: str = ""
    error_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"path": self.path, "ok": self.ok}
        if self.ok:
            result["action"] = self.action
            result["byte_size"] = self.byte_size
            if self.bytes_written:
                result["bytes_written"] = self.bytes_written
            if self.action in {"created", "overwritten"}:
                result["existed"] = self.existed
            if self.replacements:
                result["replacements"] = self.replacements
            if self.destination:
                result["destination"] = self.destination
        else:
            result["error"] = {"code": self.error_code, "message": self.error_message}
        return result


def _failure(path: str, error: LLMScribeError) -> WriteResult:
    return WriteResult(path, ok=False, error_code=error.code, error_message=error.message)


def _open_source(root: Path | str | None) -> LocalRepository:
    return LocalRepository(root)


def _target(source: LocalRepository, raw: str, *, must_exist: bool) -> tuple[str, Path]:
    """Resolve a path for writing, with the same guards the read side uses.

    ``normalize_rel_path`` rejects absolute paths, ``..`` segments (including encoded and
    backslash forms) and NUL bytes; this adds the symlink check per component and the
    final containment check, so a write cannot be redirected outside the root.
    """
    rel = normalize_rel_path(raw)
    current = source.root
    for part in rel.split("/"):
        current = current / part
        try:
            if current.is_symlink():
                raise LLMScribeError("invalid_path", f"Symlinks are not followed: '{rel}'.")
        except OSError as exc:
            raise LLMScribeError("write_error", f"Cannot access '{rel}': {exc.strerror or 'error'}.") from exc

    try:
        current.resolve().relative_to(source.root)
    except (ValueError, OSError) as exc:
        raise LLMScribeError("invalid_path", f"Path escapes the repository root: '{rel}'.") from exc

    if must_exist:
        if not current.exists():
            raise LLMScribeError("file_not_found", f"File does not exist: '{rel}'.")
        if not current.is_file():
            raise LLMScribeError("invalid_path", f"Path is not a regular file: '{rel}'.")
    else:
        parent = current.parent
        if parent != source.root and not parent.exists():
            relative_parent = parent.relative_to(source.root).as_posix()
            raise LLMScribeError(
                "invalid_path",
                f"Parent directory does not exist: '{relative_parent}'. Create it first.",
            )
    return rel, current


def _atomic_write(target: Path, data: bytes) -> None:
    """Write via a temporary file in the same directory, then replace.

    A crash mid-write leaves the original intact rather than a half-written file, which
    matters when an agent is rewriting source it cannot easily recover.
    """
    temp = target.with_name(f".{target.name}.llmscribe-tmp")
    try:
        temp.write_bytes(data)
        os.replace(temp, target)
    finally:
        if temp.exists():
            temp.unlink(missing_ok=True)


def write_file(
    file_path: str,
    content: str,
    root: Path | str | None = None,
    *,
    overwrite: bool = True,
) -> WriteResult:
    """Create or replace a file. ``overwrite=False`` refuses to clobber an existing one."""
    try:
        source = _open_source(root)
        rel, target = _target(source, file_path, must_exist=False)
        existed = target.exists()
        if existed and not overwrite:
            raise LLMScribeError("file_exists", f"File already exists: '{rel}'. Pass overwrite to replace it.")
        data = content.encode("utf-8")
        if len(data) > MAX_FILE_SIZE:
            raise LLMScribeError(
                "file_too_large", f"Content exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'."
            )
        _atomic_write(target, data)
        return WriteResult(
            rel,
            action="overwritten" if existed else "created",
            existed=existed,
            byte_size=len(data),
            bytes_written=len(data),
        )
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    except OSError as exc:
        return _failure(file_path, LLMScribeError("write_error", f"Could not write '{file_path}': {exc.strerror or 'error'}."))


def edit_file(
    file_path: str,
    old_text: str,
    new_text: str,
    root: Path | str | None = None,
    *,
    replace_all: bool = False,
) -> WriteResult:
    """Replace an exact substring.

    Exact match rather than a regex or a line range: it is unambiguous, it fails loudly
    when the file has moved on, and it cannot silently rewrite the wrong place.
    """
    try:
        source = _open_source(root)
        rel, target = _target(source, file_path, must_exist=True)
        if not old_text:
            raise LLMScribeError("invalid_argument", "old_text must not be empty.")
        original = target.read_bytes()
        if len(original) > MAX_FILE_SIZE:
            raise LLMScribeError("file_too_large", f"File exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'.")
        text = original.decode("utf-8", errors="replace")
        found = text.count(old_text)
        if found == 0:
            raise LLMScribeError("no_match", f"old_text was not found in '{rel}'.")
        if found > 1 and not replace_all:
            raise LLMScribeError(
                "ambiguous_match",
                f"old_text appears {found} times in '{rel}'. Include more context, or pass replace_all.",
            )
        updated = text.replace(old_text, new_text) if replace_all else text.replace(old_text, new_text, 1)
        data = updated.encode("utf-8")
        if len(data) > MAX_FILE_SIZE:
            raise LLMScribeError("file_too_large", f"Result exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'.")
        _atomic_write(target, data)
        return WriteResult(
            rel,
            action="edited",
            byte_size=len(data),
            bytes_written=len(data),
            replacements=found if replace_all else 1,
        )
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    except OSError as exc:
        return _failure(file_path, LLMScribeError("write_error", f"Could not edit '{file_path}': {exc.strerror or 'error'}."))


def create_directory(directory_path: str, root: Path | str | None = None) -> WriteResult:
    """Create a directory, including any missing parents."""
    try:
        source = _open_source(root)
        rel = normalize_rel_path(directory_path)
        target = source.root
        for part in rel.split("/"):
            target = target / part
            try:
                if target.is_symlink():
                    raise LLMScribeError("invalid_path", f"Symlinks are not followed: '{rel}'.")
            except OSError as exc:
                raise LLMScribeError("write_error", f"Cannot access '{rel}': {exc.strerror or 'error'}.") from exc
        try:
            target.resolve().relative_to(source.root)
        except (ValueError, OSError) as exc:
            raise LLMScribeError("invalid_path", f"Path escapes the repository root: '{rel}'.") from exc
        existed = target.exists()
        if existed and not target.is_dir():
            raise LLMScribeError("invalid_path", f"Path exists and is not a directory: '{rel}'.")
        target.mkdir(parents=True, exist_ok=True)
        return WriteResult(rel, action="directory_created" if not existed else "directory_exists", existed=existed)
    except LLMScribeError as exc:
        return _failure(directory_path, exc)
    except OSError as exc:
        return _failure(directory_path, LLMScribeError("write_error", f"Could not create '{directory_path}': {exc.strerror or 'error'}."))


def move_file(
    source_path: str,
    destination_path: str,
    root: Path | str | None = None,
    *,
    overwrite: bool = False,
) -> WriteResult:
    """Move or rename a file inside the project."""
    try:
        source = _open_source(root)
        rel, target = _target(source, source_path, must_exist=True)
        dest_rel, destination = _target(source, destination_path, must_exist=False)
        if destination.exists() and not overwrite:
            raise LLMScribeError(
                "file_exists",
                f"Destination already exists: '{dest_rel}'. Pass overwrite to replace it.",
            )
        size = target.stat().st_size
        os.replace(target, destination)
        return WriteResult(rel, action="moved", byte_size=size, destination=dest_rel)
    except LLMScribeError as exc:
        return _failure(source_path, exc)
    except OSError as exc:
        return _failure(source_path, LLMScribeError("write_error", f"Could not move '{source_path}': {exc.strerror or 'error'}."))


def delete_file(file_path: str, root: Path | str | None = None) -> WriteResult:
    """Delete one file. Directories are refused: use an explicit recursive flag elsewhere."""
    try:
        source = _open_source(root)
        rel, target = _target(source, file_path, must_exist=True)
        size = target.stat().st_size
        target.unlink()
        return WriteResult(rel, action="deleted", byte_size=size)
    except LLMScribeError as exc:
        return _failure(file_path, exc)
    except OSError as exc:
        return _failure(file_path, LLMScribeError("write_error", f"Could not delete '{file_path}': {exc.strerror or 'error'}."))

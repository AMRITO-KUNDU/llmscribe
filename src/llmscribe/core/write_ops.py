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

import codecs
import errno
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import LLMScribeError
from .file_ops import revision_of
from .file_reader import decode_text
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


def _encode_as(text: str, encoding: str, rel: str, original: bytes) -> bytes:
    """Encode in the file's own encoding, preserving any byte-order mark."""
    try:
        if encoding == "utf-16":
            if original.startswith(codecs.BOM_UTF16_BE):
                return codecs.BOM_UTF16_BE + text.encode("utf-16-be")
            return codecs.BOM_UTF16_LE + text.encode("utf-16-le")
        if encoding == "utf-8" and original.startswith(codecs.BOM_UTF8):
            return codecs.BOM_UTF8 + text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise LLMScribeError(
            "encoding_error", f"'{rel}' cannot be written as {encoding}: {exc.reason}."
        ) from None
    try:
        return text.encode(encoding)
    except UnicodeEncodeError as exc:
        raise LLMScribeError(
            "encoding_error",
            f"'{rel}' cannot be written as {encoding}: the text contains characters it "
            f"cannot represent ({exc.reason}). Pass encoding='utf-8' to convert the file.",
        ) from None


# Windows raises these when a path exceeds MAX_PATH without long-path support enabled.
_LONG_PATH_ERRNOS = {errno.ENAMETOOLONG}
_WINDOWS_LONG_PATH = 206


def _explain_oserror(exc: OSError, rel: str, doing: str) -> LLMScribeError:
    """Turn a filesystem errno into an error a caller can act on."""
    code = exc.errno
    winerror = getattr(exc, "winerror", None)

    if code in _LONG_PATH_ERRNOS or winerror == _WINDOWS_LONG_PATH:
        return LLMScribeError(
            "path_too_long",
            f"Path is too long to {doing} on this system: '{rel}'. Windows limits paths to "
            "260 characters unless long-path support is enabled.",
        )
    if code == errno.ENOSPC or winerror == 112:
        return LLMScribeError(
            "no_space",
            f"Not enough space on the device to {doing} '{rel}'. The original file was not changed.",
        )
    if code in {errno.EACCES, errno.EPERM, errno.EROFS} or winerror == 5:
        return LLMScribeError(
            "permission_denied",
            f"Permission denied trying to {doing} '{rel}'. The file or its directory may be "
            "read-only, or held open by another process.",
        )
    if code == errno.EXDEV:
        return LLMScribeError(
            "write_error",
            f"Cannot {doing} '{rel}': the temporary file landed on a different filesystem. "
            "This should not happen; please report it.",
        )
    if code == errno.EISDIR:
        return LLMScribeError("invalid_path", f"Path is a directory, not a file: '{rel}'.")
    return LLMScribeError(
        "write_error", f"Could not {doing} '{rel}': {exc.strerror or type(exc).__name__}."
    )


def _require_writable(target: Path, rel: str) -> None:
    """Refuse to overwrite a file the user has made read-only.

    On POSIX, replacing a file depends on write permission on the *directory*, not the
    file, so an atomic replace would happily overwrite a chmod 444 file. That is not what
    a person who made a file read-only expects.
    """
    if target.exists() and not os.access(target, os.W_OK):
        raise LLMScribeError(
            "permission_denied",
            f"'{rel}' is read-only. Change its permissions first, or write a different path.",
        )
    parent = target.parent
    if not os.access(parent, os.W_OK):
        raise LLMScribeError(
            "permission_denied",
            f"The directory containing '{rel}' is not writable.",
        )


def _atomic_write(target: Path, data: bytes, rel: str = "") -> None:
    """Write via a temporary file in the same directory, then replace.

    A crash mid-write leaves the original intact rather than a half-written file, which
    matters when an agent is rewriting source it cannot easily recover.

    The temporary file is created with ``mkstemp`` so two concurrent writers cannot pick
    the same name, and it lives in the target's own directory so the final ``os.replace``
    is a rename within one filesystem rather than a cross-device copy.
    """
    label = rel or target.name
    _require_writable(target, label)

    handle, temp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".llmscribe-tmp"
    )
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
    except OSError as exc:
        raise _explain_oserror(exc, label, "write") from None
    finally:
        temp.unlink(missing_ok=True)


def write_file(
    file_path: str,
    content: str,
    root: Path | str | None = None,
    *,
    overwrite: bool = True,
    encoding: str | None = None,
    expect_revision: str | None = None,
) -> WriteResult:
    """Create or replace a file.

    ``overwrite=False`` refuses to clobber an existing one. Replacing an existing file
    keeps its encoding and byte-order mark, so writing to a cp1252 source file does not
    silently convert it to UTF-8. Pass ``encoding`` to convert deliberately.
    """
    try:
        source = _open_source(root)
        rel, target = _target(source, file_path, must_exist=False)
        existed = target.exists()
        if existed and not overwrite:
            raise LLMScribeError("file_exists", f"File already exists: '{rel}'. Pass overwrite to replace it.")

        original = b""
        if existed:
            try:
                original = target.read_bytes()
            except OSError as exc:
                raise LLMScribeError(
                    "write_error", f"Could not read '{rel}' before replacing it: {exc.strerror or 'error'}."
                ) from exc

        if expect_revision is not None:
            current = revision_of(original) if existed else ""
            if current != expect_revision:
                raise LLMScribeError(
                    "conflict",
                    f"'{rel}' changed since it was read (expected revision "
                    f"{expect_revision}, found {current or 'no file'}). Read it again before "
                    "writing.",
                )

        if encoding is not None:
            target_encoding = encoding
        elif existed:
            try:
                target_encoding = decode_text(original, rel)[1]
            except LLMScribeError:
                # a binary or undecodable file being replaced with text: UTF-8 is the only
                # sensible choice, and it is what the caller implicitly asked for
                target_encoding = "utf-8"
        else:
            target_encoding = "utf-8"

        data = _encode_as(content, target_encoding, rel, original)
        if len(data) > MAX_FILE_SIZE:
            raise LLMScribeError(
                "file_too_large", f"Content exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'."
            )
        _atomic_write(target, data, rel)
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
    expect_revision: str | None = None,
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
        if expect_revision is not None and revision_of(original) != expect_revision:
            raise LLMScribeError(
                "conflict",
                f"'{rel}' changed since it was read (expected revision {expect_revision}, "
                f"found {revision_of(original)}). Read it again before editing.",
            )
        if len(original) > MAX_FILE_SIZE:
            raise LLMScribeError("file_too_large", f"File exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'.")
        # Decode with the same detector the read side uses, so an edit does not silently
        # re-encode the file. Editing one line of a cp1252 source file must not rewrite
        # every non-ASCII byte in it.
        text, encoding = decode_text(original, rel)
        found = text.count(old_text)
        if found == 0:
            raise LLMScribeError("no_match", f"old_text was not found in '{rel}'.")
        if found > 1 and not replace_all:
            raise LLMScribeError(
                "ambiguous_match",
                f"old_text appears {found} times in '{rel}'. Include more context, or pass replace_all.",
            )
        updated = text.replace(old_text, new_text) if replace_all else text.replace(old_text, new_text, 1)
        data = _encode_as(updated, encoding, rel, original)
        if len(data) > MAX_FILE_SIZE:
            raise LLMScribeError("file_too_large", f"Result exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'.")
        _atomic_write(target, data, rel)
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

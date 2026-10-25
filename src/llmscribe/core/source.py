"""Repository sources: one interface over a local project directory.

Every deterministic operation (map, overview, search, read, dependencies) is
written once against ``RepositorySource``. ``LocalRepository`` walks a
directory on disk; a new provider only has to implement ``scan``, ``info`` and
``read_bytes``.
"""

from __future__ import annotations

import os
import re
import stat
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote

from .errors import LLMScribeError
from .limits import MAX_FILE_SIZE, MAX_GITIGNORE_SIZE, MAX_REPOSITORY_FILES
from .tree_builder import IgnoreRules

_DRIVE_RE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True)
class Entry:
    """A file or directory inside a repository (posix path relative to its root)."""

    path: str
    size: int = 0
    is_dir: bool = False


@dataclass
class Scan:
    """Result of walking a repository once."""

    entries: list[Entry] = field(default_factory=list)
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def files(self) -> list[Entry]:
        return [e for e in self.entries if not e.is_dir]


def normalize_rel_path(raw: str) -> str:
    """Validate a user-supplied relative path and return it as a clean posix path.

    Rejects empty paths, NUL bytes, absolute paths (POSIX, Windows drive, UNC),
    and any ``..`` segment, including percent-encoded and backslash forms.
    """
    if raw is None or not str(raw).strip():
        raise LLMScribeError("invalid_argument", "A file path must be provided.")
    text = str(raw).strip()
    if "\x00" in text:
        raise LLMScribeError("invalid_path", "Path contains a NUL byte.")
    for variant in (text, unquote(text)):
        flat = variant.replace("\\", "/")
        if flat.startswith("/") or _DRIVE_RE.match(flat):
            raise LLMScribeError("invalid_path", f"Absolute paths are not allowed: '{text}'.")
        if ".." in flat.split("/"):
            raise LLMScribeError("invalid_path", f"Path escapes the repository root: '{text}'.")
    parts = [p for p in text.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        raise LLMScribeError("invalid_argument", "A file path must be provided.")
    return "/".join(parts)


class RepositorySource(ABC):
    """Read-only view of a repository."""

    kind = "local"
    name: str
    logical_path: str  # identifies the repository in output envelopes

    @abstractmethod
    def scan(self) -> Scan:
        """Return every non-ignored file and directory, sorted by path."""

    @abstractmethod
    def info(self, rel: str) -> Entry:
        """Return the entry for a normalized path or raise file_not_found/invalid_path."""

    @abstractmethod
    def read_bytes(self, rel: str) -> bytes:
        """Return the content of a regular file of at most ``MAX_FILE_SIZE`` bytes."""

    def text_files(self) -> list[Entry]:
        """Non-ignored files with a supported text extension, sorted by path."""
        from .file_reader import is_text_file

        return [e for e in self.scan().files if is_text_file(e.path)]


class LocalRepository(RepositorySource):
    """A directory on disk. Symlinks are never followed or listed."""

    kind = "local"

    def __init__(self, root: Path | str | None = None, ignore_patterns: Iterable[str] | None = None):
        base = Path(root) if root is not None else Path.cwd()
        try:
            resolved = base.resolve()
        except OSError as exc:
            raise LLMScribeError("invalid_path", f"Cannot resolve directory: {exc.strerror or 'error'}") from exc
        if not resolved.exists():
            raise LLMScribeError("invalid_path", f"Directory does not exist: '{resolved}'.")
        if not resolved.is_dir():
            raise LLMScribeError("invalid_path", f"Path is not a directory: '{resolved}'.")
        self.root = resolved
        self.name = resolved.name or resolved.as_posix()
        self.logical_path = resolved.as_posix()
        self._extra = list(ignore_patterns or [])
        self._scan: Scan | None = None

    def _read_gitignore(self, directory: str) -> str | None:
        path = self.root / directory / ".gitignore" if directory else self.root / ".gitignore"
        try:
            st = path.lstat()
            if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_GITIGNORE_SIZE:
                return None
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def scan(self) -> Scan:
        if self._scan is not None:
            return self._scan
        rules = IgnoreRules(self._read_gitignore, self._extra)
        scan = Scan()
        pending = [""]
        while pending:
            directory = pending.pop()
            try:
                with os.scandir(self.root / directory if directory else self.root) as it:
                    children = sorted(it, key=lambda e: e.name)
            except OSError:
                scan.warnings.append(f"Could not read directory: {directory or '.'}")
                continue
            for child in children:
                rel = f"{directory}/{child.name}" if directory else child.name
                try:
                    if child.is_symlink():
                        continue
                    is_dir = child.is_dir(follow_symlinks=False)
                    if rules.is_ignored(rel, is_dir):
                        continue
                    if len(scan.entries) >= MAX_REPOSITORY_FILES:
                        scan.truncated = True
                        break
                    if is_dir:
                        scan.entries.append(Entry(rel, 0, True))
                        pending.append(rel)
                    elif child.is_file(follow_symlinks=False):
                        scan.entries.append(Entry(rel, child.stat(follow_symlinks=False).st_size, False))
                except OSError:
                    scan.warnings.append(f"Could not stat: {rel}")
            if scan.truncated:
                scan.warnings.append(f"Scan stopped after {MAX_REPOSITORY_FILES:,} entries.")
                break
        scan.entries.sort(key=lambda e: e.path)
        scan.warnings.sort()
        self._scan = scan
        return scan

    def _checked_path(self, rel: str) -> Path:
        current = self.root
        for part in rel.split("/"):
            current = current / part
            try:
                if current.is_symlink():
                    raise LLMScribeError("invalid_path", f"Symlinks are not followed: '{rel}'.")
            except OSError as exc:
                raise LLMScribeError("read_error", f"Cannot access '{rel}': {exc.strerror or 'error'}.") from exc
        try:
            current.resolve().relative_to(self.root)
        except (ValueError, OSError) as exc:
            raise LLMScribeError("invalid_path", f"Path escapes the repository root: '{rel}'.") from exc
        return current

    def info(self, rel: str) -> Entry:
        target = self._checked_path(rel)
        try:
            st = target.lstat()
        except FileNotFoundError as exc:
            raise LLMScribeError("file_not_found", f"File does not exist: '{rel}'.") from exc
        except NotADirectoryError as exc:
            raise LLMScribeError("file_not_found", f"File does not exist: '{rel}'.") from exc
        except OSError as exc:
            raise LLMScribeError("read_error", f"Cannot access '{rel}': {exc.strerror or 'error'}.") from exc
        if stat.S_ISDIR(st.st_mode):
            raise LLMScribeError("invalid_path", f"Path is a directory, not a file: '{rel}'.")
        if not stat.S_ISREG(st.st_mode):
            raise LLMScribeError("invalid_path", f"Path is not a regular file: '{rel}'.")
        return Entry(rel, st.st_size, False)

    def read_bytes(self, rel: str) -> bytes:
        target = self._checked_path(rel)
        try:
            with open(target, "rb") as handle:
                data = handle.read(MAX_FILE_SIZE + 1)
        except PermissionError as exc:
            raise LLMScribeError("read_error", f"Permission denied reading '{rel}'.") from exc
        except OSError as exc:
            raise LLMScribeError("read_error", f"Cannot read '{rel}': {exc.strerror or 'error'}.") from exc
        if len(data) > MAX_FILE_SIZE:
            raise LLMScribeError("file_too_large", f"File exceeds {MAX_FILE_SIZE:,} bytes: '{rel}'.")
        return data

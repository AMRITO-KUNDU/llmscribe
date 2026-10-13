"""Git status and diff for a local repository (safe subprocess use only)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import LLMScribeError
from .limits import GIT_TIMEOUT, MAX_DIFF_CHARS

_REF_RE = re.compile(r"^[\w][\w./~^@{}:+\-]*$")
_ENV_PASSTHROUGH = ("PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "TMPDIR", "TEMP", "TMP", "LANG")
_STDERR_LIMIT = 4096


@dataclass
class GitStatusEntry:
    """One ``git status`` entry. ``status`` is the two-letter porcelain code."""

    status: str
    file_path: str
    original_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"status": self.status, "file_path": self.file_path}
        if self.original_path:
            data["original_path"] = self.original_path
        return data


@dataclass
class DiffResult:
    """Working-tree status and unified diff."""

    root_path: str
    staged: bool = False
    commit: str | None = None
    changed_files: list[str] = field(default_factory=list)
    status_lines: list[str] = field(default_factory=list)
    changes: list[GitStatusEntry] = field(default_factory=list)
    diff: str = ""
    truncated: bool = False
    truncation_limit: int = MAX_DIFF_CHARS
    character_count: int = 0
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "staged": self.staged,
            "commit": self.commit,
            "changed_files": self.changed_files,
            "status_lines": self.status_lines,
            "changes": [c.to_dict() for c in self.changes],
            "diff": self.diff,
            "truncated": self.truncated,
            "truncation_limit": self.truncation_limit,
            "character_count": self.character_count,
            "note": self.note,
        }


def _git_env() -> dict[str, str]:
    env = {k: os.environ[k] for k in _ENV_PASSTHROUGH if k in os.environ}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C.UTF-8"})
    return env


def _run_git(git: str, args: list[str], cwd: Path, max_bytes: int) -> tuple[int, bytes, bool, str]:
    """Run git with an argument list (never a shell), a timeout and bounded output.

    Returns ``(returncode, stdout_bytes, stdout_truncated, stderr_text)``.
    """
    try:
        proc = subprocess.Popen(
            [git, "-c", "core.fsmonitor=false", "-c", "core.quotepath=false", *args],
            cwd=cwd,
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except OSError as exc:
        raise LLMScribeError("git_unavailable", f"Could not run git: {exc.strerror or 'error'}.") from exc

    timed_out = threading.Event()

    def _kill() -> None:
        timed_out.set()
        proc.kill()

    timer = threading.Timer(GIT_TIMEOUT, _kill)
    timer.start()
    try:
        assert proc.stdout is not None and proc.stderr is not None
        data = proc.stdout.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        if truncated:
            data = data[:max_bytes]
            proc.kill()
        stderr = proc.stderr.read(_STDERR_LIMIT)
        proc.wait()
    finally:
        timer.cancel()
        for stream in (proc.stdout, proc.stderr):
            if stream:
                stream.close()
    if timed_out.is_set():
        raise LLMScribeError("git_unavailable", f"git timed out after {GIT_TIMEOUT} seconds.")
    return proc.returncode, data, truncated, stderr.decode("utf-8", errors="replace")


def parse_status_z(raw: bytes) -> list[GitStatusEntry]:
    """Parse ``git status --porcelain=v1 -z`` output (handles renames and odd file names)."""
    parts = raw.decode("utf-8", errors="replace").split("\x00")
    entries: list[GitStatusEntry] = []
    index = 0
    while index < len(parts):
        item = parts[index]
        index += 1
        if len(item) < 4:
            continue
        status, path = item[:2], item[3:]
        original = None
        if "R" in status or "C" in status:
            original = parts[index] if index < len(parts) else None
            index += 1
        entries.append(GitStatusEntry(status, path, original))
    return entries


def validate_ref(ref: str) -> str:
    """Return ``ref`` stripped, or raise ``invalid_argument`` if it could be an option or is malformed."""
    cleaned = ref.strip()
    if not cleaned or len(cleaned) > 255 or not _REF_RE.match(cleaned) or ".." in cleaned:
        raise LLMScribeError("invalid_argument", f"Invalid commit reference: '{ref}'.")
    return cleaned


def get_git_diff(
    root: Path | None = None,
    staged: bool = False,
    commit: str | None = None,
    max_diff_chars: int = MAX_DIFF_CHARS,
) -> DiffResult:
    """Return git status and a unified diff for the repository containing ``root``.

    ``commit`` compares the working tree to that revision; otherwise ``staged``
    selects staged changes only; otherwise the diff is against ``HEAD`` (or the
    index and working tree when the repository has no commits yet).

    Raises ``LLMScribeError`` with code ``invalid_path``, ``invalid_argument``,
    ``git_unavailable`` or ``not_a_repository``.
    """
    base = Path(root) if root is not None else Path.cwd()
    try:
        root = base.resolve()
    except OSError as exc:
        raise LLMScribeError("invalid_path", "Cannot resolve directory.") from exc
    if not root.is_dir():
        raise LLMScribeError("invalid_path", f"Directory does not exist: '{root}'.")
    if commit is not None and staged and commit.strip():
        raise LLMScribeError("invalid_argument", "Use either 'staged' or 'commit', not both.")

    git = shutil.which("git")
    if git is None:
        raise LLMScribeError("git_unavailable", "The git executable was not found on PATH.")

    code, out, _, err = _run_git(git, ["rev-parse", "--is-inside-work-tree"], root, 1024)
    if code != 0 or out.strip() != b"true":
        hint = " (git refused to open it: ownership check)" if "dubious ownership" in err else ""
        raise LLMScribeError("not_a_repository", f"'{root}' is not a git repository{hint}.")

    commit_clean = validate_ref(commit) if commit and commit.strip() else None
    if commit_clean:
        code, _, _, _ = _run_git(git, ["rev-parse", "--verify", "--quiet", f"{commit_clean}^{{commit}}"], root, 1024)
        if code != 0:
            raise LLMScribeError("invalid_argument", f"Unknown commit reference: '{commit_clean}'.")

    head_code, _, _, _ = _run_git(git, ["rev-parse", "--verify", "--quiet", "HEAD^{commit}"], root, 1024)
    has_head = head_code == 0

    diff_base = ["diff", "--no-ext-diff", "--no-textconv", "--no-color"]
    note = ""
    max_bytes = max_diff_chars * 4 + 1024
    if commit_clean:
        runs = [[*diff_base, commit_clean, "--"]]
    elif staged:
        runs = [[*diff_base, "--cached", "--"]]
    elif has_head:
        runs = [[*diff_base, "HEAD", "--"]]
    else:
        runs = [[*diff_base, "--cached", "--"], [*diff_base, "--"]]
        note = "Repository has no commits yet; showing staged then unstaged changes."

    chunks: list[bytes] = []
    byte_truncated = False
    for args in runs:
        code, out, was_truncated, err = _run_git(git, args, root, max_bytes)
        if code not in (0, 1) and not was_truncated:
            raise LLMScribeError("git_unavailable", f"git diff failed: {err.strip()[:200] or 'unknown error'}")
        chunks.append(out)
        byte_truncated = byte_truncated or was_truncated

    code, out, _, err = _run_git(git, ["status", "--porcelain=v1", "-z", "--untracked-files=normal"], root, 4_000_000)
    if code != 0:
        raise LLMScribeError("git_unavailable", f"git status failed: {err.strip()[:200] or 'unknown error'}")
    changes = parse_status_z(out)

    diff_text = b"".join(chunks).decode("utf-8", errors="replace")
    truncated = byte_truncated or len(diff_text) > max_diff_chars
    if truncated:
        diff_text = diff_text[:max_diff_chars] + f"\n\n[Diff truncated after {max_diff_chars:,} characters]"

    changed: list[str] = []
    for change in changes:
        if change.file_path not in changed:
            changed.append(change.file_path)
    status_lines = [f"{c.status} {c.original_path + ' -> ' if c.original_path else ''}{c.file_path}" for c in changes]

    return DiffResult(
        root_path=root.as_posix(),
        staged=staged,
        commit=commit_clean,
        changed_files=changed,
        status_lines=status_lines,
        changes=changes,
        diff=diff_text,
        truncated=truncated,
        truncation_limit=max_diff_chars,
        character_count=len(diff_text),
        note=note,
    )

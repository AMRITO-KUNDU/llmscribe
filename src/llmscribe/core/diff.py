"""Core diff functionality for LLMScribe."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GitStatusEntry:
    """A single git status entry."""
    status: str  # "A" (added), "M" (modified), "D" (deleted), etc.
    file_path: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "file_path": self.file_path,
        }


@dataclass
class DiffResult:
    """Complete diff result."""
    root_path: str
    staged: bool = False
    commit: str | None = None
    changed_files: list[str] = field(default_factory=list)
    status_lines: list[str] = field(default_factory=list)
    diff: str = ""
    truncated: bool = False
    truncation_limit: int = 200000
    character_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "root_path": self.root_path,
            "staged": self.staged,
            "commit": self.commit,
            "changed_files": self.changed_files,
            "status_lines": self.status_lines,
            "diff": self.diff,
            "truncated": self.truncated,
            "character_count": self.character_count,
        }
        if self.truncation_limit:
            result["truncation_limit"] = self.truncation_limit
        return result


def parse_porcelain_path(line: str) -> str:
    """Extract clean relative file path from git status --porcelain line."""
    path_part = line[3:].strip() if len(line) > 3 else line.strip()
    if " -> " in path_part:
        path_part = path_part.split(" -> ")[-1].strip()
    return path_part.strip('"')


def get_git_diff(
    root: Path | None = None,
    staged: bool = False,
    commit: str | None = None,
    max_diff_chars: int = 200_000,
) -> DiffResult:
    """Get git diff and status for a project.
    
    Args:
        root: Project root directory (defaults to current working directory)
        staged: Whether to show staged changes only
        commit: Optional commit reference for comparison
        max_diff_chars: Maximum characters for diff output
        
    Returns:
        DiffResult with git status and diff information
    """
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    
    # Check if git is available and root is inside a git work tree
    try:
        check_git = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if check_git.returncode != 0:
            raise RuntimeError(f"Directory '{root}' is not a git repository.")
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"Git executable is unavailable or failed: {exc}")
    
    # Validate commit parameter if provided
    if commit is not None and commit.strip():
        commit_clean = commit.strip()
        if not all(c.isalnum() or c in "_\-./~^@" for c in commit_clean):
            raise ValueError(f"Invalid commit ref format: '{commit}'")
    
    # Determine diff command
    if commit is not None and commit.strip():
        diff_cmd = ["git", "diff", commit.strip()]
    elif staged:
        diff_cmd = ["git", "diff", "--cached"]
    else:
        diff_cmd = ["git", "diff", "HEAD"]
    
    try:
        diff_proc = subprocess.run(
            diff_cmd,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git operations timed out")
    except OSError as exc:
        raise RuntimeError(f"Git operations failed: {exc}")
    
    raw_diff = diff_proc.stdout or ""
    raw_status = status_proc.stdout or ""
    
    # Parse status lines
    changed_files = []
    status_lines = []
    for line in raw_status.splitlines():
        if line.strip():
            status_lines.append(line)
            clean_p = parse_porcelain_path(line)
            if clean_p and clean_p not in changed_files:
                changed_files.append(clean_p)
    
    # Truncate diff if needed
    truncated = False
    diff_text = raw_diff
    if len(diff_text) > max_diff_chars:
        diff_text = diff_text[:max_diff_chars] + f"\n\n[Diff truncated after {max_diff_chars:,} characters]"
        truncated = True
    
    return DiffResult(
        root_path=root.as_posix(),
        staged=staged,
        commit=commit.strip() if commit else None,
        changed_files=changed_files,
        status_lines=status_lines,
        diff=diff_text,
        truncated=truncated,
        truncation_limit=max_diff_chars,
        character_count=len(diff_text),
    )
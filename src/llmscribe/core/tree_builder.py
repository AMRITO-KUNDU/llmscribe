"""Build directory trees and apply Git-style ignore rules."""

from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Iterable

DEFAULT_IGNORE = {
    ".git", ".svn", ".hg", "node_modules", "vendor", "packages", "venv",
    "__pycache__", ".eggs", "*.egg-info", "dist", "build", "target", "out",
    "bin", "obj", ".idea", ".vscode", ".vs", ".DS_Store", "Thumbs.db",
    "desktop.ini", "*.log", "logs", "tmp", "temp", ".tmp", ".cache",
    ".coverage", "coverage", ".nyc_output", ".env", ".env.*", "secrets",
}


def load_gitignore(root: Path) -> list[str]:
    """Load ordered, non-comment patterns from ``root/.gitignore``."""
    gitignore = root / ".gitignore"
    if not gitignore.exists():
        return []
    try:
        return [line.strip() for line in gitignore.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
    except OSError:
        return []


class IgnoreMatcher:
    """Dependency-free matcher for common Git ignore syntax."""

    def __init__(self, root: Path, patterns: Iterable[str]):
        self.root = root.resolve()
        self.patterns = [p for p in patterns if p and not p.startswith("#")]

    def is_ignored(self, path: Path) -> bool:
        try:
            relative = path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            relative = path.as_posix().lstrip("/")
        ignored = False
        for raw_pattern in self.patterns:
            pattern = raw_pattern.strip()
            negated = pattern.startswith("!") and not pattern.startswith("\\!")
            if negated:
                pattern = pattern[1:]
            pattern = pattern.replace("\\ ", " ").replace("\\#", "#")
            pattern = pattern.rstrip("/")
            anchored = pattern.startswith("/")
            pattern = pattern.lstrip("/")
            if self._matches(relative, pattern, anchored):
                ignored = not negated
        return ignored

    @staticmethod
    def _matches(relative: str, pattern: str, anchored: bool) -> bool:
        if not pattern:
            return False
        candidates = [relative] if anchored or "/" in pattern else [relative, *relative.split("/")]
        return any(fnmatch.fnmatchcase(candidate, pattern) for candidate in candidates)


def should_ignore(path: Path, ignore_patterns: Iterable[str], root: Path | None = None) -> bool:
    """Return whether ``path`` matches the supplied ignore rules."""
    base = root or path.parent
    return IgnoreMatcher(base, ignore_patterns).is_ignored(path)


def generate_tree(root: Path, ignore_patterns: Iterable[str]) -> str:
    """Generate a visual tree while skipping ignored or unreadable paths."""
    root = root.resolve()
    matcher = IgnoreMatcher(root, ignore_patterns)
    lines = [f"{root.name}/"]

    def walk(directory: Path, prefix: str = "") -> None:
        try:
            items = sorted(directory.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        except OSError as exc:
            lines.append(f"{prefix}└── [unreadable: {exc}]")
            return
        visible_items = [item for item in items if not matcher.is_ignored(item)]
        for index, item in enumerate(visible_items):
            connector = "└── " if index == len(visible_items) - 1 else "├── "
            lines.append(prefix + connector + item.name)
            if item.is_dir():
                extension = "    " if index == len(visible_items) - 1 else "│   "
                walk(item, prefix + extension)

    walk(root)
    return "\n".join(lines)

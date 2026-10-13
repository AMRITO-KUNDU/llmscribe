"""Ignore rules (real gitignore semantics via ``pathspec``) and tree rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

import pathspec

from .limits import MAX_GITIGNORE_SIZE

DEFAULT_IGNORE = {
    ".git", ".svn", ".hg", "node_modules", "vendor", "packages", "venv",
    "__pycache__", ".eggs", "*.egg-info", "dist", "build", "target", "out",
    "bin", "obj", ".idea", ".vscode", ".vs", ".DS_Store", "Thumbs.db",
    "desktop.ini", "*.log", "logs", "tmp", "temp", ".tmp", ".cache",
    ".coverage", "coverage", ".nyc_output", ".env", ".env.*", "secrets",
}


def _spec(lines: Iterable[str]) -> pathspec.GitIgnoreSpec:
    return pathspec.GitIgnoreSpec.from_lines(lines)


def parse_gitignore_text(text: str) -> list[str]:
    """Return the pattern lines of a ``.gitignore`` file (comments/blank kept out)."""
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def load_gitignore(root: Path) -> list[str]:
    """Load the pattern lines of ``root/.gitignore`` (empty if absent or unreadable)."""
    gitignore = root / ".gitignore"
    try:
        if gitignore.is_symlink() or not gitignore.is_file() or gitignore.stat().st_size > MAX_GITIGNORE_SIZE:
            return []
        return parse_gitignore_text(gitignore.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


class IgnoreRules:
    """Git-compatible ignore evaluation with nested ``.gitignore`` support.

    Layers, lowest to highest precedence: the default ignores, the root
    ``.gitignore``, each nested ``.gitignore`` (patterns relative to its own
    directory), then caller-supplied extra patterns. A path is ignored when it,
    or any parent directory, is ignored; a file cannot be re-included once a
    parent directory is excluded (as in Git).
    """

    def __init__(
        self,
        read_gitignore: Callable[[str], str | None],
        extra_patterns: Iterable[str] = (),
        use_defaults: bool = True,
    ) -> None:
        self._read = read_gitignore
        self._defaults = _spec(sorted(DEFAULT_IGNORE)) if use_defaults else None
        extra = [p for p in extra_patterns if p and p.strip() and not p.lstrip().startswith("#")]
        self._extra = _spec(extra) if extra else None
        self._dir_specs: dict[str, pathspec.GitIgnoreSpec | None] = {}
        self._dir_ignored: dict[str, bool] = {}

    def _spec_for_dir(self, directory: str) -> pathspec.GitIgnoreSpec | None:
        if directory not in self._dir_specs:
            text = self._read(directory)
            lines = parse_gitignore_text(text) if text else []
            self._dir_specs[directory] = _spec(lines) if lines else None
        return self._dir_specs[directory]

    def _decide(self, spec: pathspec.GitIgnoreSpec | None, candidate: str, current: bool) -> bool:
        if spec is None:
            return current
        include = spec.check_file(candidate).include
        return current if include is None else bool(include)

    def _match(self, rel: str, is_dir: bool) -> bool:
        suffix = "/" if is_dir else ""
        ignored = self._decide(self._defaults, rel + suffix, False)
        parts = rel.split("/")
        for depth in range(len(parts)):
            base = "/".join(parts[:depth])
            sub = "/".join(parts[depth:])
            ignored = self._decide(self._spec_for_dir(base), sub + suffix, ignored)
        return self._decide(self._extra, rel + suffix, ignored)

    def is_dir_ignored(self, rel: str) -> bool:
        if rel not in self._dir_ignored:
            parent = rel.rpartition("/")[0]
            self._dir_ignored[rel] = (bool(parent) and self.is_dir_ignored(parent)) or self._match(rel, True)
        return self._dir_ignored[rel]

    def is_ignored(self, rel: str, is_dir: bool = False) -> bool:
        """Return whether the posix-style relative path ``rel`` is ignored."""
        rel = rel.strip("/")
        if not rel:
            return False
        parent = rel.rpartition("/")[0]
        if parent and self.is_dir_ignored(parent):
            return True
        return self.is_dir_ignored(rel) if is_dir else self._match(rel, False)


class IgnoreMatcher:
    """Match paths against an explicit list of gitignore patterns under ``root``."""

    def __init__(self, root: Path, patterns: Iterable[str]):
        self.root = root.resolve()
        self.patterns = [p for p in patterns if p and not p.startswith("#")]
        self._rules = IgnoreRules(lambda _dir: None, self.patterns, use_defaults=False)

    def is_ignored(self, path: Path) -> bool:
        try:
            relative = path.resolve().relative_to(self.root).as_posix()
        except (ValueError, OSError):
            relative = path.as_posix().lstrip("/")
        return self._rules.is_ignored(relative, is_dir=path.is_dir())


def should_ignore(path: Path, ignore_patterns: Iterable[str], root: Path | None = None) -> bool:
    """Return whether ``path`` matches the supplied ignore patterns."""
    return IgnoreMatcher(root or path.parent, ignore_patterns).is_ignored(path)


def render_tree(name: str, entries: Iterable[tuple[str, bool]]) -> str:
    """Render ``(relative_posix_path, is_dir)`` entries as a deterministic tree."""
    root: dict = {}
    for rel, is_dir in entries:
        node = root
        parts = rel.split("/")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        if is_dir:
            node.setdefault(parts[-1], {})
        else:
            node[parts[-1]] = None

    lines = [f"{name}/"]

    def walk(node: dict, prefix: str) -> None:
        keys = sorted(node, key=lambda k: (node[k] is None, k.lower(), k))
        for index, key in enumerate(keys):
            last = index == len(keys) - 1
            lines.append(prefix + ("└── " if last else "├── ") + key)
            if node[key] is not None:
                walk(node[key], prefix + ("    " if last else "│   "))

    walk(root, "")
    return "\n".join(lines)


def generate_tree(root: Path, ignore_patterns: Iterable[str]) -> str:
    """Render the tree of ``root`` applying default ignores, ``.gitignore`` and ``ignore_patterns``."""
    from .source import LocalRepository

    source = LocalRepository(root, ignore_patterns=list(ignore_patterns))
    scan = source.scan()
    return render_tree(source.name, ((e.path, e.is_dir) for e in scan.entries))

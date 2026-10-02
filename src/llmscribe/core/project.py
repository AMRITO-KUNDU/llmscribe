"""Core project operations for LLMScribe."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .file_reader import is_text_file, TEXT_FILE_EXTENSIONS
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, load_gitignore, generate_tree


@dataclass
class ProjectMapResult:
    """Result of project map operation."""
    root_path: str
    tree: str
    files: list[str] = field(default_factory=list)
    file_count: int = 0
    character_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "tree": self.tree,
            "files": self.files,
            "file_count": self.file_count,
            "character_count": self.character_count,
        }


@dataclass
class ProjectOverviewResult:
    """Result of project overview operation."""
    root_path: str
    tree: str
    files: list[dict[str, str]] = field(default_factory=list)
    file_count: int = 0
    character_count: int = 0
    truncated: bool = False
    truncation_note: str = ""
    truncation_limit: int = 400_000
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "root_path": self.root_path,
            "tree": self.tree,
            "files": self.files,
            "file_count": self.file_count,
            "character_count": self.character_count,
        }
        if self.truncated:
            result["truncated"] = True
            result["truncation_note"] = self.truncation_note
            result["truncation_limit"] = self.truncation_limit
        return result


def project_map(
    root: Path | None = None,
    ignore_patterns: list[str] | None = None,
) -> ProjectMapResult:
    """Generate a directory tree for a project.
    
    Args:
        root: Project root directory (defaults to current working directory)
        ignore_patterns: Additional ignore patterns beyond defaults
        
    Returns:
        ProjectMapResult with tree structure and file list
    """
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    
    # Build ignore patterns
    if ignore_patterns is None:
        ignore_patterns = []
    full_ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root), *ignore_patterns]
    matcher = IgnoreMatcher(root, full_ignore_patterns)
    
    tree_str = generate_tree(root, full_ignore_patterns)
    
    files = []
    for file_path in sorted(root.rglob("*")):
        if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
            continue
        try:
            rel_path = file_path.relative_to(root).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()
        files.append(rel_path)
    
    character_count = len(tree_str)
    
    return ProjectMapResult(
        root_path=root.as_posix(),
        tree=tree_str,
        files=files,
        file_count=len(files),
        character_count=character_count,
    )


def project_overview(
    root: Path | None = None,
    ignore_patterns: list[str] | None = None,
    max_content_chars: int = 400_000,
) -> ProjectOverviewResult:
    """Generate a full project overview with tree and file contents.
    
    Args:
        root: Project root directory (defaults to current working directory)
        ignore_patterns: Additional ignore patterns beyond defaults
        max_content_chars: Maximum total characters to return
        
    Returns:
        ProjectOverviewResult with tree and file contents
    """
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    
    # Build ignore patterns
    if ignore_patterns is None:
        ignore_patterns = []
    full_ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root), *ignore_patterns]
    matcher = IgnoreMatcher(root, full_ignore_patterns)
    
    tree_str = generate_tree(root, full_ignore_patterns)
    
    files_json: list[dict[str, str]] = []
    total_chars = len(tree_str)
    truncated = False
    truncation_note = ""
    
    for file_path in sorted(root.rglob("*")):
        if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
            continue

        try:
            rel_path = file_path.relative_to(root).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = f"[Error reading file]"

        content_len = len(content)

        if total_chars + content_len > max_content_chars:
            remaining_budget = max(0, max_content_chars - total_chars)
            truncated_content = content[:remaining_budget] + "\n[Content truncated]"
            files_json.append({"path": rel_path, "content": truncated_content})
            total_chars += len(truncated_content)
            truncated = True
            truncation_note = f"Content output capped at {max_content_chars:,} characters."
            break

        files_json.append({"path": rel_path, "content": content})
        total_chars += content_len

    return ProjectOverviewResult(
        root_path=root.as_posix(),
        tree=tree_str,
        files=files_json,
        file_count=len(files_json),
        character_count=total_chars,
        truncated=truncated,
        truncation_note=truncation_note,
        truncation_limit=max_content_chars,
    )


def list_files(
    root: Path | None = None,
    extension: str | None = None,
    ignore_patterns: list[str] | None = None,
) -> list[str]:
    """List all text files in a project, optionally filtered by extension.
    
    Args:
        root: Project root directory (defaults to current working directory)
        extension: Optional extension filter (e.g., ".py", "py")
        ignore_patterns: Additional ignore patterns beyond defaults
        
    Returns:
        List of file paths
    """
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    
    # Build ignore patterns
    if ignore_patterns is None:
        ignore_patterns = []
    full_ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root), *ignore_patterns]
    matcher = IgnoreMatcher(root, full_ignore_patterns)
    
    # Prepare extension filter
    ext_filter = None
    if extension and extension.strip():
        ext = extension.strip().lower()
        ext_filter = ext if ext.startswith(".") else f".{ext}"
    
    file_list = []
    for file_path in sorted(root.rglob("*")):
        if file_path.is_dir() or matcher.is_ignored(file_path) or not is_text_file(file_path):
            continue

        if ext_filter and file_path.suffix.lower() != ext_filter:
            continue

        try:
            rel_path = file_path.relative_to(root).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()

        file_list.append(rel_path)
    
    return file_list
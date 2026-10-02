"""Core search functionality for LLMScribe."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .file_reader import is_text_file
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, load_gitignore


@dataclass
class SearchMatch:
    """A single search match with structured information."""
    file_path: str
    line_number: int
    line_content: str
    match_type: str = "content"  # "content" or "filename"
    matched_text: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "line_content": self.line_content,
            "match_type": self.match_type,
            "matched_text": self.matched_text,
        }


@dataclass 
class SearchResult:
    """Complete search result with metadata."""
    query: str
    root_path: str
    matches: list[SearchMatch] = field(default_factory=list)
    file_count: int = 0
    match_count: int = 0
    truncated: bool = False
    truncation_limit: int = 1000
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "root_path": self.root_path,
            "matches": [m.to_dict() for m in self.matches],
            "file_count": self.file_count,
            "match_count": self.match_count,
            "truncated": self.truncated,
            "truncation_limit": self.truncation_limit,
        }


def search_project(
    query: str, 
    root: Path | None = None,
    max_results: int = 1000,
    ignore_patterns: list[str] | None = None,
) -> SearchResult:
    """Search for a query in project files.
    
    Args:
        query: Search query string
        root: Project root directory (defaults to current working directory)
        max_results: Maximum number of matches to return
        ignore_patterns: Additional ignore patterns beyond defaults
        
    Returns:
        SearchResult with structured matches
    """
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty")
    
    query_lower = query.lower().strip()
    
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
    
    result = SearchResult(
        query=query,
        root_path=root.as_posix(),
        truncation_limit=max_results,
    )
    
    # Track files we've already processed for deduplication
    processed_files = set()
    
    # First, find files with matching names
    for file_path in sorted(root.rglob("*")):
        if result.match_count >= max_results:
            result.truncated = True
            break
            
        if file_path.is_dir() or matcher.is_ignored(file_path):
            continue
            
        if not is_text_file(file_path):
            continue
            
        try:
            rel_path = file_path.relative_to(root).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()
        
        if rel_path in processed_files:
            continue
        
        # Check filename match
        if query_lower in rel_path.lower():
            match = SearchMatch(
                file_path=rel_path,
                line_number=0,
                line_content="",
                match_type="filename",
                matched_text=rel_path,
            )
            result.matches.append(match)
            result.match_count += 1
            processed_files.add(rel_path)
            result.file_count += 1
    
    # Then search content for each file
    for file_path in sorted(root.rglob("*")):
        if result.match_count >= max_results:
            result.truncated = True
            break
            
        if file_path.is_dir() or matcher.is_ignored(file_path):
            continue
            
        if not is_text_file(file_path):
            continue
            
        try:
            rel_path = file_path.relative_to(root).as_posix()
        except ValueError:
            rel_path = file_path.as_posix()
        
        if rel_path in processed_files:
            # We already have a filename match for this file
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            
            file_has_matches = False
            for line_idx, line in enumerate(lines, start=1):
                if result.match_count >= max_results:
                    result.truncated = True
                    break
                    
                if query_lower in line.lower():
                    # Extract the actual matched text
                    matched_text = _extract_matched_text(line, query_lower)
                    
                    match = SearchMatch(
                        file_path=rel_path,
                        line_number=line_idx,
                        line_content=line.rstrip(),
                        match_type="content",
                        matched_text=matched_text,
                    )
                    result.matches.append(match)
                    result.match_count += 1
                    file_has_matches = True
            
            if file_has_matches:
                processed_files.add(rel_path)
                result.file_count += 1
                
        except OSError:
            # Skip files we can't read
            continue
    
    return result


def _extract_matched_text(line: str, query: str) -> str:
    """Extract the actual matched text from a line using the query."""
    # Try to find the exact case-sensitive match first
    if query in line:
        return query
    
    # Fall back to case-insensitive
    query_lower = query.lower()
    line_lower = line.lower()
    
    # Find the first occurrence
    start = line_lower.find(query_lower)
    if start != -1:
        return line[start:start + len(query)]
    
    return query


def search_project_simple(
    query: str,
    root: Path | None = None,
    max_results: int = 1000,
    ignore_patterns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Simplified search that returns a list of match dictionaries.
    
    This is a convenience function for compatibility.
    """
    result = search_project(query, root, max_results, ignore_patterns)
    return [m.to_dict() for m in result.matches]
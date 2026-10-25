"""Core LLMScribe functionality: deterministic repository data.

Everything here works on a ``RepositorySource`` (a local directory or an
in-memory snapshot) and returns plain dataclasses with ``to_dict()``.
"""

from . import limits
from .dependencies import (
    Dependency,
    DependencyResult,
    FileDependencies,
    analyze_dependencies,
    analyze_source_dependencies,
)
from .diff import DiffResult, GitStatusEntry, get_git_diff
from .errors import ERROR_CODES, LLMScribeError
from .file_ops import (
    FileReadResult,
    ReadManyResult,
    read_file,
    read_files,
    read_from_source,
    read_many_from_source,
)
from .file_reader import TEXT_FILE_EXTENSIONS, decode_text, extract_contents, is_text_file
from .project import (
    ProjectMapResult,
    ProjectOverviewResult,
    list_files,
    map_source,
    overview_source,
    project_map,
    project_overview,
)
from .search import SearchMatch, SearchResult, search_project, search_project_simple, search_source
from .source import Entry, LocalRepository, RepositorySource, Scan, normalize_rel_path
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, IgnoreRules, generate_tree, load_gitignore, should_ignore

__all__ = [
    "DEFAULT_IGNORE",
    "ERROR_CODES",
    "TEXT_FILE_EXTENSIONS",
    "Dependency",
    "DependencyResult",
    "DiffResult",
    "Entry",
    "FileDependencies",
    "FileReadResult",
    "GitStatusEntry",
    "IgnoreMatcher",
    "IgnoreRules",
    "LLMScribeError",
    "LocalRepository",
    "ProjectMapResult",
    "ProjectOverviewResult",
    "ReadManyResult",
    "RepositorySource",
    "Scan",
    "SearchMatch",
    "SearchResult",
    "analyze_dependencies",
    "analyze_source_dependencies",
    "decode_text",
    "extract_contents",
    "generate_tree",
    "get_git_diff",
    "is_text_file",
    "limits",
    "list_files",
    "load_gitignore",
    "map_source",
    "normalize_rel_path",
    "overview_source",
    "project_map",
    "project_overview",
    "read_file",
    "read_files",
    "read_from_source",
    "read_many_from_source",
    "search_project",
    "search_project_simple",
    "search_source",
    "should_ignore",
]

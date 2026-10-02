"""Core LLMScribe functionality."""

from .diff import DiffResult, GitStatusEntry, get_git_diff
from .dependencies import (
    Dependency,
    DependencyResult,
    FileDependencies,
    DependencyProvider,
    BasicDependencyProvider,
    CodeGraphProvider,
    set_dependency_provider,
    get_dependency_provider,
    analyze_dependencies,
)
from .file_ops import FileReadResult, ReadManyResult, read_file, read_files
from .file_reader import TEXT_FILE_EXTENSIONS, extract_contents, is_text_file
from .project import ProjectMapResult, ProjectOverviewResult, project_map, project_overview, list_files
from .search import SearchMatch, SearchResult, search_project, search_project_simple
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, generate_tree, load_gitignore, should_ignore
from .writer import build_project_summary, run

__all__ = [
    # Tree building
    "DEFAULT_IGNORE",
    "IgnoreMatcher",
    "generate_tree",
    "load_gitignore",
    "should_ignore",
    
    # File operations
    "TEXT_FILE_EXTENSIONS",
    "extract_contents",
    "is_text_file",
    "FileReadResult",
    "ReadManyResult",
    "read_file",
    "read_files",
    
    # Search
    "SearchMatch",
    "SearchResult", 
    "search_project",
    "search_project_simple",
    
    # Project
    "ProjectMapResult",
    "ProjectOverviewResult",
    "project_map",
    "project_overview", 
    "list_files",
    
    # Dependencies
    "Dependency",
    "DependencyResult",
    "FileDependencies",
    "DependencyProvider",
    "BasicDependencyProvider",
    "CodeGraphProvider", 
    "set_dependency_provider",
    "get_dependency_provider",
    "analyze_dependencies",
    
    # Diff
    "DiffResult",
    "GitStatusEntry",
    "get_git_diff",
    
    # Writer (legacy)
    "build_project_summary",
    "run",
]
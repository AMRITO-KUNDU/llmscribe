"""Core LLMScribe functionality."""

from .file_reader import TEXT_FILE_EXTENSIONS, extract_contents
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, generate_tree, load_gitignore, should_ignore
from .writer import build_project_summary, run

__all__ = [
    "DEFAULT_IGNORE",
    "IgnoreMatcher",
    "TEXT_FILE_EXTENSIONS",
    "build_project_summary",
    "extract_contents",
    "generate_tree",
    "load_gitignore",
    "run",
    "should_ignore",
]

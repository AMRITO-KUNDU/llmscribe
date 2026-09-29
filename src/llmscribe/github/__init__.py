"""GitHub repository source resolver package for LLMScribe."""

from .client import GitHubError, GitHubSnapshot, fetch_github_diff, fetch_github_snapshot, parse_github_repo
from .provider import (
    github_project_diff,
    github_project_get_file,
    github_project_get_files,
    github_project_list_files,
    github_project_map,
    github_project_overview,
    github_project_search,
)

__all__ = [
    "GitHubError",
    "GitHubSnapshot",
    "fetch_github_diff",
    "fetch_github_snapshot",
    "github_project_diff",
    "github_project_get_file",
    "github_project_get_files",
    "github_project_list_files",
    "github_project_map",
    "github_project_overview",
    "github_project_search",
    "parse_github_repo",
]

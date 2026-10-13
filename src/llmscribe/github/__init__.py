"""GitHub repository source for LLMScribe (archive snapshots, no cloning)."""

from .client import (
    GitHubError,
    GitHubSnapshot,
    SnapshotCache,
    clear_snapshot_cache,
    fetch_github_diff,
    fetch_github_snapshot,
    get_snapshot_cache,
    parse_github_repo,
    validate_github_ref,
)

__all__ = [
    "GitHubError",
    "GitHubSnapshot",
    "SnapshotCache",
    "clear_snapshot_cache",
    "fetch_github_diff",
    "fetch_github_snapshot",
    "get_snapshot_cache",
    "parse_github_repo",
    "validate_github_ref",
]

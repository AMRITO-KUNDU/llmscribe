"""Shared limits for every LLMScribe operation.

Every size, count and timeout used by the core, GitHub provider, MCP server
and CLI lives here so the same operation behaves the same everywhere.
"""

from __future__ import annotations

import os

# --- Output limits (characters) -------------------------------------------
MAX_CONTENT_CHARS = 400_000  # total file content returned by one overview/read_many call
MAX_DIFF_CHARS = 200_000  # diff text returned by one project_diff call
MAX_LINE_CHARS = 1_000  # a single search-result line is clipped to this length

# --- Result-count limits ---------------------------------------------------
MAX_READ_MANY_FILES = 50  # files processed by one read_many call
MAX_SEARCH_RESULTS = 1_000  # matches returned by one search call
MAX_MAP_ENTRIES = 20_000  # files + directories listed by one project_map call

# --- Repository / file size limits (bytes unless noted) --------------------
MAX_FILE_SIZE = 2 * 1024 * 1024  # larger files are never read, searched or parsed
MAX_ARCHIVE_SIZE = 100 * 1024 * 1024  # compressed GitHub archive download
MAX_REPOSITORY_SIZE = 250 * 1024 * 1024  # total uncompressed size of an archive
MAX_REPOSITORY_FILES = 100_000  # files + directories scanned in one repository
MAX_GITIGNORE_SIZE = 1024 * 1024  # a .gitignore larger than this is ignored

# --- Timeouts (seconds) ----------------------------------------------------
HTTP_TIMEOUT = 30  # per socket operation
HTTP_TOTAL_TIMEOUT = 120  # whole download
GIT_TIMEOUT = 30

# --- MCP HTTP transport ----------------------------------------------------
MAX_REQUEST_BYTES = 1_000_000  # largest accepted HTTP request body


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(minimum, int(raw))
    except ValueError:
        return default


# --- GitHub snapshot cache (configurable through the environment) ----------
def cache_max_entries() -> int:
    """``LLMSCRIBE_CACHE_MAX_ENTRIES`` (default 8, 0 disables the cache)."""
    return _env_int("LLMSCRIBE_CACHE_MAX_ENTRIES", 8)


def cache_ttl_seconds() -> int:
    """``LLMSCRIBE_CACHE_TTL_SECONDS`` (default 300)."""
    return _env_int("LLMSCRIBE_CACHE_TTL_SECONDS", 300)


CACHE_MAX_BYTES = 256 * 1024 * 1024  # total retained snapshot content across entries

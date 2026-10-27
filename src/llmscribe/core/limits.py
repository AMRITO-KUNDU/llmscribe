"""Shared limits for every LLMScribe operation.

Every size, count and timeout used by the core, MCP server and CLI lives here
so the same operation behaves the same everywhere.
"""

from __future__ import annotations

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
MAX_REPOSITORY_FILES = 100_000  # files + directories scanned in one project
MAX_GITIGNORE_SIZE = 1024 * 1024  # a .gitignore larger than this is ignored

# --- Timeouts (seconds) ----------------------------------------------------
GIT_TIMEOUT = 30

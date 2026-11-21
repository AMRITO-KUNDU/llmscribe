"""The public Python API for LLMScribe.

A thin facade over :mod:`llmscribe.core`. Build a :class:`Repository` once and call
methods on it, instead of threading the project root through every call.

    >>> from llmscribe import Repository
    >>> repo = Repository(".")
    >>> print(repo.map().tree)
    >>> for match in repo.search("auth").matches:
    ...     print(match.file_path, match.line_number, match.line_content)

Nothing here changes behaviour: every method delegates to the matching
``llmscribe.core`` function with the root given to the constructor, so the objects
you get back are the same ones the CLI and the MCP server produce.

Two error conventions, both inherited from the core:

* ``read`` and ``read_many`` **return** results carrying ``ok`` and ``error_code``.
  They never raise for a missing or unreadable file, so a batch read can report
  per-file failures instead of dying on the first one.
* ``dependencies`` and ``diff`` **raise** :class:`~llmscribe.core.errors.LLMScribeError`,
  whose ``.code`` is a stable machine-readable string.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .core import (
    DependencyResult,
    DiffResult,
    FileReadResult,
    ProjectMapResult,
    ProjectOverviewResult,
    ReadManyResult,
    SearchResult,
    analyze_dependencies,
    get_git_diff,
    limits,
    project_map,
    project_overview,
    read_file,
    read_files,
    redact_text,
    search_project,
)

__all__ = ["Repository"]


def _mask(obj: object, field_name: str) -> list[str]:
    """Mask one string field in place and return the kinds found.

    Handles both dataclass results and the plain dicts that overview returns.
    """
    if isinstance(obj, dict):
        value = obj.get(field_name)
        if not isinstance(value, str) or not value:
            return []
        masked, kinds = redact_text(value)
        if kinds:
            obj[field_name] = masked
        return kinds

    value = getattr(obj, field_name, None)
    if not isinstance(value, str) or not value:
        return []
    masked, kinds = redact_text(value)
    if kinds:
        setattr(obj, field_name, masked)
    return kinds


class Repository:
    """A local project directory, queried through one object.

    Every method delegates to the matching :mod:`llmscribe.core` function, so the
    results are identical to the CLI and MCP server output.

    The path is not validated until you call a method, so constructing a
    ``Repository`` is always cheap and side-effect free.
    """

    __slots__ = ("_ignore_patterns", "_root")

    def __init__(self, path: str | Path | None = None, *, ignore_patterns: list[str] | None = None) -> None:
        """Bind to ``path`` (default: the current directory).

        ``ignore_patterns`` are extra glob patterns applied on top of the usual
        ``.gitignore`` handling, exactly as ``project_map`` accepts them.
        """
        self._root = Path(path) if path is not None else Path.cwd()
        self._ignore_patterns = list(ignore_patterns) if ignore_patterns else None

    def __repr__(self) -> str:
        return f"Repository({str(self._root)!r})"

    @property
    def root(self) -> Path:
        """The project directory this repository reads from."""
        return self._root

    def map(self, *, max_depth: int | None = None, include_sizes: bool = False) -> ProjectMapResult:
        """The directory tree, without file contents.

        Cheapest way to show a project to a model: a few hundred tokens for a whole
        repository, and enough for most navigation decisions. Pass ``max_depth`` to
        list only the first N levels, like ``tree -L N``.
        """
        return project_map(self._root, self._ignore_patterns, max_depth, include_sizes)

    def overview(
        self,
        *,
        max_content_chars: int = limits.MAX_CONTENT_CHARS,
        max_depth: int | None = None,
        include_sizes: bool = False,
        max_tokens: int | None = None,
        compress: bool = False,
        redact: bool = True,
    ) -> ProjectOverviewResult:
        """The directory tree plus file contents.

        ``max_depth`` includes only files within the first N levels.
        """
        overview = project_overview(
            self._root,
            self._ignore_patterns,
            max_content_chars,
            max_depth,
            include_sizes,
            max_tokens,
            compress,
        )
        if redact:
            for entry in overview.files:
                if isinstance(entry, dict):
                    _mask(entry, "content")
        return overview

    def search(
        self,
        query: str,
        *,
        max_results: int = limits.MAX_SEARCH_RESULTS,
        redact: bool = True,
    ) -> SearchResult:
        """Literal substring search over file names and contents.

        Not a ranked or fuzzy search: results are ordered, and every match reports
        its path, line number and matched text. An empty result means the string is
        genuinely absent.
        """
        found = search_project(query, self._root, max_results, self._ignore_patterns)
        if redact:
            for match in found.matches:
                _mask(match, "line_content")
                _mask(match, "matched_text")
        return found

    def read(
        self,
        file_path: str | Path,
        *,
        max_content_chars: int = limits.MAX_CONTENT_CHARS,
        binary: bool = False,
        compress: bool = False,
        redact: bool = True,
    ) -> FileReadResult:
        """Read one file.

        Returns a result with ``ok`` and ``error_code`` rather than raising, so check
        ``ok`` before using ``content``.
        """
        result = read_file(str(file_path), self._root, max_content_chars, binary, compress)
        if redact and not result.media_type:
            _mask(result, "content")
        return result

    def read_many(
        self,
        file_paths: Sequence[str | Path],
        *,
        max_files: int = limits.MAX_READ_MANY_FILES,
        max_content_chars: int = limits.MAX_CONTENT_CHARS,
        redact: bool = True,
    ) -> ReadManyResult:
        """Read several files in one call.

        Per-file failures are reported in ``results`` and counted in ``error_count``;
        a missing file never aborts the batch.
        """
        batch = read_files([str(p) for p in file_paths], self._root, max_files, max_content_chars)
        if redact:
            for item in batch.results:
                _mask(item, "content")
        return batch

    def dependencies(self, file_path: str | Path) -> DependencyResult:
        """What a file imports, and what imports it.

        Raises :class:`~llmscribe.core.errors.LLMScribeError` if the file cannot be
        analysed; ``err.code`` is a stable machine-readable string.
        """
        return analyze_dependencies(str(file_path), self._root)

    def diff(
        self,
        *,
        staged: bool = False,
        commit: str | None = None,
        max_diff_chars: int = limits.MAX_DIFF_CHARS,
        redact: bool = True,
    ) -> DiffResult:
        """Git status and diff for this repository.

        Raises :class:`~llmscribe.core.errors.LLMScribeError` when the directory is
        not a Git repository.
        """
        result = get_git_diff(self._root, staged, commit, max_diff_chars)
        if redact:
            _mask(result, "diff")
        return result

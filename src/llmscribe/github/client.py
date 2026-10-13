"""GitHub access: input parsing, bounded HTTP, archive snapshots and a bounded cache.

Repositories are fetched as one zip archive through the GitHub REST API and
served from memory as a ``MemoryRepository``; nothing is cloned or written to disk.
Tokens (``GITHUB_TOKEN`` / ``GH_TOKEN``) are only ever sent to ``api.github.com``
and never appear in errors or output.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import socket
import stat
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib
from collections import OrderedDict
from typing import Any, Callable, Optional

from llmscribe import __version__
from llmscribe.core.errors import LLMScribeError
from llmscribe.core.file_reader import is_text_file
from llmscribe.core.limits import (
    CACHE_MAX_BYTES,
    HTTP_TIMEOUT,
    HTTP_TOTAL_TIMEOUT,
    MAX_ARCHIVE_SIZE,
    MAX_FILE_SIZE,
    MAX_REPOSITORY_FILES,
    MAX_REPOSITORY_SIZE,
    cache_max_entries,
    cache_ttl_seconds,
)
from llmscribe.core.source import MemoryRepository

API_HOST = "api.github.com"
_REDIRECT_HOSTS = {"api.github.com", "codeload.github.com"}
_REDIRECT_SUFFIX = ".githubusercontent.com"
_MAX_JSON_BYTES = 10 * 1024 * 1024
_ERROR_BODY_BYTES = 4096

_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")
_REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@+-]{0,254}$")
_SSH_RE = re.compile(r"^(?:ssh://)?git@github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")


class GitHubError(LLMScribeError):
    """A GitHub-related failure (same ``code``/``message`` contract as ``LLMScribeError``)."""


# --------------------------------------------------------------------------- input parsing

def _clean_repo_name(name: str) -> str:
    return name[:-4] if name.endswith(".git") else name


def validate_owner_repo(owner: str, repo: str) -> tuple[str, str]:
    """Return ``(owner, repo)`` or raise ``invalid_argument`` for names GitHub cannot have."""
    if not _OWNER_RE.match(owner or "") or not _REPO_RE.match(repo or "") or repo in (".", ".."):
        raise GitHubError("invalid_argument", f"Invalid GitHub repository: '{owner}/{repo}'.")
    return owner, repo


def validate_github_ref(ref: str) -> str:
    """Return a safe branch/tag/commit name or raise ``invalid_argument``."""
    cleaned = ref.strip()
    bad = (
        not _REF_RE.match(cleaned)
        or ".." in cleaned
        or "//" in cleaned
        or "@{" in cleaned
        or cleaned.endswith(("/", ".", ".lock"))
    )
    if bad:
        raise GitHubError("invalid_argument", f"Invalid Git reference: '{ref[:80]}'.")
    return cleaned


def parse_github_repo(repo_str: str) -> tuple[str, str]:
    """Parse ``owner/repo``, an https GitHub URL or an SSH URL into ``(owner, repo)``.

    Raises ``GitHubError(invalid_argument)`` for anything else (other hosts,
    extra path segments in the short form, unsafe characters).
    """
    if not repo_str or not str(repo_str).strip():
        raise GitHubError("invalid_argument", "GitHub repository cannot be empty.")
    cleaned = str(repo_str).strip()

    ssh = _SSH_RE.match(cleaned)
    if ssh:
        return validate_owner_repo(ssh.group(1), _clean_repo_name(ssh.group(2)))

    if "://" in cleaned:
        parsed = urllib.parse.urlparse(cleaned)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http", "https") or host not in ("github.com", "www.github.com") or parsed.username:
            raise GitHubError("invalid_argument", f"Invalid GitHub repository URL: '{cleaned[:120]}'.")
        segments = [s for s in parsed.path.split("/") if s]
        if len(segments) < 2:
            raise GitHubError("invalid_argument", f"Invalid GitHub repository URL: '{cleaned[:120]}'.")
        return validate_owner_repo(segments[0], _clean_repo_name(segments[1]))

    segments = cleaned.split("/")
    if len(segments) == 2 and all(segments):
        return validate_owner_repo(segments[0], _clean_repo_name(segments[1]))
    raise GitHubError(
        "invalid_argument",
        f"Invalid GitHub repository: '{cleaned[:120]}'. Expected 'owner/repo' or a github.com URL.",
    )


# --------------------------------------------------------------------------- HTTP

def _token() -> str:
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        value = os.environ.get(name, "").strip()
        if value and value.isprintable() and not any(c.isspace() for c in value):
            return value
    return ""


def _auth_fingerprint() -> str:
    token = _token()
    return hashlib.sha256(token.encode()).hexdigest()[:16] if token else "anonymous"


def _headers(accept: str) -> dict[str, str]:
    headers = {
        "User-Agent": f"LLMScribe/{__version__}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _allowed_redirect_host(host: str) -> bool:
    return host in _REDIRECT_HOSTS or host.endswith(_REDIRECT_SUFFIX)


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow only https redirects to GitHub hosts and never leak the token elsewhere."""

    max_redirections = 5

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        parsed = urllib.parse.urlparse(newurl)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not _allowed_redirect_host(host):
            raise GitHubError("github_unavailable", "GitHub redirected to an unexpected location.")
        new_request = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_request is not None and host != API_HOST:
            new_request.remove_header("Authorization")
        return new_request


_OPENER = urllib.request.build_opener(_SafeRedirectHandler)


def _urlopen(request: urllib.request.Request, timeout: float):
    return _OPENER.open(request, timeout=timeout)


def _translate_http_error(exc: urllib.error.HTTPError) -> GitHubError:
    status = exc.code
    headers = exc.headers or {}
    try:
        body = exc.read(_ERROR_BODY_BYTES).decode("utf-8", errors="ignore") if exc.fp is not None else ""
    except Exception:  # noqa: BLE001 - best effort, body is only used for classification
        body = ""
    has_token = bool(_token())

    if status in (403, 429):
        remaining = headers.get("x-ratelimit-remaining")
        if status == 429 or remaining == "0" or headers.get("retry-after") or "rate limit" in body.lower():
            hint = "" if has_token else " Set GITHUB_TOKEN or GH_TOKEN to raise the limit."
            return GitHubError("github_rate_limited", f"GitHub API rate limit exceeded.{hint}")
        return GitHubError(
            "github_auth_required",
            "Access denied by GitHub. Private repositories need a GITHUB_TOKEN with read access.",
        )
    if status == 401:
        return GitHubError("github_auth_required", "GitHub rejected the credentials (or none were provided).")
    if status == 404:
        hint = "" if has_token else " Private repositories require GITHUB_TOKEN."
        return GitHubError("repository_not_found", f"GitHub repository or ref not found.{hint}")
    if status == 422:
        return GitHubError("invalid_argument", "GitHub rejected the repository reference.")
    return GitHubError("github_unavailable", f"GitHub returned HTTP {status}.")


def _request(url: str, accept: str, max_bytes: int) -> bytes:
    """GET ``url`` with timeouts, a response-size cap and translated errors."""
    request = urllib.request.Request(url, headers=_headers(accept), method="GET")
    deadline = time.monotonic() + HTTP_TOTAL_TIMEOUT
    try:
        with _urlopen(request, HTTP_TIMEOUT) as response:
            declared = response.headers.get("Content-Length") if getattr(response, "headers", None) else None
            if declared and declared.isdigit() and int(declared) > max_bytes:
                raise GitHubError("repository_too_large", f"GitHub response exceeds {max_bytes:,} bytes.")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise GitHubError("repository_too_large", f"GitHub response exceeds {max_bytes:,} bytes.")
                if time.monotonic() > deadline:
                    raise GitHubError("github_unavailable", "Timed out downloading from GitHub.")
                chunks.append(chunk)
            return b"".join(chunks)
    except GitHubError:
        raise
    except urllib.error.HTTPError as exc:
        raise _translate_http_error(exc) from None
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise GitHubError("github_unavailable", f"Could not reach GitHub: {type(reason).__name__}.") from None


# --------------------------------------------------------------------------- snapshot

class GitHubSnapshot(MemoryRepository):
    """An in-memory repository unpacked from a GitHub zip archive."""

    def __init__(
        self,
        owner: str,
        repo: str,
        ref: str,
        sizes: dict[str, int],
        contents: dict[str, bytes],
        skipped: int = 0,
    ) -> None:
        explicit = bool(ref) and ref != "HEAD"
        logical = f"github.com/{owner}/{repo}" + (f"@{ref}" if explicit else "")
        super().__init__(repo, logical, sizes, contents, kind="github")
        self.owner = owner
        self.repo = repo
        self.ref = ref
        self.skipped_entries = skipped

    @classmethod
    def from_zip(cls, owner: str, repo: str, ref: str, zip_bytes: bytes) -> "GitHubSnapshot":
        """Unpack an archive safely: no extraction to disk, bounded size/count/memory."""
        try:
            archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile:
            raise GitHubError("github_unavailable", "GitHub returned a malformed archive.") from None
        with archive:
            infos = archive.infolist()
            if len(infos) > MAX_REPOSITORY_FILES:
                raise GitHubError("repository_too_large", f"Repository has more than {MAX_REPOSITORY_FILES:,} entries.")
            if sum(i.file_size for i in infos) > MAX_REPOSITORY_SIZE:
                raise GitHubError("repository_too_large", f"Repository exceeds {MAX_REPOSITORY_SIZE:,} bytes uncompressed.")

            names = [i.filename.replace("\\", "/") for i in infos]
            tops = {n.split("/", 1)[0] for n in names if n}
            strip = len(tops) == 1 and all("/" in n for n in names)
            prefix_len = len(next(iter(tops))) + 1 if strip else 0

            sizes: dict[str, int] = {}
            contents: dict[str, bytes] = {}
            skipped = 0
            retained = 0
            try:
                for info, name in zip(infos, names):
                    if name.endswith("/") or len(name) <= prefix_len:
                        continue
                    mode = info.external_attr >> 16
                    if stat.S_ISLNK(mode):
                        skipped += 1
                        continue
                    rel = _safe_member_path(name[prefix_len:])
                    if rel is None or rel in sizes:
                        skipped += 1
                        continue
                    sizes[rel] = info.file_size
                    if info.file_size > MAX_FILE_SIZE or not is_text_file(rel):
                        continue
                    with archive.open(info) as handle:
                        data = handle.read(MAX_FILE_SIZE + 1)
                    if len(data) > MAX_FILE_SIZE:
                        sizes[rel] = len(data)
                        continue
                    retained += len(data)
                    if retained > MAX_REPOSITORY_SIZE:
                        raise GitHubError("repository_too_large", "Repository content exceeds the size limit.")
                    sizes[rel] = len(data)
                    contents[rel] = data
            except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError):
                raise GitHubError("github_unavailable", "GitHub returned a corrupt archive.") from None
        return cls(owner, repo, ref, sizes, contents, skipped)


def _safe_member_path(path: str) -> str | None:
    """Return a clean relative posix path, or None if the archive member is unsafe."""
    if not path or "\x00" in path or path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return None
    parts = [p for p in path.split("/") if p not in ("", ".")]
    if not parts or ".." in parts:
        return None
    return "/".join(parts)


# --------------------------------------------------------------------------- cache

class SnapshotCache:
    """Thread-safe, bounded, in-memory LRU cache with a TTL (no persistence)."""

    def __init__(
        self,
        max_entries: int,
        ttl_seconds: float,
        max_bytes: int = CACHE_MAX_BYTES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_entries = max_entries
        self.ttl = ttl_seconds
        self.max_bytes = max_bytes
        self._clock = clock
        self._lock = threading.RLock()
        self._entries: "OrderedDict[tuple, tuple[float, GitHubSnapshot]]" = OrderedDict()
        self._loading: dict[tuple, threading.Lock] = {}

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def get(self, key: tuple) -> Optional[GitHubSnapshot]:
        with self._lock:
            item = self._entries.get(key)
            if item is None:
                return None
            stored_at, snapshot = item
            if self._clock() - stored_at >= self.ttl:
                del self._entries[key]
                return None
            self._entries.move_to_end(key)
            return snapshot

    def put(self, key: tuple, snapshot: GitHubSnapshot) -> None:
        if self.max_entries <= 0 or self.ttl <= 0 or snapshot.retained_bytes > self.max_bytes:
            return
        with self._lock:
            self._entries[key] = (self._clock(), snapshot)
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries or self._total_bytes() > self.max_bytes:
                self._entries.popitem(last=False)

    def _total_bytes(self) -> int:
        return sum(s.retained_bytes for _, s in self._entries.values())

    def get_or_load(self, key: tuple, loader: Callable[[], GitHubSnapshot]) -> GitHubSnapshot:
        """Return the cached snapshot or call ``loader`` once, even for concurrent callers."""
        cached = self.get(key)
        if cached is not None:
            return cached
        with self._lock:
            gate = self._loading.setdefault(key, threading.Lock())
        with gate:
            try:
                cached = self.get(key)
                if cached is not None:
                    return cached
                snapshot = loader()
                self.put(key, snapshot)
                return snapshot
            finally:
                with self._lock:
                    self._loading.pop(key, None)


_default_cache: SnapshotCache | None = None
_default_cache_lock = threading.Lock()


def get_snapshot_cache() -> SnapshotCache:
    """Process-wide cache configured by ``LLMSCRIBE_CACHE_MAX_ENTRIES`` / ``LLMSCRIBE_CACHE_TTL_SECONDS``."""
    global _default_cache
    with _default_cache_lock:
        if _default_cache is None:
            _default_cache = SnapshotCache(cache_max_entries(), cache_ttl_seconds())
        return _default_cache


def clear_snapshot_cache() -> None:
    """Drop every cached snapshot."""
    get_snapshot_cache().clear()


def fetch_github_snapshot(
    owner: str, repo: str, ref: Optional[str] = None, *, cache: SnapshotCache | None = None
) -> GitHubSnapshot:
    """Return a snapshot of ``owner/repo`` at ``ref`` (default branch when omitted).

    Snapshots are cached per (owner, repo, ref, credential) so repeated tool
    calls download the archive once; credentials never share cache entries.
    """
    owner, repo = validate_owner_repo(owner, repo)
    clean_ref = validate_github_ref(ref) if ref and ref.strip() else None
    key = (owner.lower(), repo.lower(), clean_ref or "HEAD", _auth_fingerprint())

    def load() -> GitHubSnapshot:
        url = f"https://{API_HOST}/repos/{owner}/{repo}/zipball"
        if clean_ref:
            url += "/" + urllib.parse.quote(clean_ref, safe="/")
        data = _request(url, "application/vnd.github+json", MAX_ARCHIVE_SIZE)
        return GitHubSnapshot.from_zip(owner, repo, clean_ref or "HEAD", data)

    return (cache if cache is not None else get_snapshot_cache()).get_or_load(key, load)


def fetch_github_diff(owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
    """Call the GitHub compare API for ``base...head`` and return the parsed JSON."""
    owner, repo = validate_owner_repo(owner, repo)
    base, head = validate_github_ref(base), validate_github_ref(head)
    url = (
        f"https://{API_HOST}/repos/{owner}/{repo}/compare/"
        f"{urllib.parse.quote(base, safe='/')}...{urllib.parse.quote(head, safe='/')}"
    )
    data = _request(url, "application/vnd.github+json", _MAX_JSON_BYTES)
    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise GitHubError("github_unavailable", "GitHub returned an unreadable compare response.") from None
    if not isinstance(parsed, dict):
        raise GitHubError("github_unavailable", "GitHub returned an unexpected compare response.")
    return parsed

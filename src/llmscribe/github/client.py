"""GitHub API client and zipball snapshot resolver using standard library urllib."""

from __future__ import annotations

import io
import json
import os
import re
import socket
import urllib.error
import urllib.request
import zipfile
from typing import Any, Optional


class GitHubError(Exception):
    """Exception raised for GitHub API or resolver errors."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def parse_github_repo(repo_str: str) -> tuple[str, str]:
    """Parse owner and repo from strings like 'owner/repo', URLs, or git endpoints.

    Examples:
        'AMRITO-KUNDU/llmscribe' -> ('AMRITO-KUNDU', 'llmscribe')
        'https://github.com/owner/repo' -> ('owner', 'repo')
        'https://github.com/owner/repo.git' -> ('owner', 'repo')
        'git@github.com:owner/repo.git' -> ('owner', 'repo')
    """
    if not repo_str or not repo_str.strip():
        raise GitHubError("invalid_argument", "GitHub repo string cannot be empty.")

    cleaned = repo_str.strip()

    # Handle SSH git URLs git@github.com:owner/repo.git
    ssh_match = re.match(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", cleaned)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    # Handle HTTP/HTTPS URLs
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        url_match = re.match(r"^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$", cleaned)
        if url_match:
            return url_match.group(1), url_match.group(2)
        raise GitHubError("invalid_argument", f"Invalid GitHub repository URL: '{repo_str}'")

    # Handle owner/repo format
    parts = [p for p in cleaned.split("/") if p]
    if len(parts) == 2:
        owner = parts[0]
        repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
        if re.match(r"^[a-zA-Z0-9_\-.]+$", owner) and re.match(r"^[a-zA-Z0-9_\-.]+$", repo):
            return owner, repo

    raise GitHubError(
        "invalid_argument",
        f"Invalid GitHub repository specifier: '{repo_str}'. Expected 'owner/repo' or GitHub URL.",
    )


def _get_auth_headers() -> dict[str, str]:
    """Build HTTP headers including GitHub token if set in environment."""
    headers = {
        "User-Agent": "LLMScribe-MCP/1.2.0",
        "Accept": "application/vnd.github.v3+json",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def _make_request(url: str, is_json: bool = True) -> bytes:
    """Make HTTP GET request to GitHub API using urllib with error translation."""
    headers = _get_auth_headers()
    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.HTTPError as exc:
        status = exc.code
        body_str = ""
        try:
            body_str = exc.read().decode("utf-8", errors="ignore")
        except Exception:
            pass

        if status == 404:
            raise GitHubError("repo_not_found", f"GitHub repository or reference not found (404): {url}")
        if status == 401:
            raise GitHubError("auth_required", "Authentication required for GitHub repository. Set GITHUB_TOKEN.")
        if status == 403:
            remaining = exc.headers.get("x-ratelimit-remaining")
            if remaining == "0" or "rate limit" in body_str.lower():
                raise GitHubError(
                    "rate_limited",
                    "GitHub API rate limit exceeded. Provide GITHUB_TOKEN or GH_TOKEN to increase limit.",
                )
            raise GitHubError(
                "auth_required",
                "Access denied for GitHub repository. Private repositories require a valid GITHUB_TOKEN.",
            )
        if status == 422:
            raise GitHubError("invalid_ref", f"Invalid Git reference or commit for GitHub repository: {url}")
        if status >= 500:
            raise GitHubError("github_unavailable", f"GitHub API service error ({status}): {exc.reason}")
        raise GitHubError("github_unavailable", f"GitHub API request failed ({status}): {exc.reason}")

    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        raise GitHubError("github_unavailable", f"Failed to connect to GitHub: {exc}")


class GitHubSnapshot:
    """In-memory repository snapshot unpacked from zipball."""

    def __init__(self, owner: str, repo: str, ref: str, zip_bytes: bytes):
        self.owner = owner
        self.repo = repo
        self.ref = ref
        self.files: dict[str, bytes] = {}

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                names = zf.namelist()
                root_prefix = names[0].split("/")[0] + "/" if names else ""
                for name in names:
                    if name.startswith(root_prefix) and not name.endswith("/"):
                        rel_path = name[len(root_prefix):]
                        self.files[rel_path] = zf.read(name)
        except zipfile.BadZipFile as exc:
            raise GitHubError("github_unavailable", f"Failed to unpack repository archive from GitHub: {exc}")

    @property
    def logical_path(self) -> str:
        """Return logical path identifier string for MCP envelopes."""
        if self.ref and self.ref != "HEAD":
            return f"github.com/{self.owner}/{self.repo}@{self.ref}"
        return f"github.com/{self.owner}/{self.repo}"

    def get_text_content(self, path: str) -> str:
        """Retrieve file content as UTF-8 string."""
        raw = self.files.get(path)
        if raw is None:
            raise FileNotFoundError(f"File not found in repository snapshot: '{path}'")
        return raw.decode("utf-8", errors="ignore")

    def load_gitignore(self) -> list[str]:
        """Parse .gitignore lines from snapshot if present."""
        raw = self.files.get(".gitignore")
        if not raw:
            return []
        try:
            content = raw.decode("utf-8", errors="ignore")
            return [
                line.strip()
                for line in content.splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
        except Exception:
            return []


def fetch_github_snapshot(owner: str, repo: str, ref: Optional[str] = None) -> GitHubSnapshot:
    """Download repository zipball archive from GitHub API and unpack into snapshot."""
    target_ref = ref.strip() if ref and ref.strip() else "HEAD"
    url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{urllib.parse.quote(target_ref)}"
    zip_bytes = _make_request(url, is_json=False)
    return GitHubSnapshot(owner, repo, target_ref, zip_bytes)


def fetch_github_diff(owner: str, repo: str, base: str, head: str) -> dict[str, Any]:
    """Call GitHub Compare API GET /repos/{owner}/{repo}/compare/{base}...{head}."""
    url = (
        f"https://api.github.com/repos/{owner}/{repo}/compare/"
        f"{urllib.parse.quote(base)}...{urllib.parse.quote(head)}"
    )
    data_bytes = _make_request(url, is_json=True)
    try:
        return json.loads(data_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise GitHubError("github_unavailable", f"Failed to parse GitHub compare response: {exc}")

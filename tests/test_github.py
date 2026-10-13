import io
import os
import stat
import urllib.error
import zipfile

import pytest

import llmscribe.github.client as gh
from conftest import GITHUB_FILES, make_zip
from llmscribe import service
from llmscribe.core import LLMScribeError
from llmscribe.github import GitHubSnapshot, SnapshotCache, fetch_github_snapshot, parse_github_repo


class FakeResponse:
    def __init__(self, data, headers=None):
        self._io = io.BytesIO(data)
        self.headers = headers or {}

    def read(self, n=-1):
        return self._io.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture
def downloads(monkeypatch):
    calls = []

    def fake(request, timeout):
        calls.append(request)
        return FakeResponse(make_zip(GITHUB_FILES))

    monkeypatch.setattr(gh, "_urlopen", fake)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    return calls


@pytest.mark.parametrize(
    "text,expected",
    [
        ("owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo/tree/main/src", ("owner", "repo")),
        ("git@github.com:owner/repo.git", ("owner", "repo")),
        ("ssh://git@github.com/owner/repo", ("owner", "repo")),
    ],
)
def test_parse_repo(text, expected):
    assert parse_github_repo(text) == expected


@pytest.mark.parametrize(
    "bad",
    ["", "owner", "a/b/c", "https://evil.com/o/r", "https://u:p@github.com/o/r", "o/..", "-bad/repo", "o/r r", "file:///etc/passwd", "../x"],
)
def test_parse_repo_rejects(bad):
    with pytest.raises(LLMScribeError) as exc:
        parse_github_repo(bad)
    assert exc.value.code == "invalid_argument"


@pytest.mark.parametrize("ref", ["--upload-pack=x", "a..b", "a b", "x;y", "refs/heads/", "-x", "a//b", "x.lock", "a@{1}"])
def test_ref_validation(ref, downloads):
    with pytest.raises(LLMScribeError) as exc:
        fetch_github_snapshot("o", "r", ref, cache=SnapshotCache(4, 60))
    assert exc.value.code == "invalid_argument" and not downloads


def test_cache_behaviour(downloads):
    now = [0.0]
    cache = SnapshotCache(2, 100, clock=lambda: now[0])
    fetch_github_snapshot("o", "r", None, cache=cache)
    assert len(downloads) == 1
    fetch_github_snapshot("O", "R", None, cache=cache)  # same repo, case-insensitive: hit
    assert len(downloads) == 1
    fetch_github_snapshot("o", "r", "dev", cache=cache)  # different ref: miss
    assert len(downloads) == 2
    fetch_github_snapshot("o", "other", None, cache=cache)  # different repo: miss + eviction of LRU
    assert len(downloads) == 3 and len(cache) == 2
    fetch_github_snapshot("o", "r", None, cache=cache)  # was evicted: download again
    assert len(downloads) == 4
    now[0] = 1000  # expired
    fetch_github_snapshot("o", "r", None, cache=cache)
    assert len(downloads) == 5


def test_cache_not_shared_between_credentials(downloads, monkeypatch):
    cache = SnapshotCache(4, 100)
    fetch_github_snapshot("o", "r", cache=cache)
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_" + "a" * 30)
    fetch_github_snapshot("o", "r", cache=cache)
    assert len(downloads) == 2


def test_cache_disabled_and_url(downloads):
    cache = SnapshotCache(0, 100)
    fetch_github_snapshot("o", "r", "feature/x", cache=cache)
    fetch_github_snapshot("o", "r", "feature/x", cache=cache)
    assert len(downloads) == 2 and len(cache) == 0
    assert downloads[0].full_url == "https://api.github.com/repos/o/r/zipball/feature/x"


def test_token_sent_only_in_header_and_never_leaked(downloads, monkeypatch):
    token = "ghp_" + "b" * 30
    monkeypatch.setenv("GITHUB_TOKEN", token)
    fetch_github_snapshot("o", "r", cache=SnapshotCache(1, 1))
    assert downloads[0].get_header("Authorization") == f"Bearer {token}"
    assert token not in downloads[0].full_url
    err = LLMScribeError("read_error", f"failed with {token}")
    assert token not in err.message and token not in service.render_error("read", err, True)


def test_redirect_handler_blocks_foreign_hosts_and_strips_auth(monkeypatch):
    import urllib.request

    handler = gh._SafeRedirectHandler()
    req = urllib.request.Request("https://api.github.com/x", headers={"Authorization": "Bearer t"})
    with pytest.raises(LLMScribeError):
        handler.redirect_request(req, None, 302, "Found", {}, "https://evil.example/zip")
    with pytest.raises(LLMScribeError):
        handler.redirect_request(req, None, 302, "Found", {}, "http://codeload.github.com/zip")
    new = handler.redirect_request(req, None, 302, "Found", {}, "https://codeload.github.com/zip")
    assert new.get_header("Authorization") is None


def _http_error(code, headers=None, body=b""):
    return urllib.error.HTTPError("https://api.github.com/x", code, "x", headers or {}, io.BytesIO(body))


@pytest.mark.parametrize(
    "error,code",
    [
        (_http_error(404), "repository_not_found"),
        (_http_error(401), "github_auth_required"),
        (_http_error(403), "github_auth_required"),
        (_http_error(403, {"x-ratelimit-remaining": "0"}), "github_rate_limited"),
        (_http_error(429), "github_rate_limited"),
        (_http_error(403, body=b"API rate limit exceeded"), "github_rate_limited"),
        (_http_error(500), "github_unavailable"),
        (urllib.error.URLError("boom"), "github_unavailable"),
        (TimeoutError(), "github_unavailable"),
    ],
)
def test_http_errors(monkeypatch, error, code):
    def fake(request, timeout):
        raise error

    monkeypatch.setattr(gh, "_urlopen", fake)
    with pytest.raises(LLMScribeError) as exc:
        fetch_github_snapshot("o", "r", cache=SnapshotCache(1, 1))
    assert exc.value.code == code


def test_download_size_limits(monkeypatch):
    monkeypatch.setattr(gh, "_urlopen", lambda r, t: FakeResponse(b"x" * 5000))
    monkeypatch.setattr(gh, "MAX_ARCHIVE_SIZE", 1000)
    with pytest.raises(LLMScribeError) as exc:
        fetch_github_snapshot("o", "r", cache=SnapshotCache(1, 1))
    assert exc.value.code == "repository_too_large"
    monkeypatch.setattr(gh, "_urlopen", lambda r, t: FakeResponse(b"x", {"Content-Length": "999999"}))
    with pytest.raises(LLMScribeError) as exc:
        gh._request("https://api.github.com/x", "a", 1000)
    assert exc.value.code == "repository_too_large"


def test_archive_hardening(monkeypatch):
    def extra(zf):
        zf.writestr("own-repo-abc123/../../evil.py", "x")
        zf.writestr("own-repo-abc123//abs.py", "x")
        info = zipfile.ZipInfo("own-repo-abc123/link.py")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(info, "/etc/passwd")
        zf.writestr("own-repo-abc123/pic.png", b"\x89PNG\x00")

    snap = GitHubSnapshot.from_zip("o", "r", "HEAD", make_zip({"ok.py": "x"}, extra=extra))
    assert sorted(snap.sizes) == ["abs.py", "ok.py", "pic.png"] or sorted(snap.sizes) == ["ok.py", "pic.png"]
    assert "evil.py" not in snap.sizes and "link.py" not in snap.sizes and snap.skipped_entries >= 2
    assert "pic.png" not in snap.contents  # binary kept as metadata only


def test_malformed_and_oversized_archives(monkeypatch):
    with pytest.raises(LLMScribeError) as exc:
        GitHubSnapshot.from_zip("o", "r", "HEAD", b"not a zip")
    assert exc.value.code == "github_unavailable"
    monkeypatch.setattr(gh, "MAX_REPOSITORY_FILES", 2)
    with pytest.raises(LLMScribeError) as exc:
        GitHubSnapshot.from_zip("o", "r", "HEAD", make_zip({"a.py": "1", "b.py": "2", "c.py": "3"}))
    assert exc.value.code == "repository_too_large"
    monkeypatch.undo()
    monkeypatch.setattr(gh, "MAX_REPOSITORY_SIZE", 10)
    with pytest.raises(LLMScribeError) as exc:
        GitHubSnapshot.from_zip("o", "r", "HEAD", make_zip({"a.py": "x" * 100}))
    assert exc.value.code == "repository_too_large"


def test_zip_bomb_lying_header(monkeypatch):
    monkeypatch.setattr(gh, "MAX_FILE_SIZE", 100)
    snap = GitHubSnapshot.from_zip("o", "r", "HEAD", make_zip({"big.txt": "a" * 100000}))
    assert "big.txt" not in snap.contents  # never held in memory


def test_concurrent_loads_download_once(downloads):
    import threading

    cache = SnapshotCache(2, 60)
    threads = [threading.Thread(target=fetch_github_snapshot, args=("o", "r", None), kwargs={"cache": cache}) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(downloads) == 1


# ---------------------------------------------------------------- parity

TOOLS_CASES = [
    ("project_map", {}),
    ("search", {"query": "needle"}),
    ("read", {"file_path": "src/pkg/b.py"}),
    ("read_many", {"file_paths": ["README.md", "src/pkg/b.py", "missing.py"]}),
    ("project_dependencies", {"file_path": "src/pkg/a.py"}),
    ("project_dependencies", {"file_path": "src/pkg/b.py"}),
    ("project_overview", {}),
]


def _shape(value):
    if isinstance(value, dict):
        return {k: _shape(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_shape(v) for v in value[:1]]
    return type(value).__name__


def test_local_github_parity(repo, downloads, monkeypatch):
    monkeypatch.setattr(gh, "_default_cache", SnapshotCache(4, 60))
    for tool, args in TOOLS_CASES:
        local = service.execute(tool, path=str(repo), **args)
        remote = service.execute(tool, repo="o/r", **args)
        assert (local.source, remote.source) == ("local", "github")
        assert local.tool == remote.tool == tool
        assert _shape(local.data) == _shape(remote.data), tool
        assert local.metadata.keys() == remote.metadata.keys()
        for key in ("tree", "files", "matches", "content", "results", "used_by", "file_dependencies"):
            if key in local.data:
                lval, rval = local.data[key], remote.data[key]
                if key == "tree":  # first line is the repository name
                    lval, rval = lval.split("\n", 1)[1], rval.split("\n", 1)[1]
                assert _normalize(lval, str(repo)) == _normalize(rval, str(repo)), (tool, key)
    assert len(downloads) == 1  # one archive for every GitHub call


def _normalize(value, root):
    import json

    return json.loads(json.dumps(value).replace(root.replace("\\", "/"), "<root>").replace(os.path.basename(root) + "/", "<root>/"))


def test_github_errors_use_same_codes(downloads):
    for tool, args, code in (
        ("read", {"file_path": "missing.py"}, "file_not_found"),
        ("read", {"file_path": "../x"}, "invalid_path"),
        ("read", {"file_path": "src"}, "invalid_path"),
        ("read_many", {"file_paths": []}, "invalid_argument"),
        ("project_dependencies", {"file_path": "README.md"}, "unsupported_operation"),
    ):
        with pytest.raises(LLMScribeError) as exc:
            service.execute(tool, repo="o/r", **args)
        assert exc.value.code == code, tool


def test_github_diff(monkeypatch):
    payload = {"files": [
        {"filename": "a.py", "status": "modified", "patch": "@@ -1 +1 @@\n-a\n+b"},
        {"filename": "n.py", "status": "renamed", "previous_filename": "o.py", "patch": "@@"},
        {"filename": "img.png", "status": "added"},
    ]}
    monkeypatch.setattr(service, "fetch_github_diff", lambda o, r, b, h: payload)
    result = service.execute("project_diff", repo="o/r", commit="main", ref="dev")
    assert result.source == "github" and result.path == "github.com/o/r@dev"
    assert result.data["changed_files"] == ["a.py", "n.py", "img.png"]
    assert result.data["changes"][1]["original_path"] == "o.py"
    assert "no textual patch" in result.data["note"]
    for kwargs, code in (({"commit": None}, "invalid_argument"), ({"commit": "x", "staged": True}, "unsupported_operation")):
        with pytest.raises(LLMScribeError) as exc:
            service.execute("project_diff", repo="o/r", **kwargs)
        assert exc.value.code == code

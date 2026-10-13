import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

import llmscribe
from llmscribe import service
from llmscribe.mcp import asgi, tools

EXPECTED = ["project_dependencies", "project_diff", "project_map", "project_overview", "read", "read_many", "search"]


def cli(*args, cwd=None):
    return subprocess.run([sys.executable, "-m", "llmscribe", *args], capture_output=True, text=True, cwd=cwd)


# ---------------------------------------------------------------- CLI
def test_cli_version_and_help():
    assert cli("version").stdout.strip() == f"llmscribe version {llmscribe.__version__}"
    assert "dependencies" in cli("--help").stdout


@pytest.mark.parametrize(
    "args",
    [["map"], ["overview"], ["search", "needle"], ["read", "README.md"], ["read-many", "README.md", "nope.md"], ["dependencies", "src/pkg/a.py"]],
)
def test_cli_json_is_clean(repo, args):
    result = cli(*args, "--path", str(repo), "--json")
    payload = json.loads(result.stdout)  # stdout is exactly one JSON document
    assert payload["ok"] is True and payload["tool"] in service.TOOLS and result.stderr == ""


def test_cli_errors_and_exit_codes(repo, tmp_path):
    missing = cli("read", "nope.py", "--path", str(repo))
    assert missing.returncode == 1 and missing.stdout == "" and "file_not_found" in missing.stderr
    payload = json.loads(cli("read", "../x", "--path", str(repo), "--json").stdout)
    assert payload["ok"] is False and payload["error"]["code"] == "invalid_path"
    assert cli("map", "--path", str(tmp_path / "nope")).returncode == 1
    assert cli("bogus").returncode == 2
    assert cli("diff", "--path", str(repo), "--json").returncode == 1  # not a git repo
    empty = json.loads(cli("search", "zzzzqq", "--path", str(repo), "--json").stdout)
    assert empty["data"]["match_count"] == 0


# ---------------------------------------------------------------- MCP tools (SDK-free)
def test_tool_names_and_functions():
    assert sorted(tools.TOOL_FUNCTIONS) == EXPECTED == sorted(service.TOOLS)
    assert all(fn.__doc__ for fn in tools.TOOL_FUNCTIONS.values())


def test_tools_execute_and_errors(repo):
    tools.set_local_roots(None)
    assert "Needle" in tools.read("README.md", path=str(repo))
    payload = json.loads(tools.read_many([], path=str(repo), format="json"))
    assert payload["error"]["code"] == "invalid_argument"
    assert "Error [invalid_argument]" in tools.search("x", path=str(repo), repo="o/r")
    assert "Error [invalid_argument]" in tools.project_map(format="yaml")
    assert "legacy" not in tools.project_map(path=str(repo))
    for legacy in ("project_get_file", "project_search", "project_list_files", "project_get_files"):
        assert legacy not in tools.project_map(path=str(repo), format="json")


def test_internal_errors_have_no_traceback(repo, monkeypatch):
    tools.set_local_roots(None)
    monkeypatch.setattr(service, "map_source", lambda s: 1 / 0)
    out = tools.project_map(path=str(repo))
    assert "internal_error" in out and "Traceback" not in out and "ZeroDivision" not in out


def test_local_path_policy(repo, tmp_path):
    tools.set_local_roots([])
    assert "unsupported_operation" in tools.project_map(path=str(repo))
    tools.set_local_roots([repo])
    assert "Error" not in tools.project_map(path=str(repo / "src"))
    assert "invalid_path" in tools.project_map(path=str(tmp_path.parent))
    tools.set_local_roots(None)


def test_local_roots_env(monkeypatch, tmp_path):
    monkeypatch.delenv("MCP_ALLOW_LOCAL_PATHS", raising=False)
    monkeypatch.delenv("MCP_ALLOWED_ROOTS", raising=False)
    assert tools.local_roots_from_env(False) is None
    assert tools.local_roots_from_env(True) == []
    monkeypatch.setenv("MCP_ALLOWED_ROOTS", str(tmp_path))
    assert tools.local_roots_from_env(True) == [tmp_path.resolve()]
    monkeypatch.setenv("MCP_ALLOW_LOCAL_PATHS", "1")
    assert tools.local_roots_from_env(True) is None


def test_mcp_registration_via_public_api():
    pytest.importorskip("mcp")
    from llmscribe.mcp import mcp

    if not hasattr(mcp, "list_tools"):
        pytest.skip("SDK without list_tools")
    listed = asyncio.run(mcp.list_tools())
    assert sorted(t.name for t in listed) == EXPECTED
    by_name = {t.name: t for t in listed}

    def schema(tool):
        # The MCP SDK exposes the JSON Schema as ``input_schema`` in 2.x and as
        # ``inputSchema`` in 1.x; accept either so the test tracks both ranges.
        return tool.input_schema if hasattr(tool, "input_schema") else tool.inputSchema

    assert "query" in schema(by_name["search"])["required"]
    assert set(schema(by_name["project_diff"])["properties"]) >= {"path", "repo", "ref", "staged", "commit", "format"}
    assert schema(by_name["read_many"])["properties"]["file_paths"]["type"] == "array"


# ---------------------------------------------------------------- HTTP layer
async def _call(app, method, path, headers=None, body=b""):
    sent = []

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    raw = [(k.encode(), v.encode()) for k, v in (headers or {}).items()]
    await app({"type": "http", "method": method, "path": path, "headers": raw}, receive, send)
    return sent[0]["status"], sent[1]["body"], dict(sent[0]["headers"])


def _app(**kw):
    seen = {}

    async def inner(scope, receive, send):
        seen["path"] = scope["path"]
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"mcp"})

    app = asgi.HttpApp(
        inner, version="9.9.9", backend="test", tools=EXPECTED,
        allowed_hosts=kw.get("hosts", ["localhost", "localhost:*", "mcp.example.com"]),
        allowed_origins=kw.get("origins", ["http://localhost:*", "https://claude.ai"]),
        max_body_bytes=kw.get("max", 100),
    )
    return app, seen


def run(coro):
    return asyncio.run(coro)


def test_health_info_and_routes():
    app, _ = _app()
    status, body, _ = run(_call(app, "GET", "/health"))
    assert status == 200 and json.loads(body)["tools"] == EXPECTED
    assert run(_call(app, "HEAD", "/health"))[1] == b""
    info = json.loads(run(_call(app, "GET", "/info"))[1])
    assert info["version"] == "9.9.9" and info["tools"] == 7 and info["mcp_endpoint"] == "/mcp"
    assert run(_call(app, "POST", "/health"))[0] == 405
    assert run(_call(app, "GET", "/old-endpoint"))[0] == 404


def test_mcp_security():
    app, seen = _app()
    ok = {"host": "localhost:8000"}
    assert run(_call(app, "POST", "/mcp", ok))[0] == 200 and seen["path"] == "/"
    run(_call(app, "POST", "/mcp/x", ok))
    assert seen["path"] == "/x"
    assert run(_call(app, "POST", "/mcp", {"host": "evil.com"}))[0] == 421
    assert run(_call(app, "POST", "/mcp", {"host": "mcp.example.com"}))[0] == 200
    assert run(_call(app, "POST", "/mcp", {"host": "localhost", "origin": "http://evil.com"}))[0] == 403
    assert run(_call(app, "POST", "/mcp", {"host": "localhost", "origin": "http://localhost:6274"}))[0] == 200
    assert run(_call(app, "POST", "/mcp", {"host": "localhost", "origin": "https://claude.ai"}))[0] == 200
    assert run(_call(app, "POST", "/mcp", {"host": "localhost", "content-length": "5000"}))[0] == 413
    assert run(_call(app, "POST", "/mcp", {"host": "localhost"}, body=b"x" * 500))[0] == 413
    assert run(_call(app, "GET", "/health", {"host": "anything.example"}))[0] == 200  # status routes unrestricted


def test_wildcards_and_env_config():
    app, _ = _app(hosts=["*"], origins=["*"])
    assert run(_call(app, "POST", "/mcp", {"host": "any.host", "origin": "https://any.origin"}))[0] == 200
    env = {"RENDER_EXTERNAL_HOSTNAME": "svc.onrender.com"}
    assert asgi.host_allowed("svc.onrender.com", asgi.allowed_hosts_from_env(env))
    assert asgi.origin_allowed("https://svc.onrender.com", asgi.allowed_origins_from_env(env))
    assert not asgi.host_allowed("evil.com", asgi.allowed_hosts_from_env({}))
    assert not asgi.origin_allowed("http://localhost.evil.com", asgi.allowed_origins_from_env({}))
    assert asgi.allowed_hosts_from_env({"MCP_ALLOWED_HOSTS": "a.com, b.com"}) == ["a.com", "b.com"]


def test_lifespan_runs_context():
    events = []

    class Ctx:
        async def __aenter__(self):
            events.append("start")

        async def __aexit__(self, *a):
            events.append("stop")

    app = asgi.HttpApp(lambda *a: None, version="1", backend="t", tools=[], allowed_hosts=[], allowed_origins=[], lifespan=Ctx)
    messages = iter([{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}])
    sent = []

    async def receive():
        return next(messages)

    async def send(m):
        sent.append(m["type"])

    run(app({"type": "lifespan"}, receive, send))
    assert events == ["start", "stop"] and sent == ["lifespan.startup.complete", "lifespan.shutdown.complete"]


# ---------------------------------------------------------------- repository hygiene
ROOT = Path(__file__).resolve().parent.parent


def test_single_version_source():
    import re

    assert re.fullmatch(r"\d+\.\d+\.\d+", llmscribe.__version__)
    assert "version =" not in (ROOT / "pyproject.toml").read_text().split("[project]")[1].split("[project.optional")[0].replace("dynamic", "")


def test_no_secrets_or_legacy_names_in_source():
    banned = ["project_get_file", "project_search", "project_list_files", "ghp_", "github_pat_", "Authorization: Bearer "]
    for path in (ROOT / "src").rglob("*.py"):
        if path.name == "errors.py":  # holds the token-redaction patterns
            continue
        text = path.read_text()
        for word in banned:
            assert word not in text.replace('"Authorization"', ""), (path, word)

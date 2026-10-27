import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

import llmscribe
from llmscribe import service
from llmscribe.mcp import tools

EXPECTED = [
    "project_dependencies",
    "project_diff",
    "project_impact",
    "project_map",
    "project_overview",
    "read",
    "read_many",
    "search",
]


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


def test_cli_impact(repo):
    payload = json.loads(cli("impact", "src/pkg/b.py", "--path", str(repo), "--json").stdout)
    assert payload["ok"] is True and payload["tool"] == "project_impact"
    affected = [entry["file_path"] for entry in payload["data"]["affected"]]
    assert "src/pkg/a.py" in affected  # a.py imports b.py, so it is in scope


# ---------------------------------------------------------------- MCP tools (SDK-free)
def test_tool_names_and_functions():
    assert sorted(tools.TOOL_FUNCTIONS) == EXPECTED == sorted(service.TOOLS)
    assert all(fn.__doc__ for fn in tools.TOOL_FUNCTIONS.values())


def test_tools_execute_and_errors(repo):
    tools.set_local_roots(None)
    assert "Needle" in tools.read("README.md", path=str(repo))
    payload = json.loads(tools.read_many([], path=str(repo), format="json"))
    assert payload["error"]["code"] == "invalid_argument"
    assert "Error [invalid_argument]" in tools.search("x", format="yaml")
    assert "legacy" not in tools.project_map(path=str(repo))
    for legacy in ("project_get_file", "project_search", "project_list_files", "project_get_files"):
        assert legacy not in tools.project_map(path=str(repo), format="json")


def test_tools_reject_cloud_arguments(repo):
    # GitHub support was removed: the tools no longer accept repo/ref.
    for kwargs in ({"repo": "o/r"}, {"ref": "main"}):
        with pytest.raises(TypeError):
            tools.project_map(path=str(repo), **kwargs)


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
    assert tools.local_roots_from_env() is None  # default: unrestricted
    monkeypatch.setenv("MCP_ALLOWED_ROOTS", str(tmp_path))
    assert tools.local_roots_from_env() == [tmp_path.resolve()]
    monkeypatch.delenv("MCP_ALLOWED_ROOTS", raising=False)
    monkeypatch.setenv("MCP_ALLOW_LOCAL_PATHS", "0")
    assert tools.local_roots_from_env() == []  # explicitly disabled


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
    assert set(schema(by_name["project_diff"])["properties"]) >= {"path", "staged", "commit", "format"}
    assert schema(by_name["read_many"])["properties"]["file_paths"]["type"] == "array"
    # No cloud arguments on any tool.
    for name in EXPECTED:
        assert "repo" not in schema(by_name[name])["properties"]
        assert "ref" not in schema(by_name[name])["properties"]


# ---------------------------------------------------------------- repository hygiene
ROOT = Path(__file__).resolve().parent.parent


def test_single_version_source():
    import re

    assert re.fullmatch(r"\d+\.\d+\.\d+", llmscribe.__version__)
    assert "version =" not in (ROOT / "pyproject.toml").read_text().split("[project]")[1].split("[project.optional")[0].replace("dynamic", "")


def test_no_cloud_code_or_secrets_in_source():
    banned = ["project_get_file", "project_search", "project_list_files", "ghp_", "github_pat_", "api.github", "zipball", "Authorization: Bearer "]
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text()
        for word in banned:
            assert word not in text, (path, word)


def test_cloud_code_removed():
    assert not (ROOT / "src" / "llmscribe" / "github").exists()
    assert not (ROOT / "src" / "llmscribe" / "mcp" / "asgi.py").exists()
    for name in ("Dockerfile", "Procfile", "railway.json", ".dockerignore"):
        assert not (ROOT / name).exists(), name

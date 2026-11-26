"""The integration surface: cheap to install, easy to adopt, stable to build on.

These are the tests that keep LLMScribe usable as a *library* rather than only as a
server. The most important one is import purity: if importing the package ever starts
pulling in `mcp`, the 155-package dependency tree comes back and framework authors go
back to writing their own file readers.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from llmscribe import SCHEMA_VERSION, Repository, tool_names, tool_schemas
from llmscribe.schema import TOOLS
from llmscribe.tools import require, tools

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- import purity
def test_importing_the_package_pulls_no_server_dependencies():
    code = (
        "import sys, llmscribe; from llmscribe import Repository, tool_schemas;"
        "assert 'mcp' not in sys.modules, 'mcp was imported';"
        "assert 'pydantic' not in sys.modules, 'pydantic was imported';"
        "print('clean')"
    )
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    assert "clean" in proc.stdout


def test_core_declares_only_pathspec():
    """The packaging promise, checked at the source."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    core = text.split("dependencies = [", 1)[1].split("]", 1)[0]
    declared = [line for line in core.splitlines() if "pathspec" in line or "mcp" in line or "pydantic" in line]
    assert len(declared) == 1 and "pathspec" in declared[0], declared
    assert 'server = [' in text and '"mcp>=1.9,<3"' in text.split("server = [", 1)[1][:120]


def test_mcp_entry_explains_a_missing_extra():
    """A missing extra must say what to install, not raise a bare ImportError."""
    source = (ROOT / "src" / "llmscribe" / "mcp_entry.py").read_text(encoding="utf-8")
    assert "llmscribe[server]" in source


# ---------------------------------------------------------------- schemas
def test_every_tool_has_a_schema():
    assert len(TOOLS) == 7
    assert tool_names() == [tool["name"] for tool in TOOLS]


@pytest.mark.parametrize(
    "fmt,keys",
    [
        ("openai", ("type", "function")),
        ("anthropic", ("name", "description", "input_schema")),
        ("mcp", ("name", "description", "inputSchema")),
        ("raw", ("name", "description", "parameters")),
    ],
)
def test_formats_have_the_right_shape(fmt, keys):
    schemas = tool_schemas(fmt)
    assert len(schemas) == 7
    assert tuple(schemas[0]) == keys


def test_unknown_format_is_rejected():
    with pytest.raises(ValueError):
        tool_schemas("langchain")


def test_schema_version_is_published():
    assert SCHEMA_VERSION == "1.0"
    from llmscribe import service

    response = service.execute("project_map", path=".")
    assert json.loads(service.render_json(response))["schema_version"] == SCHEMA_VERSION


# ---------------------------------------------------------------- handlers
def test_bound_tools_cannot_be_repointed():
    """`path` is dropped: a model must not be able to read another directory."""
    for tool in tools(Repository(".")):
        assert "path" not in tool.parameters.get("properties", {}), tool.name


def test_handlers_never_raise(tmp_path):
    handlers = Repository(tmp_path).handlers()
    result = handlers["read"](file_path="nope.py")
    assert result["ok"] is False
    assert result["error"]["code"] == "file_not_found"


def test_handlers_return_the_envelope(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    result = Repository(tmp_path).handlers()["project_map"](depth=1)
    assert result["ok"] is True and result["schema_version"] == SCHEMA_VERSION
    assert result["data"]["files"] == ["a.py"]


def test_handlers_translate_schema_arguments(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    result = Repository(tmp_path).handlers()["project_map"](sizes=True)
    assert result["data"]["sizes"] == {"a.py": 6}


def test_missing_framework_gets_an_install_hint():
    with pytest.raises(ModuleNotFoundError) as excinfo:
        require("definitely_not_installed_pkg")
    assert "pip install" in str(excinfo.value)


# ---------------------------------------------------------------- adapters
@pytest.fixture
def project(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    return tmp_path


def test_anthropic_adapter_needs_no_sdk(project):
    from llmscribe.adapters import as_anthropic_tools

    definitions, dispatch = as_anthropic_tools(Repository(project))
    assert len(definitions) == 7
    assert set(definitions[0]) == {"name", "description", "input_schema"}
    assert dispatch["project_map"](depth=1)["data"]["files"] == ["a.py"]


def test_langchain_adapter(project):
    pytest.importorskip("langchain_core")
    from llmscribe.adapters import as_langchain_tools

    built = as_langchain_tools(Repository(project))
    assert len(built) == 7
    assert built[0].invoke({"depth": 1})["ok"] is True


def test_pydantic_ai_adapter(project):
    pytest.importorskip("pydantic_ai")
    from llmscribe.adapters import as_pydantic_ai_tools

    assert len(as_pydantic_ai_tools(Repository(project))) == 7


def test_smolagents_adapter(project):
    pytest.importorskip("smolagents")
    from llmscribe.adapters import as_smolagents_tools

    built = as_smolagents_tools(Repository(project))
    assert len(built) == 7
    assert built[0](depth=1)["ok"] is True

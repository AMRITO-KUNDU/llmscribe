"""`--read-only` must hide the write tools, not merely refuse them.

A model cannot ask for a tool it cannot see, so the strong guarantee is that the write
tools are never registered in that session.
"""

import json
import os
import re
import subprocess
import sys

import pytest

from llmscribe.schema import _REL_PATH_PATTERN, tool_schemas
from llmscribe.service import READ_ONLY_TOOLS, TOOLS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def list_tools(read_only: bool) -> list[str]:
    """Ask the server what it registered, in a fresh interpreter."""
    env = {**os.environ}
    env.pop("LLMSCRIBE_READ_ONLY", None)
    if read_only:
        env["LLMSCRIBE_READ_ONLY"] = "1"
    code = (
        "import asyncio, json, llmscribe.mcp as m;"
        "print(json.dumps(sorted(t.name for t in asyncio.run(m.mcp.list_tools()))))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


def test_read_only_registers_only_the_read_tools():
    assert list_tools(read_only=True) == sorted(READ_ONLY_TOOLS)


def test_default_registers_everything():
    assert list_tools(read_only=False) == sorted(TOOLS)


def test_read_only_hides_every_write_tool():
    hidden = set(TOOLS) - set(READ_ONLY_TOOLS)
    assert hidden, "there should be write tools to hide"
    listed = set(list_tools(read_only=True))
    assert listed & hidden == set(), f"write tools leaked: {listed & hidden}"


# ---------------------------------------------------------------- schema paths
@pytest.mark.parametrize("path", ["src/main.py", "a.py", "a..b.py", "deep/nested/f.py"])
def test_safe_paths_match_the_schema_pattern(path):
    assert re.match(_REL_PATH_PATTERN, path)


@pytest.mark.parametrize("path", ["../x.py", "a/../../b.py", "/etc/passwd", "C:/x", "a\\b.py", "..", "a\x00b"])
def test_unsafe_paths_are_rejected_by_the_schema(path):
    assert not re.match(_REL_PATH_PATTERN, path)


def test_every_file_parameter_carries_the_constraint():
    """The runtime check is the real guard; the schema must say so too."""
    missing = []
    for tool in tool_schemas("raw"):
        for name, spec in tool["parameters"].get("properties", {}).items():
            if name.endswith("_path") or name == "file_path":
                if spec.get("pattern") != _REL_PATH_PATTERN:
                    missing.append(f"{tool['name']}.{name}")
    assert missing == [], f"path parameters without a schema pattern: {missing}"

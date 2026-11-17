"""``--depth`` limits map/overview to the first N levels, like ``tree -L N``.

Depth is the number of path segments: a top-level file is depth 1, ``a/b.py`` is
depth 2. Entries deeper than the limit are dropped from both the tree and the file
list, so ``overview --depth 2`` does not read files it was told to skip.
"""

import json
import subprocess
import sys

import pytest

from llmscribe import LLMScribeError, Repository, core
from llmscribe.mcp import tools


@pytest.fixture
def nested(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    (tmp_path / "top.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "a" / "mid.py").write_text("y = 1\n", encoding="utf-8")
    (tmp_path / "a" / "b" / "deep.py").write_text("z = 1\n", encoding="utf-8")
    return tmp_path


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "llmscribe", *args], capture_output=True, text=True)


# ---------------------------------------------------------------- core
def test_depth_filters_the_file_list(nested):
    assert core.project_map(nested).files == ["a/b/deep.py", "a/mid.py", "top.py"]
    assert core.project_map(nested, max_depth=1).files == ["top.py"]
    assert core.project_map(nested, max_depth=2).files == ["a/mid.py", "top.py"]
    assert core.project_map(nested, max_depth=3).files == ["a/b/deep.py", "a/mid.py", "top.py"]


def test_depth_prunes_the_tree(nested):
    tree = core.project_map(nested, max_depth=2).tree
    assert "mid.py" in tree
    assert "b" in tree, "the directory at the limit should still be shown"
    assert "deep.py" not in tree, "children of a directory at the limit must be dropped"


def test_depth_must_be_positive(nested):
    with pytest.raises(LLMScribeError) as excinfo:
        core.project_map(nested, max_depth=0)
    assert excinfo.value.code == "invalid_argument"


def test_no_depth_is_unchanged(nested):
    """The default must stay exactly as it was before --depth existed."""
    assert core.project_map(nested).files == core.project_map(nested, max_depth=None).files
    assert "deep.py" in core.project_map(nested).tree


# ---------------------------------------------------------------- surfaces
def test_sdk_depth(nested):
    repo = Repository(nested)
    assert repo.map(max_depth=2).files == ["a/mid.py", "top.py"]
    assert [f["path"] for f in repo.overview(max_depth=1).files] == ["top.py"]


def test_mcp_depth(nested):
    mapped = json.loads(tools.project_map(path=str(nested), format="json", depth=2))
    assert mapped["data"]["files"] == ["a/mid.py", "top.py"]

    overview = json.loads(tools.project_overview(path=str(nested), format="json", depth=1))
    assert [f["path"] for f in overview["data"]["files"]] == ["top.py"]

    bad = json.loads(tools.project_map(path=str(nested), format="json", depth=0))
    assert bad["error"]["code"] == "invalid_argument"


def test_cli_depth(nested):
    out = json.loads(run_cli("map", "--path", str(nested), "--depth", "2", "--json").stdout)
    assert out["data"]["files"] == ["a/mid.py", "top.py"]

    text = run_cli("map", "--path", str(nested), "--depth", "1").stdout
    assert "top.py" in text and "mid.py" not in text


def test_cli_rejects_a_bad_depth(nested):
    proc = run_cli("map", "--path", str(nested), "--depth", "0")
    assert proc.returncode == 1
    assert "invalid_argument" in proc.stderr

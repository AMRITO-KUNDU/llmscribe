"""`start_line` / `end_line` read part of a file.

The point is context economy: asking for lines 200-250 of a 5,000-line file must return
51 lines, not 5,000. `line_count` always reports the whole file, so the caller can tell
there is more.
"""

import json
import subprocess
import sys

import pytest

from llmscribe import LLMScribeError, Repository, core
from llmscribe.mcp import tools


@pytest.fixture
def big(tmp_path):
    (tmp_path / "big.py").write_text("".join(f"line{i}\n" for i in range(1, 501)), encoding="utf-8")
    return tmp_path


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "llmscribe", *args], capture_output=True, text=True)


def test_reads_only_the_requested_lines(big):
    result = Repository(big).read("big.py", start_line=200, end_line=250)
    assert result.returned_lines == 51
    assert result.content.startswith("line200\n")
    assert result.content.endswith("line250\n")


def test_line_count_still_describes_the_whole_file(big):
    """The agent must be able to tell there is more file."""
    result = Repository(big).read("big.py", start_line=10, end_line=12)
    assert result.line_count == 500
    assert result.returned_lines == 3


def test_start_alone_reads_to_the_end(big):
    result = Repository(big).read("big.py", start_line=498)
    assert result.returned_lines == 3
    assert result.line_end == 500


def test_end_alone_reads_from_the_top(big):
    result = Repository(big).read("big.py", start_line=None, end_line=2)
    assert result.content == "line1\nline2\n"


def test_no_range_leaves_the_shape_unchanged(big):
    result = Repository(big).read("big.py")
    payload = result.to_dict()
    assert "line_start" not in payload, "the default shape must not change"
    assert result.line_count == 500


def test_a_range_costs_far_less_than_the_whole_file(big):
    whole = Repository(big).read("big.py").character_count
    part = Repository(big).read("big.py", start_line=200, end_line=250).character_count
    assert part < whole / 5


@pytest.mark.parametrize("kwargs", [{"start_line": 0}, {"start_line": -1}, {"start_line": 5, "end_line": 2}])
def test_invalid_ranges_are_rejected(big, kwargs):
    with pytest.raises(LLMScribeError) as excinfo:
        Repository(big).read("big.py", **kwargs)
    assert excinfo.value.code == "invalid_argument"


def test_range_and_compress_are_mutually_exclusive(big):
    """Compression rewrites the file, so line numbers would stop meaning what was asked."""
    with pytest.raises(LLMScribeError) as excinfo:
        Repository(big).read("big.py", start_line=1, end_line=10, compress=True)
    assert excinfo.value.code == "invalid_argument"


def test_range_is_clipped_by_the_character_budget(big):
    result = core.read_file("big.py", big, max_content_chars=20, start_line=1, end_line=100)
    assert result.truncated is True
    assert result.returned_lines == 100, "the range was honoured; the body was clipped"


# ---------------------------------------------------------------- surfaces
def test_cli_lines(big):
    proc = run_cli("read", "big.py", "--lines", "200:202", "--path", str(big))
    assert proc.returncode == 0
    assert "line200" in proc.stdout and "line203" not in proc.stdout
    assert "lines 200-202 of 500" in proc.stdout


def test_cli_open_ended_range(big):
    proc = run_cli("read", "big.py", "--lines", "499:", "--path", str(big))
    assert "line499" in proc.stdout and "line500" in proc.stdout


def test_cli_rejects_a_malformed_range(big):
    proc = run_cli("read", "big.py", "--lines", "abc", "--path", str(big))
    assert proc.returncode != 0
    assert "START:END" in (proc.stderr + proc.stdout)


def test_mcp_and_handlers_expose_the_range(big):
    payload = json.loads(
        tools.read(file_path="big.py", path=str(big), format="json", start_line=200, end_line=202)
    )
    assert payload["data"]["returned_lines"] == 3

    handler = Repository(big).handlers()["read"]
    assert handler(file_path="big.py", start_line=1, end_line=5)["data"]["returned_lines"] == 5


# ---------------------------------------------------------------- read_many
def test_read_many_applies_the_range_to_every_file(big):
    batch = Repository(big).read_many(["big.py", "big.py"], start_line=5, end_line=7)
    assert [item.returned_lines for item in batch.results] == [3, 3]
    assert all(item.content.startswith("line5\n") for item in batch.results)
    assert batch.results[0].line_count == 500


def test_read_many_without_a_range_is_unchanged(big):
    batch = Repository(big).read_many(["big.py"])
    assert batch.results[0].returned_lines == 0
    assert "line_start" not in batch.results[0].to_dict()


def test_cli_read_many_lines(big):
    proc = run_cli("read-many", "big.py", "--lines", "5:7", "--path", str(big))
    assert proc.returncode == 0
    assert "line5" in proc.stdout and "line8" not in proc.stdout
    assert "lines 5-7 of 500" in proc.stdout

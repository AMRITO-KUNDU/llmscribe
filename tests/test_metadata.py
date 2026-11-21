"""File metadata: sizes on map, stat fields on read, opt-in binary reads.

These close the three gaps against `@modelcontextprotocol/server-filesystem`, which
ships `get_file_info`, `list_directory_with_sizes` and `read_media_file`. The
read-only posture is unchanged: binaries are still excluded from overview and
read_many, and only an explicit `binary=True` will decode one.
"""

import base64
import json

import pytest

from llmscribe import Repository, core
from llmscribe.mcp import tools

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    (tmp_path / "pixel.png").write_bytes(PNG)
    return tmp_path


# ---------------------------------------------------------------- sizes
def test_map_sizes_are_opt_in(project):
    assert "sizes" not in core.project_map(project).to_dict(), "default output must not change"
    sizes = core.project_map(project, include_sizes=True).sizes
    assert sizes["src/main.py"] == (project / "src" / "main.py").stat().st_size
    assert sizes["pixel.png"] == len(PNG)


def test_map_sizes_cover_binaries_too(project):
    """A size listing should describe the directory, not just the readable part."""
    sizes = Repository(project).map(include_sizes=True).sizes
    assert "pixel.png" in sizes


# ---------------------------------------------------------------- stat fields
def test_read_reports_stat_fields(project):
    result = Repository(project).read("src/main.py")
    assert result.byte_size == (project / "src" / "main.py").stat().st_size
    assert result.line_count == 2
    assert result.modified.endswith("+00:00"), "modified should be ISO 8601 UTC"
    assert "T" in result.modified


def test_line_count_is_the_whole_file_not_the_clipped_body(project):
    result = Repository(project).read("src/main.py", max_content_chars=4)
    assert result.truncated is True
    assert result.line_count == 2, "line_count must describe the file, not the fragment"


# ---------------------------------------------------------------- binary reads
def test_binary_read_returns_base64_and_media_type(project):
    result = Repository(project).read("pixel.png", binary=True)
    assert result.ok
    assert result.media_type == "image/png"
    assert base64.b64decode(result.content) == PNG
    assert result.byte_size == len(PNG)
    assert result.line_count == 0

    payload = result.to_dict()
    assert payload["base64"] is True and payload["media_type"] == "image/png"
    assert "encoding" not in payload, "a binary payload has no text encoding"


def test_text_read_still_refuses_binaries_by_default(project):
    """The read-only, text-only default must not have loosened."""
    result = Repository(project).read("pixel.png")
    assert result.ok is False
    assert result.error_code == "unsupported_file_type"


def test_binaries_stay_out_of_overview_and_read_many(project):
    overview = Repository(project).overview()
    assert "pixel.png" not in [f["path"] for f in overview.files]

    batch = Repository(project).read_many(["README.md", "pixel.png"])
    assert batch.error_count == 1, "read_many must not silently decode binaries"


# ---------------------------------------------------------------- surfaces
def test_mcp_exposes_sizes_and_binary(project):
    sized = json.loads(tools.project_map(path=str(project), format="json", sizes=True))
    assert sized["data"]["sizes"]["src/main.py"] == (project / "src" / "main.py").stat().st_size

    media = json.loads(tools.read(file_path="pixel.png", path=str(project), format="json", binary=True))
    assert media["data"]["media_type"] == "image/png"

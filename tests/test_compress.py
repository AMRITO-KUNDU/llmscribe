"""`--compress` keeps the shape of a Python file and drops the bodies.

A fixed syntactic transform, not a summary: no inference, no ranking, same output every
time. Files that will not parse are left exactly as they are.
"""

import ast

import pytest

from llmscribe import Repository, core
from llmscribe.core.compress import compress_python

SOURCE = '''
"""Module docstring."""
import os

LIMIT = 10


class Service:
    """Does things."""

    def __init__(self, name):
        """Remember the name."""
        self.name = name
        self._cache = {k: v for k, v in os.environ.items()}

    def run(self, payload):
        result = {}
        for key, value in payload.items():
            result[key] = value * 2 if value > LIMIT else value
        return result


def helper(a, b=3):
    """Adds them."""
    total = a + b
    for i in range(10):
        total += i
    return total
'''


def test_bodies_are_dropped():
    squeezed = compress_python(SOURCE)
    assert squeezed is not None
    assert "for key, value in payload.items()" not in squeezed
    assert "total += i" not in squeezed


def test_shape_is_kept():
    squeezed = compress_python(SOURCE)
    assert "import os" in squeezed
    assert "LIMIT = 10" in squeezed
    assert "class Service:" in squeezed
    assert "def run(self, payload):" in squeezed
    assert "def helper(a, b=3):" in squeezed
    assert '"""Adds them."""' in squeezed
    assert '"""Does things."""' in squeezed


def test_output_is_valid_python():
    ast.parse(compress_python(SOURCE))


def test_it_is_smaller_and_deterministic():
    squeezed = compress_python(SOURCE)
    assert len(squeezed) < len(SOURCE)
    assert compress_python(SOURCE) == squeezed


def test_unparseable_file_is_left_alone():
    assert compress_python("def broken(:\n    pass") is None


# ---------------------------------------------------------------- surfaces
@pytest.fixture
def project(tmp_path):
    (tmp_path / "mod.py").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "notes.md").write_text("# notes\n\n" + "text\n" * 50, encoding="utf-8")
    return tmp_path


def test_overview_reports_what_it_compressed(project):
    result = core.project_overview(project, compress=True)
    assert result.compressed_files == ["mod.py"]
    assert result.to_dict()["compressed_files"] == ["mod.py"]


def test_markdown_files_are_not_compressed(project):
    result = core.project_overview(project, compress=True)
    assert "notes.md" not in result.compressed_files


def test_default_output_is_unchanged(project):
    assert core.project_overview(project).compressed_files == []
    assert "compressed_files" not in core.project_overview(project).to_dict()


def test_compress_and_budget_compose(project):
    """The two features are independent: compress first, then spend the budget."""
    result = core.project_overview(project, compress=True, max_tokens=50)
    assert result.compressed_files == ["mod.py"]
    assert result.truncation_limit == 50 * 4


def test_read_marks_a_compressed_result(project):
    result = Repository(project).read("mod.py", compress=True)
    assert result.compressed is True
    assert "for key, value in payload.items()" not in result.content
    assert result.to_dict()["compressed"] is True
    assert Repository(project).read("mod.py").compressed is False

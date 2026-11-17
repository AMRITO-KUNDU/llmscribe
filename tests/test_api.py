"""Tests for the public Python API — ``from llmscribe import Repository``."""

import pytest

import llmscribe
from llmscribe import LLMScribeError, Repository, core


def test_public_api_is_importable():
    assert isinstance(llmscribe.__version__, str) and llmscribe.__version__
    assert Repository.__name__ == "Repository"
    assert issubclass(LLMScribeError, Exception)
    assert set(llmscribe.__all__) == {"LLMScribeError", "Repository", "__version__"}
    # the lazy module __getattr__ must reject unknown names properly
    with pytest.raises(AttributeError):
        llmscribe.does_not_exist  # noqa: B018


def test_importing_the_package_stays_cheap():
    """``import llmscribe`` must not pull in the core (~200ms)."""
    import subprocess
    import sys

    code = "import sys, llmscribe; print('llmscribe.core' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.stdout.strip() == "False", "core was imported eagerly"


def test_repository_delegates_to_core(repo):
    root = repo
    api = Repository(root)

    assert api.root == root
    assert repr(api) == f"Repository({str(root)!r})"

    assert api.map().files == core.project_map(root).files
    assert api.search("needle").match_count == core.search_project("needle", root).match_count
    assert api.read("README.md").content == core.read_file("README.md", root).content


def test_read_returns_errors_instead_of_raising(repo):
    api = Repository(repo)

    missing = api.read("nope.py")
    assert missing.ok is False and missing.error_code == "file_not_found"

    batch = api.read_many(["README.md", "nope.py"])
    assert batch.file_count == 2 and batch.success_count == 1 and batch.error_count == 1


def test_dependencies_raises_with_a_stable_code(repo):
    api = Repository(repo)

    with pytest.raises(LLMScribeError) as excinfo:
        api.dependencies("nope.py")
    assert excinfo.value.code == "file_not_found"

    deps = api.dependencies("src/pkg/a.py")
    assert "src/pkg/b.py" in deps.file_dependencies.local_dependencies


def test_diff_raises_outside_a_git_repository(repo):
    api = Repository(repo)
    with pytest.raises(LLMScribeError):
        api.diff()


def test_ignore_patterns_are_passed_through(repo):
    plain = Repository(repo).map()
    assert "README.md" in plain.files

    filtered = Repository(repo, ignore_patterns=["*.md"]).map()
    assert "README.md" not in filtered.files

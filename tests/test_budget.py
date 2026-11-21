"""`--max-tokens` spends a context budget in a fixed order.

The rule that makes this safe: files are taken in path order until the budget is gone.
Never by relevance, likelihood or importance — that would be ranking, which is the one
thing this project exists not to do.
"""

import json

import pytest

from llmscribe import LLMScribeError, Repository, core
from llmscribe.core.limits import CHARS_PER_TOKEN, MAX_CONTENT_CHARS
from llmscribe.mcp import tools


@pytest.fixture
def project(tmp_path):
    for index in range(6):
        (tmp_path / f"file{index}.py").write_text(f"# file {index}\n" + "x = 1\n" * 40, encoding="utf-8")
    return tmp_path


def test_budget_is_spent_in_characters(project):
    result = core.project_overview(project, max_tokens=100)
    assert result.truncation_limit == 100 * CHARS_PER_TOKEN


def test_budget_stops_the_read(project):
    full = core.project_overview(project)
    small = core.project_overview(project, max_tokens=20)
    assert small.omitted_files, "a small budget must report what it skipped"
    assert len(small.files) < len(full.files)


def test_budget_is_deterministic(project):
    """Same budget, same files, every time — no ranking, no tie-breaking."""
    first = [f["path"] for f in core.project_overview(project, max_tokens=60).files]
    second = [f["path"] for f in core.project_overview(project, max_tokens=60).files]
    assert first == second
    assert first == sorted(first), "files must arrive in path order"


def test_budget_must_be_positive(project):
    with pytest.raises(LLMScribeError) as excinfo:
        core.project_overview(project, max_tokens=0)
    assert excinfo.value.code == "invalid_argument"


def test_no_budget_is_unchanged(project):
    assert core.project_overview(project).truncation_limit == MAX_CONTENT_CHARS


def test_surfaces_accept_a_budget(project):
    sdk = Repository(project).overview(max_tokens=20)
    assert sdk.truncation_limit == 20 * CHARS_PER_TOKEN

    payload = json.loads(
        tools.project_overview(path=str(project), format="json", max_tokens=20)
    )
    assert payload["data"]["truncation_limit"] == 20 * CHARS_PER_TOKEN

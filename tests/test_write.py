"""Write operations: create, edit, move, delete.

The read side has always refused to escape the project root. Writes must be held to the
same standard, because a write that lands outside the root is far worse than a read that
does: it damages something the user never pointed at.
"""

import json
import os
import subprocess
import sys

import pytest

from llmscribe import Repository
from llmscribe.mcp import tools


@pytest.fixture
def project(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
    return tmp_path


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "llmscribe", *args], capture_output=True, text=True, cwd=cwd
    )


# ---------------------------------------------------------------- write_file
def test_creates_a_file(project):
    result = Repository(project).write_file("new.py", "z = 3\n")
    assert result.action == "created"
    assert result.existed is False
    assert (project / "new.py").read_text(encoding="utf-8") == "z = 3\n"


def test_overwrites_and_reports_it(project):
    result = Repository(project).write_file("a.py", "replaced\n")
    assert result.action == "overwritten" and result.existed is True
    assert (project / "a.py").read_text(encoding="utf-8") == "replaced\n"


def test_refuses_to_clobber_when_asked(project):
    result = Repository(project).write_file("a.py", "nope\n", overwrite=False)
    assert result.ok is False and result.error_code == "file_exists"
    assert (project / "a.py").read_text(encoding="utf-8") == "x = 1\ny = 2\n"


def test_write_leaves_no_temporary_file(project):
    Repository(project).write_file("new.py", "z = 3\n")
    leftovers = [p.name for p in project.iterdir() if "llmscribe-tmp" in p.name]
    assert leftovers == []


def test_newlines_are_written_verbatim(project):
    """Bytes are encoded explicitly, so a Windows run does not turn \\n into \\r\\n."""
    Repository(project).write_file("nl.py", "a\nb\n")
    assert (project / "nl.py").read_bytes() == b"a\nb\n"


# ---------------------------------------------------------------- edit_file
def test_edits_one_exact_match(project):
    result = Repository(project).edit_file("a.py", "y = 2", "y = 99")
    assert result.action == "edited" and result.replacements == 1
    assert (project / "a.py").read_text(encoding="utf-8") == "x = 1\ny = 99\n"


def test_missing_text_is_reported_not_ignored(project):
    result = Repository(project).edit_file("a.py", "not here", "x")
    assert result.ok is False and result.error_code == "no_match"


def test_ambiguous_text_requires_replace_all(project):
    (project / "dup.py").write_text("v = 1\nv = 1\n", encoding="utf-8")
    ambiguous = Repository(project).edit_file("dup.py", "v = 1", "v = 2")
    assert ambiguous.ok is False and ambiguous.error_code == "ambiguous_match"

    all_of_them = Repository(project).edit_file("dup.py", "v = 1", "v = 2", replace_all=True)
    assert all_of_them.replacements == 2
    assert (project / "dup.py").read_text(encoding="utf-8") == "v = 2\nv = 2\n"


def test_empty_old_text_is_rejected(project):
    result = Repository(project).edit_file("a.py", "", "x")
    assert result.ok is False and result.error_code == "invalid_argument"


# ---------------------------------------------------------------- directories, move, delete
def test_creates_nested_directories(project):
    result = Repository(project).create_directory("pkg/sub")
    assert result.action == "directory_created"
    assert (project / "pkg" / "sub").is_dir()


def test_create_directory_is_idempotent(project):
    repo = Repository(project)
    repo.create_directory("pkg")
    assert repo.create_directory("pkg").action == "directory_exists"


def test_moves_a_file(project):
    result = Repository(project).move_file("a.py", "moved.py")
    assert result.action == "moved" and result.destination == "moved.py"
    assert not (project / "a.py").exists()
    assert (project / "moved.py").exists()


def test_move_refuses_to_clobber(project):
    (project / "b.py").write_text("keep\n", encoding="utf-8")
    result = Repository(project).move_file("a.py", "b.py")
    assert result.ok is False and result.error_code == "file_exists"
    assert (project / "b.py").read_text(encoding="utf-8") == "keep\n"


def test_deletes_a_file(project):
    assert Repository(project).delete_file("a.py").action == "deleted"
    assert not (project / "a.py").exists()


def test_delete_refuses_a_directory(project):
    (project / "pkg").mkdir()
    result = Repository(project).delete_file("pkg")
    assert result.ok is False


# ---------------------------------------------------------------- safety
@pytest.mark.parametrize(
    "target",
    ["../outside.py", "../../etc/passwd", "/tmp/outside.py", "a/../../outside.py", "..\\outside.py", "%2e%2e/outside.py"],
)
def test_writes_cannot_escape_the_root(project, target):
    result = Repository(project).write_file(target, "pwned\n")
    assert result.ok is False
    assert result.error_code in {"invalid_path", "invalid_argument"}
    assert not (project.parent / "outside.py").exists()


def test_writes_refuse_to_follow_a_symlink_out(project, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "secret.py"
    outside.write_text("original\n", encoding="utf-8")
    os.symlink(outside, project / "link.py")

    result = Repository(project).write_file("link.py", "pwned\n")
    assert result.ok is False and result.error_code == "invalid_path"
    assert outside.read_text(encoding="utf-8") == "original\n", "the symlink target was modified"


def test_write_requires_an_existing_parent(project):
    result = Repository(project).write_file("missing/deep/file.py", "x\n")
    assert result.ok is False and result.error_code == "invalid_path"


def test_secrets_are_written_verbatim_not_redacted(project):
    """Redaction protects what leaves; it must never alter what is stored."""
    Repository(project).write_file("cfg.py", 'KEY = "AK' + 'IA' + 'IOSFODNN7EXAMPLE"\n')
    assert "AKIA" in (project / "cfg.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------- surfaces
def test_cli_write_edit_and_delete(project):
    assert run_cli("write", "c.py", "--content", "v = 1", "--path", str(project)).returncode == 0
    assert (project / "c.py").read_text(encoding="utf-8") == "v = 1"

    assert run_cli("edit", "c.py", "--old", "v = 1", "--new", "v = 2", "--path", str(project)).returncode == 0
    assert (project / "c.py").read_text(encoding="utf-8") == "v = 2"

    assert run_cli("rm", "c.py", "--path", str(project)).returncode == 0
    assert not (project / "c.py").exists()


def test_cli_write_reads_stdin(project):
    proc = subprocess.run(
        [sys.executable, "-m", "llmscribe", "write", "piped.py", "--path", str(project)],
        input="from_stdin = True\n", capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert (project / "piped.py").read_text(encoding="utf-8") == "from_stdin = True\n"


def test_mcp_exposes_the_write_tools(project):
    payload = json.loads(
        tools.write_file(file_path="m.py", content="m = 1\n", path=str(project), format="json")
    )
    assert payload["ok"] is True and payload["data"]["action"] == "created"

    edited = json.loads(
        tools.edit_file(
            file_path="m.py", old_text="m = 1", new_text="m = 2", path=str(project), format="json"
        )
    )
    assert edited["data"]["replacements"] == 1


def test_handlers_can_write(project):
    handler = Repository(project).handlers()["write_file"]
    assert handler(file_path="h.py", content="h = 1\n")["data"]["action"] == "created"

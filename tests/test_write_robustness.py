"""Failure modes that lose work, not just return an error.

Each of these is a way an agent damages something without noticing: overwriting a change
made after it read the file, clobbering a file someone made read-only, or leaving a
half-written file behind. The write path is new, so these are the cases worth pinning.
"""

import errno
import os
import stat

import pytest

from llmscribe import Repository
from llmscribe.core.write_ops import _explain_oserror

POSIX_ONLY = pytest.mark.skipif(os.name == "nt", reason="chmod semantics differ on Windows")
NOT_ROOT = pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores file permissions"
)


# ---------------------------------------------------------------- lost update
def test_a_stale_revision_is_refused(tmp_path):
    """The file changed after the agent read it: refuse rather than overwrite."""
    path = tmp_path / "a.py"
    path.write_text("x = 1\n", encoding="utf-8")
    repo = Repository(tmp_path)
    revision = repo.read("a.py").revision

    path.write_text("x = 99\n", encoding="utf-8")  # someone else edits it
    result = repo.edit_file("a.py", "x = 1", "x = 2", expect_revision=revision)

    assert result.ok is False and result.error_code == "conflict"
    assert path.read_text(encoding="utf-8") == "x = 99\n", "the other change survived"


def test_a_matching_revision_is_accepted(tmp_path):
    path = tmp_path / "a.py"
    path.write_text("x = 1\n", encoding="utf-8")
    repo = Repository(tmp_path)
    result = repo.edit_file("a.py", "x = 1", "x = 2", expect_revision=repo.read("a.py").revision)
    assert result.ok and path.read_text(encoding="utf-8") == "x = 2\n"


def test_write_file_honours_the_revision_too(tmp_path):
    path = tmp_path / "a.py"
    path.write_text("v = 1\n", encoding="utf-8")
    repo = Repository(tmp_path)
    revision = repo.read("a.py").revision
    path.write_text("v = 2\n", encoding="utf-8")
    result = repo.write_file("a.py", "v = 3\n", expect_revision=revision)
    assert result.ok is False and result.error_code == "conflict"
    assert path.read_text(encoding="utf-8") == "v = 2\n"


def test_read_reports_a_revision_for_every_file(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("x = 1\n", encoding="utf-8")
    repo = Repository(tmp_path)
    first, second = repo.read("a.py").revision, repo.read("b.py").revision
    assert first and second and first == second, "same bytes, same revision"
    (tmp_path / "b.py").write_text("x = 2\n", encoding="utf-8")
    assert repo.read("b.py").revision != first


# ---------------------------------------------------------------- permissions
@POSIX_ONLY
@NOT_ROOT
def test_a_read_only_file_is_not_overwritten(tmp_path):
    path = tmp_path / "ro.py"
    path.write_text("v = 1\n", encoding="utf-8")
    os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    try:
        repo = Repository(tmp_path)
        assert repo.edit_file("ro.py", "v = 1", "v = 2").error_code == "permission_denied"
        assert repo.write_file("ro.py", "v = 9\n").error_code == "permission_denied"
        assert path.read_text(encoding="utf-8") == "v = 1\n"
    finally:
        os.chmod(path, 0o644)


@POSIX_ONLY
@NOT_ROOT
def test_a_read_only_directory_refuses_writes(tmp_path):
    directory = tmp_path / "locked"
    directory.mkdir()
    (directory / "f.py").write_text("w = 1\n", encoding="utf-8")
    os.chmod(directory, 0o555)
    try:
        result = Repository(tmp_path).write_file("locked/f.py", "w = 2\n")
        assert result.ok is False and result.error_code == "permission_denied"
    finally:
        os.chmod(directory, 0o755)


@POSIX_ONLY
@NOT_ROOT
def test_a_failed_write_leaves_no_temporary_file(tmp_path):
    directory = tmp_path / "locked"
    directory.mkdir()
    (directory / "f.py").write_text("w = 1\n", encoding="utf-8")
    os.chmod(directory, 0o555)
    try:
        Repository(tmp_path).write_file("locked/f.py", "w = 2\n")
    finally:
        os.chmod(directory, 0o755)
    assert [p for p in tmp_path.rglob("*llmscribe-tmp*")] == []


# ---------------------------------------------------------------- errno mapping
@pytest.mark.parametrize(
    "exc,code",
    [
        (OSError(errno.ENOSPC, "No space left on device"), "no_space"),
        (OSError(errno.ENAMETOOLONG, "File name too long"), "path_too_long"),
        (OSError(errno.EXDEV, "Invalid cross-device link"), "write_error"),
        (OSError(errno.EACCES, "Permission denied"), "permission_denied"),
        (OSError(errno.EROFS, "Read-only file system"), "permission_denied"),
        (OSError(errno.EISDIR, "Is a directory"), "invalid_path"),
    ],
)
def test_errno_becomes_an_actionable_code(exc, code):
    assert _explain_oserror(exc, "src/a.py", "write").code == code


def test_windows_error_codes_are_mapped():
    """Windows reports winerror rather than errno for these."""
    for winerror, code in ((206, "path_too_long"), (112, "no_space"), (5, "permission_denied")):
        exc = OSError(0, "windows")
        exc.winerror = winerror
        assert _explain_oserror(exc, "a.py", "write").code == code


def test_a_disk_full_message_says_the_original_is_safe():
    message = _explain_oserror(OSError(errno.ENOSPC, "No space"), "a.py", "write").message
    assert "not changed" in message


def test_a_long_path_message_mentions_the_windows_limit():
    message = _explain_oserror(OSError(errno.ENAMETOOLONG, "too long"), "a.py", "write").message
    assert "260" in message

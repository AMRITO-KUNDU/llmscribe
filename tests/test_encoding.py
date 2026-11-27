"""Encoding behaviour across read, write and diff.

Two failure modes matter here. Silently *changing* a file's encoding when it is edited,
and silently *hiding* bytes the decoder could not map. Both make an agent believe
something about a file that is not true.
"""

import codecs
import os
import subprocess

import pytest

from llmscribe import Repository

# 0x81 has no mapping in cp1252, so decoding substitutes U+FFFD
UNDECODABLE = b"x = '\x81'\ny = 2\n"


@pytest.fixture
def project(tmp_path):
    return tmp_path


# ---------------------------------------------------------------- read
def test_read_reports_the_encoding(project):
    (project / "latin.py").write_bytes("# café\n".encode("cp1252"))
    (project / "wide.py").write_bytes("# café\n".encode("utf-16"))
    repo = Repository(project)
    assert repo.read("latin.py").encoding == "cp1252"
    assert repo.read("wide.py").encoding == "utf-16"
    assert "café" in repo.read("latin.py").content


def test_read_flags_bytes_the_decoder_could_not_map(project):
    (project / "weird.py").write_bytes(UNDECODABLE)
    result = Repository(project).read("weird.py")
    assert result.replaced_bytes == 1
    assert result.to_dict()["lossy"] is True


def test_a_clean_cp1252_file_is_not_flagged(project):
    (project / "latin.py").write_bytes("# café\n".encode("cp1252"))
    assert "lossy" not in Repository(project).read("latin.py").to_dict()


def test_overview_lists_lossy_files_only(project):
    (project / "weird.py").write_bytes(UNDECODABLE)
    (project / "latin.py").write_bytes("# café\n".encode("cp1252"))
    payload = Repository(project).overview().to_dict()
    assert payload["lossy_files"] == ["weird.py"]


# ---------------------------------------------------------------- diff
def test_diff_decodes_a_cp1252_file(project):
    """Git does not transcode; decoding its output as UTF-8 turned café into U+FFFD."""
    # Inherit the environment and add an identity. Replacing it outright leaves Windows
    # without SystemRoot, and CreateProcess hangs rather than failing.
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "a",
        "GIT_AUTHOR_EMAIL": "a@b",
        "GIT_COMMITTER_NAME": "a",
        "GIT_COMMITTER_EMAIL": "a@b",
    }
    subprocess.run(["git", "init", "-q"], cwd=project, check=True, env=env)
    (project / "a.py").write_bytes("# café\nx = 1\n".encode("cp1252"))
    subprocess.run(["git", "add", "-A"], cwd=project, check=True, env=env)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=project, check=True, env=env)
    (project / "a.py").write_bytes("# café\nx = 2\n".encode("cp1252"))

    diff = Repository(project).diff().diff
    assert "café" in diff
    assert "\ufffd" not in diff


# ---------------------------------------------------------------- round trip
def test_read_then_write_preserves_encoding(project):
    path = project / "latin.py"
    path.write_bytes("# café\nx = 1\n".encode("cp1252"))
    repo = Repository(project)
    text = repo.read("latin.py").content
    repo.write_file("latin.py", text.replace("x = 1", "x = 2"))
    assert path.read_bytes() == "# café\nx = 2\n".encode("cp1252"), "the round trip changed the encoding"


def test_read_then_write_preserves_a_bom(project):
    path = project / "bom.py"
    path.write_bytes(codecs.BOM_UTF8 + b"x = 1\n")
    repo = Repository(project)
    repo.write_file("bom.py", repo.read("bom.py").content)
    assert path.read_bytes().startswith(codecs.BOM_UTF8)

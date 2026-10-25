import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A small real project on disk."""
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src/pkg/__init__.py").write_text("")
    (tmp_path / "src/pkg/a.py").write_text("import os\nimport requests\nfrom . import b\nfrom .missing import z\n")
    (tmp_path / "src/pkg/b.py").write_text("def f():\n    return 'needle'\n")
    (tmp_path / "README.md").write_text("# Demo\nNeedle here\n")
    (tmp_path / "Dockerfile").write_text("FROM scratch\n")
    (tmp_path / ".gitignore").write_text("*.cfg\n!keep.cfg\nbuild/\n/root.txt\n")
    (tmp_path / "x.cfg").write_text("ignored")
    (tmp_path / "keep.cfg").write_text("kept")
    (tmp_path / "root.txt").write_text("root ignored")
    (tmp_path / "src/root.txt").write_text("nested file kept")
    (tmp_path / "build").mkdir()
    (tmp_path / "build/out.py").write_text("ignored")
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01\x02")
    return tmp_path


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout

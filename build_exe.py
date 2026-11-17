"""Build the standalone Windows GUI executable with PyInstaller.

Run on Windows from the repository root after ``pip install ".[gui]" pyinstaller``:

    python build_exe.py

Output: ``dist/LLMScribe-GUI.exe`` plus ``dist/LLMScribe-GUI.exe.sha256``.
The version is read from the installed/checked-out package, never hard-coded.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT_DIR / "src"))

from llmscribe import __version__  # noqa: E402

ENTRY_POINT = ROOT_DIR / "src" / "llmscribe" / "gui" / "app.py"
ICON_PATH = ROOT_DIR / "docs" / "public" / "favicon.ico"
NAME = "LLMScribe-GUI"


def build_command() -> list[str]:
    """The PyInstaller command line.

    ``--icon`` sets the icon on the .exe file; ``--add-data`` ships the same file
    inside the bundle so the running window can set its own icon too. The separator
    differs per platform, hence ``os.pathsep``.
    """
    return [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", NAME,
        "--paths", str(ROOT_DIR / "src"),
        "--collect-all", "customtkinter",
        "--exclude-module", "pytest",
        "--icon", str(ICON_PATH),
        "--add-data", f"{ICON_PATH}{os.pathsep}docs{os.sep}public",
        str(ENTRY_POINT),
    ]


def build() -> Path:
    if not ICON_PATH.is_file():
        raise SystemExit(f"icon missing: {ICON_PATH.relative_to(ROOT_DIR)} (a release must not ship without it)")
    for folder in ("build", "dist"):
        shutil.rmtree(ROOT_DIR / folder, ignore_errors=True)
    cmd = build_command()
    print(f"Building LLMScribe {__version__} GUI executable...")
    subprocess.run(cmd, cwd=ROOT_DIR, check=True)

    exe = ROOT_DIR / "dist" / f"{NAME}.exe"
    if not exe.is_file():
        raise SystemExit(f"Build finished but {exe} was not produced.")
    digest = hashlib.sha256(exe.read_bytes()).hexdigest()
    (exe.parent / f"{exe.name}.sha256").write_text(f"{digest}  {exe.name}\n", encoding="utf-8")
    print(f"OK: {exe} ({exe.stat().st_size / 1_048_576:.1f} MB) sha256={digest}")
    return exe


if __name__ == "__main__":
    build()

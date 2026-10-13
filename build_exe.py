"""Build the standalone Windows GUI executable with PyInstaller.

Run on Windows from the repository root after ``pip install ".[gui]" pyinstaller``:

    python build_exe.py

Output: ``dist/LLMScribe-GUI.exe`` plus ``dist/LLMScribe-GUI.exe.sha256``.
The version is read from the installed/checked-out package, never hard-coded.
"""

from __future__ import annotations

import hashlib
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


def build() -> Path:
    for folder in ("build", "dist"):
        shutil.rmtree(ROOT_DIR / folder, ignore_errors=True)
    cmd = [
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", NAME,
        "--paths", str(ROOT_DIR / "src"),
        "--collect-all", "customtkinter",
        "--exclude-module", "pytest",
    ]
    if ICON_PATH.exists():
        cmd += ["--icon", str(ICON_PATH)]
    cmd.append(str(ENTRY_POINT))
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

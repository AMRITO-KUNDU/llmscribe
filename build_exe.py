"""Build script for packaging LLMScribe GUI into a standalone Windows executable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.resolve()
ENTRY_POINT = ROOT_DIR / "src" / "llmscribe" / "gui" / "app.py"
ICON_PATH = ROOT_DIR / "docs" / "public" / "favicon.ico"


def build() -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "LLMScribe-GUI",
        "--icon",
        str(ICON_PATH) if ICON_PATH.exists() else "NONE",
        "--paths",
        str(ROOT_DIR / "src"),
        "--collect-all",
        "customtkinter",
        str(ENTRY_POINT),
    ]
    print("Building standalone executable with PyInstaller...")
    print("Command:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT_DIR, check=True)

    exe_path = ROOT_DIR / "dist" / "LLMScribe-GUI.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\nSUCCESS: Standalone executable created at: {exe_path} ({size_mb:.2f} MB)")
    else:
        print("\nBuild completed but executable was not found in dist/")


if __name__ == "__main__":
    build()
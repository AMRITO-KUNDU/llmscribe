"""Command text user interface for LLMScribe - thin wrapper around CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def pick_folder_gui() -> Path | None:
    """Load the optional GUI folder picker."""
    try:
        from llmscribe.gui.app import pick_folder_gui
        return pick_folder_gui()
    except ImportError as exc:
        raise RuntimeError(
            "GUI mode requires Tkinter. Install your OS Python Tk package "
            "(for example, python3-tk on Debian/Ubuntu)."
        ) from exc


def main() -> None:
    """Run the LLMScribe CUI as a thin wrapper around CLI."""
    print("LLMScribe CUI (thin wrapper around CLI)")
    print("=" * 50)
    
    # For now, just delegate to CLI
    print("Redirecting to CLI interface...")
    print("Use: llmscribe <command> [options]")
    print("Available commands: map, overview, search, read, read-many, dependencies, diff")
    
    # Run the CLI
    try:
        import subprocess
        import sys
        result = subprocess.run([sys.executable, "-m", "llmscribe.cli.main", "--help"], 
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
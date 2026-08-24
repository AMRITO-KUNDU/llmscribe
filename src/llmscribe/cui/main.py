"""Command text user interface for LLMScribe."""

from __future__ import annotations

import argparse
from pathlib import Path

from llmscribe.core.writer import run


def parse_args() -> argparse.Namespace:
    """Parse command text interface arguments."""
    parser = argparse.ArgumentParser(prog="llmscribe-cui", description="LLMScribe command text interface")
    parser.add_argument("--path", help="Project folder path")
    parser.add_argument("--output", help="Output file", default="project_overview.txt")
    parser.add_argument("--gui", action="store_true", help="Use GUI folder picker")
    parser.add_argument("--tree-only", action="store_true", help="Export only the directory tree.")
    parser.add_argument("--version", action="version", version=_version_string())
    return parser.parse_args()


def _version_string() -> str:
    from llmscribe import __version__

    return f"llmscribe-cui {__version__}"


def choose_project_path(args: argparse.Namespace) -> Path | None:
    """Choose a project path from flags, GUI mode, or the text menu."""
    if args.gui:
        return _pick_folder_gui()

    if args.path:
        return Path(args.path).expanduser()

    return prompt_for_project_path()


def prompt_for_project_path() -> Path | None:
    """Prompt users in a command text window for how they want to select a project."""
    while True:
        print("\nLLMScribe CUI")
        print("1) Enter project folder path")
        print("2) Open GUI folder picker")
        print("3) Quit")

        choice = input("Choose an option [1-3]: ").strip()

        if choice == "1":
            user_input = input("Project folder path: ").strip()
            return Path(user_input).expanduser() if user_input else None

        if choice == "2":
            return _pick_folder_gui()

        if choice == "3":
            return None

        print("Invalid option. Please enter 1, 2, or 3.")


def _pick_folder_gui() -> Path | None:
    """Load the optional GUI only when the user requests it."""
    try:
        from llmscribe.gui.app import pick_folder_gui
    except ImportError as exc:
        raise RuntimeError(
            "GUI mode requires Tkinter. Install your OS Python Tk package "
            "(for example, python3-tk on Debian/Ubuntu)."
        ) from exc
    return pick_folder_gui()


def main() -> None:
    """Run the LLMScribe command text user interface."""
    args = parse_args()
    try:
        project_path = choose_project_path(args)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        return

    if project_path is None:
        print("No folder selected.")
        return

    if not project_path.exists() or not project_path.is_dir():
        print("Invalid project folder path.")
        return

    try:
        run(project_path.resolve(), Path(args.output).expanduser(), tree_only=args.tree_only)
    except OSError as exc:
        print(f"Error: could not read or write files: {exc}")


if __name__ == "__main__":
    main()

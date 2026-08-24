"""Command-line entry point for LLMScribe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from llmscribe.core.writer import run


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="llmscribe",
        description="LLMScribe — export a project folder to a single text file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--path",
        help="Project folder path.",
    )

    parser.add_argument(
        "--output",
        help="Output file path.",
        default="project_overview.txt",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Open a GUI folder picker instead of typing a path.",
    )

    parser.add_argument(
        "--tree-only",
        action="store_true",
        help="Export only the directory tree without file contents.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=_version_string(),
    )

    return parser.parse_args()


def _version_string() -> str:
    from llmscribe import __version__

    return f"llmscribe {__version__}"


def resolve_project_path(args: argparse.Namespace) -> Path | None:
    """Resolve the project path from CLI flags, GUI picker, or interactive prompt."""
    if args.gui:
        return _pick_folder_gui()

    if args.path:
        return Path(args.path).expanduser()

    user_input = input(
        "Enter project folder path (or press Enter to open folder picker): "
    ).strip()

    if user_input:
        return Path(user_input).expanduser()

    return _pick_folder_gui()


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
    """Run the LLMScribe CLI."""
    args = parse_args()
    try:
        project_path = resolve_project_path(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if project_path is None:
        print("No folder selected. Exiting.")
        sys.exit(0)

    if not project_path.exists():
        print(f"Error: path does not exist: {project_path}")
        sys.exit(1)

    if not project_path.is_dir():
        print(f"Error: path is not a directory: {project_path}")
        sys.exit(1)

    try:
        run(
            project_path.resolve(),
            Path(args.output).expanduser(),
            tree_only=args.tree_only,
        )
    except OSError as exc:
        print(f"Error: could not read or write files: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

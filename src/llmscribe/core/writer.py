"""Write LLMScribe project summaries."""

from __future__ import annotations

from pathlib import Path

from .file_reader import extract_contents
from .tree_builder import DEFAULT_IGNORE, generate_tree, load_gitignore


def build_project_summary(project_path: Path, tree_only: bool = False) -> str:
    """Build the full project summary text for a project path.

    Args:
        project_path: Resolved path to the project root.
        tree_only:    Export only the directory tree, skipping file contents.
    """
    ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(project_path)]

    tree = generate_tree(project_path, ignore_patterns)

    if tree_only:
        return f"Selected Files Directory Structure:\n\n{tree}"

    contents = extract_contents(project_path, ignore_patterns)

    return (
        f"Selected Files Directory Structure:\n\n"
        f"{tree}\n\n"
        f"File Contents:\n{contents}"
    )


def run(project_path: Path, output_file: Path, tree_only: bool = False) -> None:
    """Generate and write a project summary file.

    Args:
        project_path: Resolved path to the project root.
        output_file:  Destination file for the summary.
        tree_only:    Export only the directory tree, skipping file contents.
    """
    print(f"\nScanning {project_path.name}...\n")

    summary = build_project_summary(project_path, tree_only=tree_only)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(summary, encoding="utf-8")

    line_count = summary.count("\n")
    print(f"Done. {line_count:,} lines written to: {output_file}\n")

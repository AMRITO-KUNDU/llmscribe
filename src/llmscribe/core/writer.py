"""Compatibility wrapper for legacy writer APIs.

This module remains available for backwards compatibility, but the actual
project export logic now lives in the core project result types and the
public project_* helpers.
"""

from __future__ import annotations

from pathlib import Path

from .project import project_map, project_overview
from .tree_builder import DEFAULT_IGNORE, generate_tree, load_gitignore


def build_project_summary(project_path: Path, tree_only: bool = False) -> str:
    """Backward-compatible summary builder.

    Prefer the deterministic project_map/project_overview helpers from
    ``llmscribe.core`` for new code.
    """
    root = project_path.resolve()
    ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
    tree = generate_tree(root, ignore_patterns)

    if tree_only:
        return f"Selected Files Directory Structure:\n\n{tree}"

    overview = project_overview(root, ignore_patterns=ignore_patterns)
    return (
        f"Selected Files Directory Structure:\n\n"
        f"{tree}\n\n"
        f"File Contents:\n"
        + "\n\n".join(f"--- {entry['path']} ---\n{entry['content']}" for entry in overview.files)
    )


def run(project_path: Path, output_file: Path, tree_only: bool = False) -> None:
    """Generate and write a project summary file for legacy consumers."""
    print(f"\nScanning {project_path.name}...\n")
    summary = build_project_summary(project_path, tree_only=tree_only)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(summary, encoding="utf-8")
    line_count = summary.count("\n")
    print(f"Done. {line_count:,} lines written to: {output_file}\n")

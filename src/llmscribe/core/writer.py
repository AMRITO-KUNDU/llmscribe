"""Plain-text project export used by the GUI.

``build_project_summary`` renders the tree (and, unless ``tree_only``, the
contents of every supported text file) as one text document. It is built on
``project_map`` / ``project_overview`` and bounded by the same limits.
"""

from __future__ import annotations

from pathlib import Path

from .project import project_map, project_overview


def build_project_summary(project_path: Path, tree_only: bool = False) -> str:
    """Return the text export for ``project_path`` (raises ``LLMScribeError`` for a bad path)."""
    if tree_only:
        result = project_map(project_path)
        text = f"Selected Files Directory Structure:\n\n{result.tree}"
        return text + (f"\n\n[{result.truncation_note}]" if result.truncated else "")
    overview = project_overview(project_path)
    contents = "\n\n".join(f"--- {entry['path']} ---\n{entry['content']}" for entry in overview.files)
    text = f"Selected Files Directory Structure:\n\n{overview.tree}\n\nFile Contents:\n{contents}"
    return text + (f"\n\n[{overview.truncation_note}]" if overview.truncated else "")

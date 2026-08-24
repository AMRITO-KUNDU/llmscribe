"""Read supported text files for project summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .tree_builder import IgnoreMatcher

TEXT_FILE_EXTENSIONS = {
    # Programming Languages
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp",
    ".go", ".rb", ".rs", ".php", ".scala", ".kt", ".swift", ".dart", ".lua", ".pl", ".pm",
    ".r", ".m", ".hs", ".ml", ".fs", ".fsx", ".vb", ".cs", ".clj", ".cljs", ".elm", ".ex",
    ".exs", ".nim", ".zig", ".cr", ".d", ".nimble", ".v", ".pony", ".tcl", ".tk",
    # Web Technologies
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte", ".pug", ".ejs",
    ".hbs", ".handlebars", ".mustache", ".twig", ".jsp", ".asp", ".aspx", ".erb", ".haml",
    # Configuration & Data
    ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties",
    ".env", ".dotenv", ".lock", ".sum", ".mod", ".gradle", ".pom",
    ".gitignore", ".gitattributes", ".editorconfig", ".prettierrc", ".eslintrc", ".babelrc",
    # Scripts & Shell
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd", ".awk", ".sed",
    # Documentation & plain text
    ".md", ".rst", ".adoc", ".tex", ".bib", ".txt",
    # Data (text-based only)
    ".csv", ".tsv", ".sql",
    # Logs
    ".log",
}


def is_text_file(path: Path) -> bool:
    """Return True when a path has a supported text-like extension."""
    return path.suffix.lower() in TEXT_FILE_EXTENSIONS


def extract_contents(root: Path, ignore_patterns: Iterable[str]) -> str:
    """Extract full contents from every supported text file below root.

    Args:
        root:            Project root directory.
        ignore_patterns: Patterns passed to should_ignore.
    """
    output: list[str] = []
    matcher = IgnoreMatcher(root, ignore_patterns)

    for path in sorted(root.rglob("*")):
        if path.is_dir() or matcher.is_ignored(path) or not is_text_file(path):
            continue

        rel = path.relative_to(root)
        output.append(f"\n--- {rel} ---\n")

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            output.append(f"[Error reading file: {exc}]\n")
            continue

        output.append(content)

    return "".join(output)

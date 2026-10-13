"""Text-file detection and decoding shared by every read path."""

from __future__ import annotations

import codecs
from pathlib import Path, PurePosixPath
from typing import Iterable

from .errors import LLMScribeError

TEXT_FILE_EXTENSIONS = {
    # Programming languages
    ".py", ".js", ".mjs", ".cjs", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cc", ".cxx",
    ".h", ".hpp", ".go", ".rb", ".rs", ".php", ".scala", ".kt", ".swift", ".dart", ".lua",
    ".pl", ".pm", ".r", ".m", ".hs", ".ml", ".fs", ".fsx", ".vb", ".cs", ".clj", ".cljs",
    ".elm", ".ex", ".exs", ".nim", ".zig", ".cr", ".d", ".nimble", ".v", ".pony", ".tcl", ".tk",
    # Web
    ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte", ".pug", ".ejs",
    ".hbs", ".handlebars", ".mustache", ".twig", ".jsp", ".asp", ".aspx", ".erb", ".haml",
    # Configuration and data
    ".json", ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties",
    ".env", ".dotenv", ".lock", ".sum", ".mod", ".gradle", ".pom",
    # Shell
    ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd", ".awk", ".sed",
    # Documentation and plain text
    ".md", ".rst", ".adoc", ".tex", ".bib", ".txt",
    # Text-based data
    ".csv", ".tsv", ".sql",
    ".log",
}

# Extension-less files (and dotfiles, whose ``Path.suffix`` is empty).
TEXT_FILE_NAMES = {
    "dockerfile", "makefile", "procfile", "license", "licence", "notice", "readme",
    "changelog", "contributing", "authors", "codeowners", "gemfile", "rakefile",
    "jenkinsfile", "vagrantfile", "brewfile", "justfile",
    ".gitignore", ".gitattributes", ".gitmodules", ".dockerignore", ".editorconfig",
    ".prettierrc", ".eslintrc", ".babelrc", ".npmrc", ".nvmrc", ".python-version",
}

_BINARY_SNIFF_BYTES = 8192


def is_text_file(path: Path | PurePosixPath | str) -> bool:
    """Return True when the file name looks like a supported text file."""
    name = PurePosixPath(str(path).replace("\\", "/")).name
    lowered = name.lower()
    if lowered in TEXT_FILE_NAMES:
        return True
    return PurePosixPath(lowered).suffix in TEXT_FILE_EXTENSIONS


def decode_text(data: bytes, display_path: str = "file") -> tuple[str, str]:
    """Decode ``data`` deterministically and return ``(text, encoding)``.

    Order: UTF-16/UTF-8 BOM, strict UTF-8, then cp1252 (with replacement for
    the few undefined bytes). Data containing NUL bytes (without a UTF-16 BOM)
    is binary and raises ``binary_file``.
    """
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        try:
            return data.decode("utf-16"), "utf-16"
        except UnicodeDecodeError:
            pass
    if b"\x00" in data[:_BINARY_SNIFF_BYTES]:
        raise LLMScribeError("binary_file", f"'{display_path}' appears to be a binary file.")
    try:
        return data.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace"), "cp1252"


def extract_contents(root: Path, ignore_patterns: Iterable[str]) -> str:
    """Return ``--- path ---`` blocks for every readable text file below ``root``.

    ``ignore_patterns`` are applied in addition to the default ignores and any
    ``.gitignore`` files, exactly as in ``project_overview``.
    """
    from .project import project_overview

    result = project_overview(root, ignore_patterns=list(ignore_patterns))
    return "".join(f"\n--- {entry['path']} ---\n{entry['content']}" for entry in result.files)

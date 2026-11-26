"""Tool schemas in the shapes agent frameworks actually register.

Plain dictionaries, no pydantic: this module must import on a core-only install, because
the whole point of exporting schemas is to let another framework adopt LLMScribe without
taking on an MCP server's dependency tree.

    from llmscribe import tool_schemas
    tools = tool_schemas("openai")     # or "anthropic", "mcp", "raw"
"""

from __future__ import annotations

from typing import Any, Literal

# Bumped only for a breaking change to the JSON envelope in service.render_json.
SCHEMA_VERSION = "1.0"

Format = Literal["openai", "anthropic", "mcp", "raw"]

_STRING = {"type": "string"}
_BOOL = {"type": "boolean"}
_INT = {"type": "integer"}

_PATH = {
    "type": "string",
    "description": "Project directory to read. Defaults to the server's working directory.",
}
_FORMAT = {
    "type": "string",
    "enum": ["markdown", "json"],
    "description": "Response format. 'json' returns one machine-readable document.",
}
_DEPTH = {
    "type": "integer",
    "minimum": 1,
    "description": "Only include entries within the first N path levels, like `tree -L N`.",
}
_SIZES = {"type": "boolean", "description": "Include each file's size in bytes."}
_MAX_TOKENS = {
    "type": "integer",
    "minimum": 1,
    "description": (
        "Stop once the content reaches roughly this many tokens (estimated at 4 "
        "characters each). Files are taken in path order, never by relevance."
    ),
}
_COMPRESS = {
    "type": "boolean",
    "description": (
        "Reduce Python files to imports, signatures and docstrings, dropping bodies. "
        "A fixed syntactic transform; files that do not parse are left untouched."
    ),
}

TOOLS: list[dict[str, Any]] = [
    {
        "name": "project_map",
        "description": (
            "Directory tree of a local project, with file contents excluded. Respects "
            ".gitignore. The cheapest first step when exploring an unfamiliar repository."
        ),
        "properties": {"path": _PATH, "format": _FORMAT, "depth": _DEPTH, "sizes": _SIZES},
    },
    {
        "name": "project_overview",
        "description": (
            "Directory tree plus the contents of every supported text file. Secrets are "
            "masked. Bounded by a character or token budget, and every cut is reported."
        ),
        "properties": {
            "path": _PATH,
            "format": _FORMAT,
            "depth": _DEPTH,
            "sizes": _SIZES,
            "max_tokens": _MAX_TOKENS,
            "compress": _COMPRESS,
        },
    },
    {
        "name": "search",
        "description": (
            "Literal text search across the project, by filename and by file contents. "
            "Reports 'no matches' explicitly rather than returning silence."
        ),
        "properties": {"query": _STRING, "path": _PATH, "format": _FORMAT},
        "required": ["query"],
    },
    {
        "name": "read",
        "description": (
            "Read one file, with path-traversal protection. Reports byte size, line count "
            "and modified time for the whole file, even when the body is clipped. Secrets "
            "are masked."
        ),
        "properties": {
            "file_path": _STRING,
            "path": _PATH,
            "format": _FORMAT,
            "binary": {
                "type": "boolean",
                "description": "Return any file as base64 with its media type (images, PDFs).",
            },
            "compress": _COMPRESS,
        },
        "required": ["file_path"],
    },
    {
        "name": "read_many",
        "description": "Read several files at once. A failure on one file does not stop the rest.",
        "properties": {
            "file_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Paths relative to the project root.",
            },
            "path": _PATH,
            "format": _FORMAT,
        },
        "required": ["file_paths"],
    },
    {
        "name": "project_dependencies",
        "description": (
            "Imports of a file, split into local, standard library and external, plus "
            "which files import it back (used_by)."
        ),
        "properties": {"file_path": _STRING, "path": _PATH, "format": _FORMAT},
    },
    {
        "name": "project_diff",
        "description": "Git diff for the working tree, staged changes, or one commit.",
        "properties": {
            "path": _PATH,
            "staged": _BOOL,
            "commit": {"type": "string", "description": "Commit SHA or ref to diff against."},
            "format": _FORMAT,
        },
    },
]


def _parameters(tool: dict[str, Any]) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": tool["properties"],
        "additionalProperties": False,
    }
    if tool.get("required"):
        schema["required"] = tool["required"]
    return schema


def tool_schemas(fmt: Format = "openai") -> list[dict[str, Any]]:
    """Return every tool definition in the requested framework's shape.

    ``openai``     - ``{"type": "function", "function": {...}}``
    ``anthropic``  - ``{"name", "description", "input_schema"}``
    ``mcp``        - ``{"name", "description", "inputSchema"}``
    ``raw``        - the neutral form this module stores
    """
    if fmt == "raw":
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": _parameters(tool),
            }
            for tool in TOOLS
        ]

    if fmt == "openai":
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": _parameters(tool),
                },
            }
            for tool in TOOLS
        ]

    if fmt == "anthropic":
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": _parameters(tool),
            }
            for tool in TOOLS
        ]

    if fmt == "mcp":
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": _parameters(tool),
            }
            for tool in TOOLS
        ]

    raise ValueError(f"Unknown schema format: {fmt!r}. Use openai, anthropic, mcp or raw.")


def tool_names() -> list[str]:
    """The seven tool names, in a stable order."""
    return [tool["name"] for tool in TOOLS]

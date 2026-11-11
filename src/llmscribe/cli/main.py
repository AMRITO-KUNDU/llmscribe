"""Command-line interface for LLMScribe.

Every command runs the same implementation as the MCP tools (``llmscribe.service``)
on a local directory. With ``--json`` stdout contains exactly one JSON document;
diagnostics go to stderr. Exit codes: 0 success, 1 tool error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from llmscribe import __version__, service

# Familiar verbs map onto the canonical commands.
ALIASES = {
    "ls": "map",
    "tree": "overview",
    "grep": "search",
    "find": "search",
    "cat": "read",
    "deps": "dependencies",
}


def _emit(tool: str, command: str, as_json: bool, **kwargs: Any) -> int:
    try:
        response = service.execute(tool, **kwargs)
    except Exception as exc:  # noqa: BLE001 - converted to a structured error
        error = service.to_error(exc)
        if as_json:
            payload = service.error_envelope(tool, error)
            payload["command"] = command
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(f"llmscribe {command}: error [{error.code}]: {error.message}", file=sys.stderr)
        return 1
    if as_json:
        payload = service.envelope(response)
        payload["command"] = command
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(response.text)
    return 0


def _path_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-p", "--path", help="Project directory (default: current directory)")
    parser.add_argument("-j", "--json", action="store_true", help="Print one machine-readable JSON document")


def _path_positional(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "path_pos",
        nargs="?",
        metavar="PATH",
        help="Project directory (default: current directory)",
    )


def _command_names() -> set[str]:
    return {
        "map", "overview", "search", "read", "read-many", "dependencies", "diff", "version",
        *ALIASES,
    }


def _rewrite_path_only(argv: list[str]) -> list[str]:
    """`llmscribe .` or `llmscribe ./src` means `llmscribe map <path>`."""
    if not argv or argv[0].startswith("-"):
        return argv
    if argv[0] in _command_names():
        return argv
    if Path(argv[0]).is_dir():
        return ["map", *argv]
    return argv


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llmscribe",
        description="LLMScribe — deterministic repository data for humans, agents and LLM applications.",
        epilog="Examples:\n"
        "  llmscribe                      show this help\n"
        "  llmscribe .                    map the current directory\n"
        "  llmscribe map ./src            map a specific directory\n"
        "  llmscribe search \"auth\" .      search inside a directory\n"
        "  llmscribe read a.py b.py       read several files at once\n"
        "  llmscribe diff --staged --json\n"
        "\nAliases: ls=map, tree=overview, grep/find=search, cat=read, deps=dependencies\n"
        "Any command takes an optional PATH, so --path is never required.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="version", version=f"llmscribe version {__version__}")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("map", aliases=["ls"], help="Show project structure")
    _path_positional(p)
    _path_option(p)

    p = sub.add_parser("overview", aliases=["tree"], help="Tree plus file contents")
    _path_positional(p)
    _path_option(p)

    p = sub.add_parser("search", aliases=["grep", "find"], help="Search file names and contents")
    p.add_argument("query")
    _path_positional(p)
    _path_option(p)

    p = sub.add_parser("read", aliases=["cat"], help="Read one or more files")
    p.add_argument("files", nargs="+", metavar="FILE")
    _path_option(p)

    p = sub.add_parser("read-many", help="Read several files")
    p.add_argument("files", nargs="+", metavar="FILE")
    _path_option(p)

    p = sub.add_parser("dependencies", aliases=["deps"], help="Show a file's dependencies and dependents")
    p.add_argument("file_path")
    _path_positional(p)
    _path_option(p)

    p = sub.add_parser("diff", help="Show git status and diff")
    p.add_argument("--staged", action="store_true", help="Staged changes only")
    p.add_argument("--commit", help="Compare the working tree with this revision")
    _path_positional(p)
    _path_option(p)

    sub.add_parser("version", help="Show version")
    return parser


def main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

    raw = list(sys.argv[1:] if argv is None else argv)
    parser = create_parser()
    args = parser.parse_args(_rewrite_path_only(raw))

    command = ALIASES.get(args.command, args.command)
    if not command:
        parser.print_help()
        return
    if command == "version":
        print(f"llmscribe version {__version__}")
        return

    common = {"path": args.path or getattr(args, "path_pos", None)}
    as_json = args.json

    if command == "map":
        code = _emit("project_map", "map", as_json, **common)
    elif command == "overview":
        code = _emit("project_overview", "overview", as_json, **common)
    elif command == "search":
        code = _emit("search", "search", as_json, query=args.query, **common)
    elif command == "read":
        if len(args.files) == 1:
            code = _emit("read", "read", as_json, file_path=args.files[0], **common)
        else:
            code = _emit("read_many", "read", as_json, file_paths=args.files, **common)
    elif command == "read-many":
        code = _emit("read_many", "read-many", as_json, file_paths=args.files, **common)
    elif command == "dependencies":
        code = _emit("project_dependencies", "dependencies", as_json, file_path=args.file_path, **common)
    else:
        code = _emit("project_diff", "diff", as_json, staged=args.staged, commit=args.commit, **common)

    try:
        sys.stdout.flush()
    except BrokenPipeError:
        sys.stderr.close()
    sys.exit(code)


if __name__ == "__main__":
    main()

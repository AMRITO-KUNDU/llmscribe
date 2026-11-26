"""Command-line interface for LLMScribe.

Every command runs the same implementation as the MCP tools (``llmscribe.service``)
on a local directory. With ``--json`` stdout contains exactly one JSON document;
diagnostics go to stderr. Exit codes: 0 success, 1 tool error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from llmscribe import __version__, service


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
    parser.add_argument("--path", help="Project directory (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Print one machine-readable JSON document")
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Do not mask secrets. They are masked by default, including for MCP clients.",
    )


def _compress_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Reduce Python files to signatures and docstrings, dropping bodies",
    )


def _tokens_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--max-tokens",
        type=int,
        metavar="N",
        help="Stop after roughly N tokens (~4 characters each), taking files in path order",
    )


def _sizes_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--sizes", action="store_true", help="Include each file's size in bytes")


def _depth_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--depth",
        type=int,
        metavar="N",
        help="List only the first N levels (like `tree -L N`)",
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llmscribe",
        description="LLMScribe — repository data for humans, agents and LLM applications.",
        epilog="Examples:\n  llmscribe map\n  llmscribe search \"auth\" --json\n  llmscribe read src/main.py\n"
        "  llmscribe dependencies src/main.py\n  llmscribe diff --staged",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    for name, help_text in (("map", "Show project structure"), ("overview", "Tree plus file contents")):
        p = sub.add_parser(name, help=help_text)
        _path_option(p)
        _depth_option(p)
        _sizes_option(p)
        _tokens_option(p)
        _compress_option(p)

    p = sub.add_parser("search", help="Search file names and contents")
    p.add_argument("query")
    _path_option(p)

    p = sub.add_parser("read", help="Read one file")
    p.add_argument("file_path")
    p.add_argument(
        "--binary",
        action="store_true",
        help="Read any file as base64 with its media type (images, PDFs)",
    )
    p.add_argument(
        "--compress",
        action="store_true",
        help="For .py files, return signatures and docstrings only",
    )
    _path_option(p)

    p = sub.add_parser("read-many", help="Read several files")
    p.add_argument("file_paths", nargs="+")
    _path_option(p)

    p = sub.add_parser("dependencies", help="Show a file's dependencies and dependents")
    p.add_argument("file_path")
    _path_option(p)

    p = sub.add_parser("diff", help="Show git status and diff")
    p.add_argument("--staged", action="store_true", help="Staged changes only")
    p.add_argument("--commit", help="Compare the working tree with this revision")
    _path_option(p)

    sub.add_parser("version", help="Show version")

    sp = sub.add_parser("schema", help="Print tool schemas for an agent framework")
    sp.add_argument(
        "--format",
        choices=["openai", "anthropic", "mcp", "raw"],
        default="openai",
        help="Which framework's shape to emit (default: openai)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point: run the CLI, exiting quietly if the reader closes the pipe."""
    try:
        _main(argv)
    except BrokenPipeError:
        # e.g. `llmscribe overview . | head` - the reader went away. Detach stdout so
        # interpreter shutdown cannot raise again, then exit cleanly.
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except (OSError, ValueError):
            pass
        sys.exit(0)


def _main(argv: list[str] | None = None) -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass

    parser = create_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse: 0 for --help, 2 for usage errors
        raise exc
    if not args.command:
        parser.print_help()
        return
    if args.command == "version":
        print(f"llmscribe version {__version__}")
        return
    if args.command == "schema":
        from llmscribe.schema import tool_schemas

        print(json.dumps(tool_schemas(args.format), indent=2, ensure_ascii=False))
        return

    common = {"path": args.path, "redact": not args.no_redact}
    if args.command in ("map", "overview"):
        common["max_depth"] = args.depth
        common["include_sizes"] = args.sizes
        common["max_tokens"] = args.max_tokens
        common["compress"] = args.compress
    if args.command == "read":
        common["binary"] = args.binary
        common["compress"] = args.compress
    as_json = args.json
    if args.command == "map":
        code = _emit("project_map", "map", as_json, **common)
    elif args.command == "overview":
        code = _emit("project_overview", "overview", as_json, **common)
    elif args.command == "search":
        code = _emit("search", "search", as_json, query=args.query, **common)
    elif args.command == "read":
        code = _emit("read", "read", as_json, file_path=args.file_path, **common)
    elif args.command == "read-many":
        code = _emit("read_many", "read-many", as_json, file_paths=args.file_paths, **common)
    elif args.command == "dependencies":
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

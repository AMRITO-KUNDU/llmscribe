"""Command-line interface for LLMScribe.

LLMScribe — code context for AI agents

Usage:
  llmscribe <command> [options]

Commands:
  map             Show project structure
  overview        Generate project overview
  search          Search project code
  read            Read a file or line range
  read-many       Read multiple files
  dependencies    Show file dependencies
  diff            Show project changes

Other:
  version         Show version
  help            Show help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Set stdout to use UTF-8 encoding to avoid encoding issues on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')

from llmscribe import __version__
from llmscribe.core import (
    analyze_dependencies,
    get_git_diff,
    project_map as core_project_map,
    project_overview as core_project_overview,
    read_file,
    read_files,
    search_project,
)


def _print_json(data: dict) -> None:
    """Print JSON output to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _print_markdown(text: str) -> None:
    """Print markdown output to stdout."""
    print(text, encoding='utf-8', errors='ignore')


def _handle_error(error: Exception, command: str) -> int:
    """Handle an error and print appropriate message."""
    print(f"llmscribe {command}: Error: {error}", file=sys.stderr)
    if hasattr(error, '__context__') and error.__context__:
        print(f"Details: {error.__context__}", file=sys.stderr)
    return 1


def _resolve_project_root(path: str | None = None) -> Path:
    """Resolve project root directory."""
    if path and path.strip():
        return Path(path).resolve()
    else:
        return Path.cwd().resolve()


def cmd_map(args: argparse.Namespace) -> int:
    """Handle the 'map' command."""
    try:
        root = _resolve_project_root(args.path)
        result = core_project_map(root)
        
        if args.json:
            _print_json({
                "ok": True,
                "command": "map",
                "path": root.as_posix(),
                "data": result.to_dict(),
                "metadata": {
                    "file_count": result.file_count,
                    "character_count": result.character_count,
                },
            })
        else:
            print(f"Project Map: {root}")
            print("=" * 40)
            print(result.tree)
            print(f"\nTotal files: {result.file_count}")
        
        return 0
    except Exception as e:
        return _handle_error(e, "map")


def cmd_overview(args: argparse.Namespace) -> int:
    """Handle the 'overview' command."""
    try:
        root = _resolve_project_root(args.path)
        result = core_project_overview(root)
        
        if args.json:
            data = result.to_dict()
            metadata: dict = {
                "file_count": result.file_count,
                "character_count": result.character_count,
            }
            if result.truncated:
                metadata["truncated"] = True
                metadata["truncation_note"] = result.truncation_note
            
            _print_json({
                "ok": True,
                "command": "overview",
                "path": root.as_posix(),
                "data": data,
                "metadata": metadata,
            })
        else:
            print(f"Project Overview: {root}")
            print("=" * 40)
            print("Directory Structure:")
            print(result.tree)
            print(f"\nFile Count: {result.file_count}")
            print(f"Character Count: {result.character_count:,}")
            if result.truncated:
                print(f"Note: {result.truncation_note}")
        
        return 0
    except Exception as e:
        return _handle_error(e, "overview")


def cmd_search(args: argparse.Namespace) -> int:
    """Handle the 'search' command."""
    try:
        if not args.query:
            print("Error: Query cannot be empty", file=sys.stderr)
            return 1
        
        root = _resolve_project_root(args.path)
        result = search_project(args.query, root, max_results=1000)
        
        if args.json:
            _print_json({
                "ok": True,
                "command": "search",
                "path": root.as_posix(),
                "data": result.to_dict(),
                "metadata": {
                    "query": result.query,
                    "file_count": result.file_count,
                    "match_count": result.match_count,
                    "truncated": result.truncated,
                },
            })
        else:
            print(f"Search Results for '{args.query}': {root}")
            print("=" * 50)
            
            if not result.matches:
                print("No matches found.")
                return 0
            
            # Group by file
            matches_by_file: dict[str, list] = {}
            for match in result.matches:
                if match.file_path not in matches_by_file:
                    matches_by_file[match.file_path] = []
                matches_by_file[match.file_path].append(match)
            
            for file_path, file_matches in sorted(matches_by_file.items()):
                print(f"\nFile: {file_path}")
                
                # Check match types
                has_filename = any(m.match_type == "filename" for m in file_matches)
                content_matches = [m for m in file_matches if m.match_type == "content"]
                
                if has_filename and not content_matches:
                    print("  (Filename match)")
                
                # Show content matches (limit to 5 per file)
                for match in content_matches[:5]:
                    print(f"  Line {match.line_number}: {match.line_content}")
                
                if len(content_matches) > 5:
                    print(f"  ... and {len(content_matches) - 5} more matches")
            
            print(f"\nFound {result.match_count} matches in {result.file_count} files")
            if result.truncated:
                print("Note: Results truncated.")
        
        return 0
    except Exception as e:
        return _handle_error(e, "search")


def cmd_read(args: argparse.Namespace) -> int:
    """Handle the 'read' command."""
    try:
        if not args.file_path:
            print("Error: File path must be provided", file=sys.stderr)
            return 1
        
        root = _resolve_project_root(args.path)
        result = read_file(args.file_path, root)
        
        if not result.ok:
            print(f"Error: {result.error_message}", file=sys.stderr)
            return 1
        
        if args.json:
            _print_json({
                "ok": True,
                "command": "read",
                "path": root.as_posix(),
                "data": result.to_dict(),
                "metadata": {
                    "character_count": result.character_count,
                },
            })
        else:
            print(f"File: {result.file_path}")
            print("=" * 40)
            print(result.content)
            print(f"\nCharacters: {result.character_count:,}")
        
        return 0
    except Exception as e:
        return _handle_error(e, "read")


def cmd_read_many(args: argparse.Namespace) -> int:
    """Handle the 'read-many' command."""
    try:
        if not args.file_paths:
            print("Error: At least one file path must be provided", file=sys.stderr)
            return 1
        
        root = _resolve_project_root(args.path)
        result = read_files(args.file_paths, root)
        
        if args.json:
            metadata: dict = {
                "file_count": result.file_count,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "character_count": result.character_count,
            }
            if result.truncated:
                metadata["truncated"] = True
                metadata["truncation_note"] = result.truncation_note
            
            _print_json({
                "ok": True,
                "command": "read-many",
                "path": root.as_posix(),
                "data": result.to_dict(),
                "metadata": metadata,
            })
        else:
            print(f"Reading {len(args.file_paths)} files from: {root}")
            print("=" * 50)
            
            for file_result in result.results:
                if file_result.ok:
                    print(f"\n--- {file_result.file_path} ---")
                    print(file_result.content)
                    print(f"Characters: {file_result.character_count:,}")
                else:
                    print(f"Error reading {file_result.file_path}: [{file_result.error_code}] {file_result.error_message}")
            
            print(f"\nSummary: {result.success_count} succeeded, {result.error_count} failed")
            if result.truncated:
                print(f"Note: {result.truncation_note}")
        
        return 0
    except Exception as e:
        return _handle_error(e, "read-many")


def cmd_dependencies(args: argparse.Namespace) -> int:
    """Handle the 'dependencies' command."""
    try:
        if not args.file_path:
            print("Error: File path must be provided", file=sys.stderr)
            return 1
        
        root = _resolve_project_root(args.path)
        result = analyze_dependencies(args.file_path, root)
        
        if args.json:
            _print_json({
                "ok": True,
                "command": "dependencies",
                "path": root.as_posix(),
                "data": result.to_dict(),
                "metadata": {
                    "file_count": len(result.all_local_files),
                    "external_dep_count": len(result.all_external_deps),
                    "unresolved_count": len(result.all_unresolved),
                },
            })
        else:
            print(f"Dependencies for: {args.file_path}")
            print("=" * 40)
            
            file_deps = result.file_dependencies
            
            if file_deps.imports:
                print(f"\nImports: {', '.join(file_deps.imports)}")
            
            if file_deps.local_dependencies:
                print(f"\nLocal Dependencies:")
                for dep in file_deps.local_dependencies:
                    print(f"  - {dep}")
            
            if file_deps.external_dependencies:
                print(f"\nExternal Dependencies:")
                for dep in file_deps.external_dependencies:
                    print(f"  - {dep}")
            
            if file_deps.unresolved_dependencies:
                print(f"\nUnresolved Dependencies:")
                for dep in file_deps.unresolved_dependencies:
                    print(f"  - {dep}")
            
            if result.all_local_files:
                print(f"\nFiles that depend on this file:")
                for dep in result.all_local_files:
                    print(f"  - {dep}")
            
            if not any([file_deps.imports, file_deps.local_dependencies, 
                      file_deps.external_dependencies, file_deps.unresolved_dependencies]):
                print("\nNo dependencies found or file not supported.")
        
        return 0
    except Exception as e:
        return _handle_error(e, "dependencies")


def cmd_diff(args: argparse.Namespace) -> int:
    """Handle the 'diff' command."""
    try:
        root = _resolve_project_root(args.path)
        result = get_git_diff(root, staged=args.staged, commit=args.commit)
        
        if args.json:
            _print_json({
                "ok": True,
                "command": "diff",
                "path": root.as_posix(),
                "data": {
                    "staged": result.staged,
                    "commit": result.commit,
                    "changed_files": result.changed_files,
                    "status_lines": result.status_lines,
                    "diff": result.diff,
                    "truncated": result.truncated,
                },
                "metadata": {
                    "changed_file_count": len(result.changed_files),
                    "character_count": result.character_count,
                    "truncated": result.truncated,
                },
            })
        else:
            print(f"Git Status & Diff: {root}")
            print("=" * 40)
            
            if result.changed_files:
                print("Changed Files:")
                for f in result.changed_files:
                    print(f"  - {f}")
            else:
                print("No changed files.")
            
            if result.diff.strip():
                print(f"\nDiff (first {len(result.diff):,} characters):")
                print("-" * 30)
                print(result.diff)
            else:
                print("\nNo diff output.")
            
            if result.truncated:
                print(f"\nNote: Diff truncated at {result.truncation_limit:,} characters.")
        
        return 0
    except Exception as e:
        return _handle_error(e, "diff")


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="llmscribe",
        description="LLMScribe — code context for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  llmscribe map                    # Show project structure
  llmscribe overview               # Generate full project overview
  llmscribe search "auth"          # Search for "auth" in code
  llmscribe read src/main.py       # Read a specific file
  llmscribe read-many src/main.py src/utils.py  # Read multiple files
  llmscribe dependencies src/main.py  # Show file dependencies
  llmscribe diff                   # Show git diff
  llmscribe search "auth" --json   # Get JSON output

For more help on a specific command:
  llmscribe search --help
        """
    )
    
    # Subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Map command
    map_parser = subparsers.add_parser("map", help="Show project structure")
    map_parser.add_argument("--path", help="Project folder path (default: current directory)")
    map_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Overview command
    overview_parser = subparsers.add_parser("overview", help="Generate project overview")
    overview_parser.add_argument("--path", help="Project folder path (default: current directory)")
    overview_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search project code")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--path", help="Project folder path (default: current directory)")
    search_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Read command
    read_parser = subparsers.add_parser("read", help="Read a file")
    read_parser.add_argument("file_path", help="File path to read")
    read_parser.add_argument("--path", help="Project root path (default: current directory)")
    read_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Read-many command
    read_many_parser = subparsers.add_parser("read-many", help="Read multiple files")
    read_many_parser.add_argument("file_paths", nargs="+", help="File paths to read")
    read_many_parser.add_argument("--path", help="Project root path (default: current directory)")
    read_many_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Dependencies command
    deps_parser = subparsers.add_parser("dependencies", help="Show file dependencies")
    deps_parser.add_argument("file_path", help="File path to analyze")
    deps_parser.add_argument("--path", help="Project root path (default: current directory)")
    deps_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Show project changes")
    diff_parser.add_argument("--path", help="Project root path (default: current directory)")
    diff_parser.add_argument("--staged", action="store_true", help="Show staged changes only")
    diff_parser.add_argument("--commit", help="Compare against specific commit")
    diff_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    # Version command
    subparsers.add_parser("version", help="Show version")
    
    return parser


def main() -> None:
    """Run the LLMScribe CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command or args.command == "help":
        parser.print_help()
        return
    
    if args.command == "version":
        print(f"llmscribe version {__version__}")
        return
    
    # Route to appropriate command handler
    command_handlers = {
        "map": cmd_map,
        "overview": cmd_overview,
        "search": cmd_search,
        "read": cmd_read,
        "read-many": cmd_read_many,
        "dependencies": cmd_dependencies,
        "diff": cmd_diff,
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
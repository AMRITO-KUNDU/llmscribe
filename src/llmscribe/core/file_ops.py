"""Core file operations for LLMScribe."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .file_reader import is_text_file
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, load_gitignore


@dataclass
class FileReadResult:
    """Result of reading a single file."""
    file_path: str
    content: str
    character_count: int
    ok: bool = True
    error_code: str = ""
    error_message: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "file_path": self.file_path,
            "character_count": self.character_count,
        }
        if self.ok:
            result["content"] = self.content
        else:
            result["ok"] = False
            result["error"] = {
                "code": self.error_code,
                "message": self.error_message,
            }
        return result


@dataclass
class ReadManyResult:
    """Result of reading multiple files."""
    root_path: str
    results: list[FileReadResult] = field(default_factory=list)
    file_count: int = 0
    success_count: int = 0
    error_count: int = 0
    character_count: int = 0
    truncated: bool = False
    truncation_limit: int = 50
    truncation_note: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "results": [r.to_dict() for r in self.results],
            "file_count": self.file_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "character_count": self.character_count,
            "truncated": self.truncated,
            "truncation_limit": self.truncation_limit,
            "truncation_note": self.truncation_note,
        }


def read_file(
    file_path: str,
    root: Path | None = None,
    max_content_chars: int = 400_000,
) -> FileReadResult:
    """Read a single file with path traversal prevention.
    
    Args:
        file_path: Relative path to the file from root
        root: Project root directory (defaults to current working directory)
        max_content_chars: Maximum characters to return
        
    Returns:
        FileReadResult with file content or error
    """
    if not file_path or not file_path.strip():
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="invalid_argument",
            error_message="file_path must be provided",
        )
    
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="invalid_path",
            error_message=f"Root directory does not exist: {root}",
        )
    if not root.is_dir():
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="not_a_directory",
            error_message=f"Root path is not a directory: {root}",
        )
    
    # Resolve target path
    target_path = (root / file_path).resolve()
    
    # Check for path traversal
    try:
        target_path.relative_to(root)
    except ValueError:
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="path_traversal",
            error_message=f"Path traversal attempt detected. '{file_path}' is outside root directory.",
        )
    
    # Check if file exists and is a file
    if not target_path.exists():
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="file_not_found",
            error_message=f"File does not exist: '{file_path}'",
        )
    
    if not target_path.is_file():
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="not_a_file",
            error_message=f"Path is not a file: '{file_path}'",
        )
    
    # Check if it's a text file
    if not is_text_file(target_path):
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="not_text_file",
            error_message=f"File '{file_path}' is not a recognized text file.",
        )
    
    # Read content
    try:
        content = target_path.read_text(encoding="utf-8", errors="ignore")
        
        # Apply character limit
        if len(content) > max_content_chars:
            content = content[:max_content_chars] + "\n[Content truncated]"
        
        return FileReadResult(
            file_path=str(target_path.relative_to(root).as_posix()),
            content=content,
            character_count=len(content),
            ok=True,
        )
    except OSError as exc:
        return FileReadResult(
            file_path=file_path,
            content="",
            character_count=0,
            ok=False,
            error_code="read_error",
            error_message=str(exc),
        )


def read_files(
    file_paths: list[str],
    root: Path | None = None,
    max_files: int = 50,
    max_content_chars: int = 400_000,
) -> ReadManyResult:
    """Read multiple files with path traversal prevention.
    
    Args:
        file_paths: List of relative file paths to read
        root: Project root directory (defaults to current working directory)
        max_files: Maximum number of files to process
        max_content_chars: Maximum total characters to return
        
    Returns:
        ReadManyResult with results for all files
    """
    if not file_paths:
        return ReadManyResult(
            root_path="",
            file_count=0,
            error_count=1,
            error_message="file_paths list cannot be empty",
        )
    
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        return ReadManyResult(
            root_path=root.as_posix(),
            file_count=len(file_paths),
            error_count=len(file_paths),
            truncation_note=f"Root directory does not exist: {root}",
        )
    
    result = ReadManyResult(
        root_path=root.as_posix(),
        file_count=len(file_paths),
        truncation_limit=max_files,
    )
    
    # Limit number of files
    truncated_batch = False
    if len(file_paths) > max_files:
        target_paths_list = file_paths[:max_files]
        truncated_batch = True
    else:
        target_paths_list = file_paths
    
    total_chars = 0
    truncated_chars = False
    
    for fp in target_paths_list:
        if not fp or not fp.strip():
            error_result = FileReadResult(
                file_path=fp,
                content="",
                character_count=0,
                ok=False,
                error_code="invalid_argument",
                error_message="Empty file path provided",
            )
            result.results.append(error_result)
            result.error_count += 1
            continue
        
        # Check path traversal
        target_path = (root / fp).resolve()
        try:
            target_path.relative_to(root)
        except ValueError:
            error_result = FileReadResult(
                file_path=fp,
                content="",
                character_count=0,
                ok=False,
                error_code="path_traversal",
                error_message=f"Path traversal attempt: '{fp}' is outside root.",
            )
            result.results.append(error_result)
            result.error_count += 1
            continue
        
        # Check if file exists
        if not target_path.exists():
            error_result = FileReadResult(
                file_path=fp,
                content="",
                character_count=0,
                ok=False,
                error_code="file_not_found",
                error_message=f"File does not exist: '{fp}'",
            )
            result.results.append(error_result)
            result.error_count += 1
            continue
        
        # Check if it's a file
        if not target_path.is_file():
            error_result = FileReadResult(
                file_path=fp,
                content="",
                character_count=0,
                ok=False,
                error_code="not_a_file",
                error_message=f"Path is not a file: '{fp}'",
            )
            result.results.append(error_result)
            result.error_count += 1
            continue
        
        # Check if it's a text file
        if not is_text_file(target_path):
            error_result = FileReadResult(
                file_path=fp,
                content="",
                character_count=0,
                ok=False,
                error_code="not_text_file",
                error_message=f"File '{fp}' is not a recognized text file.",
            )
            result.results.append(error_result)
            result.error_count += 1
            continue
        
        # Read file content
        try:
            rel_posix = target_path.relative_to(root).as_posix()
            content = target_path.read_text(encoding="utf-8", errors="ignore")
            content_len = len(content)
            
            # Check total character limit
            if total_chars + content_len > max_content_chars:
                remaining = max(0, max_content_chars - total_chars)
                truncated_content = content[:remaining] + "\n[Content truncated]"
                total_chars += len(truncated_content)
                
                read_result = FileReadResult(
                    file_path=rel_posix,
                    content=truncated_content,
                    character_count=len(truncated_content),
                    ok=True,
                )
                result.results.append(read_result)
                result.success_count += 1
                truncated_chars = True
                break
            
            total_chars += content_len
            read_result = FileReadResult(
                file_path=rel_posix,
                content=content,
                character_count=content_len,
                ok=True,
            )
            result.results.append(read_result)
            result.success_count += 1
            
        except OSError as exc:
            error_result = FileReadResult(
                file_path=fp,
                content="",
                character_count=0,
                ok=False,
                error_code="read_error",
                error_message=str(exc),
            )
            result.results.append(error_result)
            result.error_count += 1
    
    result.character_count = total_chars
    
    # Set truncation info
    if truncated_batch or truncated_chars:
        result.truncated = True
        notes = []
        if truncated_batch:
            notes.append(f"Processed first {max_files} files out of {len(file_paths)} requested.")
        if truncated_chars:
            notes.append(f"Total file content capped at {max_content_chars:,} characters.")
        result.truncation_note = " ".join(notes)
    
    return result
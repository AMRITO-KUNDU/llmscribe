"""One small error model shared by the core, CLI and MCP."""

from __future__ import annotations

ERROR_CODES = (
    "invalid_argument",
    "invalid_path",
    "file_not_found",
    "unsupported_file_type",
    "binary_file",
    "file_too_large",
    "read_error",
    "not_a_repository",
    "git_unavailable",
    "unsupported_operation",
    "internal_error",
)


class LLMScribeError(Exception):
    """A user-presentable failure with a stable machine-readable ``code``."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}

"""One small error model shared by the core, GitHub provider, CLI and MCP."""

from __future__ import annotations

import os
import re

ERROR_CODES = (
    "invalid_argument",
    "invalid_path",
    "file_not_found",
    "unsupported_file_type",
    "binary_file",
    "file_too_large",
    "read_error",
    "repository_not_found",
    "not_a_repository",
    "repository_too_large",
    "github_rate_limited",
    "github_auth_required",
    "github_unavailable",
    "git_unavailable",
    "unsupported_operation",
    "internal_error",
)

_TOKEN_PATTERN = re.compile(r"(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")


class LLMScribeError(Exception):
    """A user-presentable failure with a stable machine-readable ``code``."""

    def __init__(self, code: str, message: str):
        message = redact(message)
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def redact(text: str) -> str:
    """Remove GitHub tokens (from the environment or token-shaped) from ``text``."""
    for name in ("GITHUB_TOKEN", "GH_TOKEN"):
        token = os.environ.get(name, "").strip()
        if len(token) >= 8:
            text = text.replace(token, "[REDACTED]")
    return _TOKEN_PATTERN.sub("[REDACTED]", text)

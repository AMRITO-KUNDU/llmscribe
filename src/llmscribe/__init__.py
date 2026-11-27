"""LLMScribe — repository extraction and contextual code access.

The public API is imported lazily so ``import llmscribe`` stays instant (loading
``llmscribe.core`` costs ~200ms):

    >>> from llmscribe import Repository, LLMScribeError
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

__version__ = "3.0.1"

__all__ = [
    "LLMScribeError",
    "Repository",
    "SCHEMA_VERSION",
    "__version__",
    "tool_names",
    "tool_schemas",
]

if TYPE_CHECKING:  # pragma: no cover - for type checkers and IDEs only
    from .api import Repository
    from .core.errors import LLMScribeError


def __getattr__(name: str) -> Any:
    """Resolve the public API on first access (PEP 562)."""
    if name == "Repository":
        from .api import Repository

        return Repository
    if name == "LLMScribeError":
        from .core.errors import LLMScribeError

        return LLMScribeError
    if name in {"tool_schemas", "tool_names", "SCHEMA_VERSION"}:
        from . import schema

        return getattr(schema, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)

"""Adapters that turn the tool list into another framework's native objects.

Each adapter imports its framework lazily, so installing ``llmscribe`` never pulls one
in. Importing an adapter module without its framework raises a ModuleNotFoundError that
names the pip command.
"""

from __future__ import annotations

__all__ = [
    "as_anthropic_tools",
    "as_langchain_tools",
    "as_llamaindex_tools",
    "as_pydantic_ai_tools",
    "as_smolagents_tools",
]


def __getattr__(name: str):
    """Import the adapter module only when its function is asked for."""
    mapping = {
        "as_anthropic_tools": ("anthropic", "as_anthropic_tools"),
        "as_langchain_tools": ("langchain", "as_langchain_tools"),
        "as_llamaindex_tools": ("llamaindex", "as_llamaindex_tools"),
        "as_pydantic_ai_tools": ("pydantic_ai", "as_pydantic_ai_tools"),
        "as_smolagents_tools": ("smolagents", "as_smolagents_tools"),
    }
    if name in mapping:
        import importlib

        module_name, attr = mapping[name]
        module = importlib.import_module(f".{module_name}", __name__)
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

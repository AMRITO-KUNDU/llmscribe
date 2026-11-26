"""One neutral tool list that any agent framework can consume.

This is the primitive adapters are built from: a name, a description, a JSON Schema for
the arguments, and a callable that takes exactly those arguments. No pydantic, no MCP,
so it works on the core install.

    from llmscribe import Repository, tools
    for tool in tools(Repository(".")):
        register(tool.name, tool.description, tool.parameters, tool.handler)
"""

from __future__ import annotations

import copy
import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .schema import tool_schemas


@dataclass(frozen=True)
class Tool:
    """A tool definition plus the callable that runs it."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., dict[str, Any]]


def _bound(parameters: dict[str, Any]) -> dict[str, Any]:
    """Drop the ``path`` argument from a bound tool.

    The tool is already tied to one repository. Letting a model pass ``path`` would let
    it repoint the reader at any directory on the machine — a sandbox escape dressed up
    as a convenience.
    """
    bound = copy.deepcopy(parameters)
    bound.get("properties", {}).pop("path", None)
    if "required" in bound:
        bound["required"] = [name for name in bound["required"] if name != "path"]
        if not bound["required"]:
            bound.pop("required")
    return bound


def tools(repository: Any) -> list[Tool]:
    """Return every tool bound to ``repository`` (anything with ``.handlers()``).

    ``path`` is removed from each schema: the set is bound to one root.
    """
    handlers = repository.handlers()
    return [
        Tool(
            name=definition["name"],
            description=definition["description"],
            parameters=_bound(definition["parameters"]),
            handler=handlers[definition["name"]],
        )
        for definition in tool_schemas("raw")
    ]


MISSING_HINT = (
    "This adapter needs {package}. Install it with:\n"
    "    pip install 'llmscribe[adapters]'\n"
    "or install {package} directly."
)


def require(module: str, package: str | None = None) -> Any:
    """Import a framework, or explain how to install it.

    A bare ModuleNotFoundError inside an adapter is unhelpful: the user asked for
    LangChain tools and gets told about a missing package with no next step.
    """
    try:
        return importlib.import_module(module)
    except ModuleNotFoundError:
        raise ModuleNotFoundError(MISSING_HINT.format(package=package or module)) from None

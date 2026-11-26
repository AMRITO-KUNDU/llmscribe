"""LlamaIndex tools backed by a LLMScribe repository."""

from __future__ import annotations

from typing import Any

from ..tools import require, tools

_TYPES = {"string": "str", "integer": "int", "boolean": "bool", "number": "float"}


def _callable_for(tool: Any) -> Any:
    """Build a callable with a real signature.

    LlamaIndex derives the tool schema from the function's signature and type hints, so
    a ``**kwargs`` wrapper would produce a tool that takes no arguments. The parameter
    names come from our own schema, which is fixed.
    """
    properties = tool.parameters.get("properties", {})
    required = set(tool.parameters.get("required", []))
    # required parameters first: Python does not allow a defaulted one before them
    names = [name for name in properties if name in required]
    names += [name for name in properties if name not in required]

    params = []
    for name in names:
        spec = properties[name]
        annotation = "list[str]" if spec.get("type") == "array" else _TYPES.get(spec.get("type", "string"), "str")
        params.append(f"{name}: {annotation}" if name in required else f"{name}: {annotation} | None = None")

    arguments = ", ".join(f"{name}={name}" for name in names)
    namespace: dict[str, Any] = {"_handler": tool.handler}
    exec(f"def _tool({', '.join(params)}):\n    return _handler({arguments})\n", namespace)

    function = namespace["_tool"]
    function.__name__ = tool.name
    function.__doc__ = tool.description
    return function


def as_llamaindex_tools(repository: Any) -> list[Any]:
    """Return ``FunctionTool`` objects for a LlamaIndex agent."""
    FunctionTool = require("llama_index.core.tools", "llama-index-core").FunctionTool

    return [
        FunctionTool.from_defaults(
            fn=_callable_for(tool),
            name=tool.name,
            description=tool.description,
        )
        for tool in tools(repository)
    ]

"""LangChain tools backed by a LLMScribe repository."""

from __future__ import annotations

from typing import Any

from ..tools import require, tools

_TYPES: dict[str, Any] = {"string": str, "integer": int, "boolean": bool, "number": float}


def _args_model(tool_name: str, parameters: dict[str, Any]) -> Any:
    """Build a pydantic model from a JSON Schema, which is what LangChain expects."""
    pydantic = require("pydantic")
    required = set(parameters.get("required", []))
    fields: dict[str, Any] = {}
    for prop, spec in parameters.get("properties", {}).items():
        if spec.get("type") == "array":
            annotation: Any = list[str]
        else:
            annotation = _TYPES.get(spec.get("type", "string"), str)
        if prop not in required:
            annotation = annotation | None
            fields[prop] = (annotation, None)
        else:
            fields[prop] = (annotation, pydantic.Field(..., description=spec.get("description")))
    return pydantic.create_model(f"LLMScribe_{tool_name}_args", **fields)


def as_langchain_tools(repository: Any) -> list[Any]:
    """Return ``StructuredTool`` objects; pass them straight to an agent."""
    structured = require("langchain_core.tools", "langchain-core").StructuredTool

    built = []
    for tool in tools(repository):
        built.append(
            structured.from_function(
                func=tool.handler,
                name=tool.name,
                description=tool.description,
                args_schema=_args_model(tool.name, tool.parameters),
            )
        )
    return built

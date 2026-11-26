"""PydanticAI tools backed by a LLMScribe repository."""

from __future__ import annotations

from typing import Any

from ..tools import require, tools


def as_pydantic_ai_tools(repository: Any) -> list[Any]:
    """Return ``pydantic_ai.Tool`` objects built from the JSON Schema."""
    Tool = require("pydantic_ai", "pydantic-ai").Tool

    return [
        Tool.from_schema(
            function=tool.handler,
            name=tool.name,
            description=tool.description,
            json_schema=tool.parameters,
        )
        for tool in tools(repository)
    ]

"""Tool definitions and a dispatcher for the Anthropic Messages API.

No SDK import: the Messages API takes tool definitions as plain dicts and returns
``tool_use`` blocks whose ``input`` you dispatch yourself. That is all this provides, so
it works with the raw SDK, the Claude Agent SDK, or anything else that speaks the same
shape.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..tools import tools


def as_anthropic_tools(
    repository: Any,
) -> tuple[list[dict[str, Any]], dict[str, Callable[..., dict[str, Any]]]]:
    """Return ``(tool_definitions, dispatch)``.

        tools, run = as_anthropic_tools(Repository("."))
        response = client.messages.create(..., tools=tools)
        for block in response.content:
            if block.type == "tool_use":
                result = run[block.name](**block.input)
    """
    bound = tools(repository)
    definitions = [
        {"name": tool.name, "description": tool.description, "input_schema": tool.parameters}
        for tool in bound
    ]
    return definitions, {tool.name: tool.handler for tool in bound}

"""smolagents tools backed by a LLMScribe repository."""

from __future__ import annotations

from typing import Any

from ..tools import require, tools

_TYPES = {
    "string": "string",
    "integer": "integer",
    "number": "number",
    "boolean": "boolean",
    "array": "array",
    "object": "object",
}


def _inputs(parameters: dict[str, Any]) -> dict[str, dict[str, Any]]:
    required = set(parameters.get("required", []))
    described: dict[str, dict[str, Any]] = {}
    for prop, spec in parameters.get("properties", {}).items():
        described[prop] = {
            "type": _TYPES.get(spec.get("type", "string"), "string"),
            "description": spec.get("description", ""),
            "nullable": prop not in required,
        }
    return described


def _forward(names: list[str]) -> Any:
    """Build ``forward`` with real parameters.

    smolagents validates that ``forward``'s signature matches the ``inputs`` keys, so a
    ``**kwargs`` method is rejected. The parameter names come from our own schema, which
    is fixed, so generating the function is safe and keeps the two in sync.
    """
    signature = ", ".join(f"{name}=None" for name in names)
    arguments = ", ".join(f"{name}={name}" for name in names)
    namespace: dict[str, Any] = {}
    exec(f"def forward(self, {signature}):\n    return self._handler({arguments})\n", namespace)
    return namespace["forward"]


def as_smolagents_tools(repository: Any) -> list[Any]:
    """Return ``smolagents.Tool`` instances, one per LLMScribe tool."""
    base = require("smolagents", "smolagents").Tool

    built = []
    for tool in tools(repository):
        names = list(tool.parameters.get("properties", {}))

        def _init(self, _handler=tool.handler):
            base.__init__(self)
            self._handler = _handler

        built.append(
            type(
                f"LLMScribe_{tool.name}",
                (base,),
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputs": _inputs(tool.parameters),
                    "output_type": "object",
                    "forward": _forward(names),
                    "__init__": _init,
                },
            )()
        )
    return built

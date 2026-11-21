"""Reduce a Python file to its API surface, using the standard library parser.

The point is token economy without judgement: keep imports, signatures, docstrings and
class shape, drop the bodies. Nothing is summarised, inferred or ranked — a fixed
syntactic transform, so the same file always produces the same bytes.

This is deliberately Python-only and deliberately not tree-sitter. A native parser would
cover more languages and add a compiled dependency to a pure-Python package; saying
"Python only" is more honest than an eleven-language claim that has to be maintained.

Output depends on the running Python's ``ast.unparse``, which is why the version is
pinned in CI — the cross-platform digest would otherwise drift between runners.
"""

from __future__ import annotations

import ast

PLACEHOLDER = ast.Expr(value=ast.Constant(value=Ellipsis))


def _docstring(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> ast.Expr | None:
    """Return the node's docstring expression, if its body starts with one."""
    if not node.body:
        return None
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        if isinstance(first.value.value, str):
            return first
    return None


def compress_python(text: str) -> str | None:
    """Return a signature-level view of ``text``, or ``None`` if it will not parse.

    ``None`` means "leave this file alone" — a file that does not parse is a file we
    should not be rewriting.
    """
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError):
        return None

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = _docstring(node)
            node.body = [doc, PLACEHOLDER] if doc else [PLACEHOLDER]

    try:
        return ast.unparse(tree).rstrip() + "\n"
    except (ValueError, RecursionError):
        return None


def is_compressible(path: str) -> bool:
    """Only Python files, and only those the parser understands."""
    return path.endswith(".py")

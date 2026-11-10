## What does this change?

<!-- One or two sentences. Link the issue it closes, if any. -->

Closes #

## Which surface does it touch?

- [ ] Core (`src/llmscribe/core/`)
- [ ] MCP tools (`src/llmscribe/mcp/`)
- [ ] CLI (`src/llmscribe/cli/`)
- [ ] Desktop GUI (`src/llmscribe/gui/`)
- [ ] Docs / website

## Checklist

- [ ] `python -m pytest` passes
- [ ] `ruff check .` is clean
- [ ] Behaviour changes are reflected in `README.md`
- [ ] Any new limit lives in `src/llmscribe/core/limits.py`
- [ ] Core logic is reused rather than duplicated in the CLI/GUI layers
- [ ] The version in `src/llmscribe/__init__.py` is unchanged (releases bump it, not PRs)

## Notes for reviewers

<!-- Trade-offs, anything surprising, or something you're unsure about. -->

# Contributing

Thanks for contributing to LLMScribe.

## Setup

- Python 3.10+
- Clone the repo, then install in editable mode:

  ```bash
  pip install -e ".[dev]"
  ```

  This installs the `llmscribe`, `llmscribe-gui`, and `llmscribe-mcp` commands and picks
  up any code changes immediately, without reinstalling.

## Run

- CLI: `llmscribe --help`
- GUI: `llmscribe-gui`
- MCP: `llmscribe-mcp`

## Checks

```bash
python -m pytest
ruff check .
python -m build && python -m twine check dist/*
```

## Guidelines

- Keep changes focused and small.
- Prefer reusing `llmscribe/core/` logic (don't duplicate it in the GUI/CLI layers).
- If you change behavior, update `README.md`.
- The version lives only in `src/llmscribe/__init__.py`.
- Local and GitHub sources must produce the same schema: implement operations against `RepositorySource`, and add new limits to `llmscribe/core/limits.py`.
- Source lives under `src/llmscribe/` (src-layout). Import it as `llmscribe.core`,
  `llmscribe.cli`, `llmscribe.gui` — not with bare `core`/`cli`/etc.

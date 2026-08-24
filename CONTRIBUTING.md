# Contributing

Thanks for contributing to LLMScribe.

## Setup

- Python 3.10+
- Clone the repo, then install in editable mode:

  ```bash
  pip install -e .
  ```

  This installs the `llmscribe`, `llmscribe-gui`, and `llmscribe-cui` commands and picks
  up any code changes immediately, without reinstalling.

## Run

- CLI: `llmscribe --help`
- GUI: `llmscribe-gui` (or `llmscribe --gui`)
- Terminal menu: `llmscribe-cui`

## Guidelines

- Keep changes focused and small.
- Prefer reusing `llmscribe/core/` logic (don't duplicate it in the GUI/CLI/CUI layers).
- If you change behavior, update `README.md`.
- Source lives under `src/llmscribe/` (src-layout). Import it as `llmscribe.core`,
  `llmscribe.cli`, `llmscribe.cui`, `llmscribe.gui` — not with bare `core`/`cli`/etc.

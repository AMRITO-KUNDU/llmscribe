# Contributing

Thanks for contributing to LLMScribe.

Two short documents explain the project before you invest time: [VISION.md](VISION.md)
covers what is in scope and what deliberately is not, and [GOVERNANCE.md](GOVERNANCE.md)
covers how decisions are made.

Participation is covered by the [Code of Conduct](CODE_OF_CONDUCT.md), which applies in
all project spaces. For security issues, follow [SECURITY.md](SECURITY.md) rather than
opening a public issue.

## What kinds of contributions are welcome

- **Bug reports** — use the issue form and include the version and interface.
- **Documentation fixes** — genuinely useful, and easy to review.
- **Bug fixes with a test** that fails before the change and passes after it.
- **New capabilities that fit [VISION.md](VISION.md)** — please open an issue first.

Not accepted: AI features, embeddings or ranking, hosted services, and anything that
makes output non-deterministic. VISION.md explains why for each.

## What to expect from a review

- **Response time:** a first response within about **7 days**. This is a part-time
  project. If a week passes with no reply, ping the thread — that is helpful, not rude.
- **What we look for:** correctness, tests, and whether the change fits the scope. Small,
  focused pull requests get merged fastest.
- **Saying no:** if a change doesn't fit, you'll get the reason and the criterion in
  VISION.md it failed. That is a decision about scope, not about the quality of your work.

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
- If you change behavior, update `README.md` and `CHANGELOG.md`.
- The version lives only in `src/llmscribe/__init__.py`, and only maintainers bump it.
- Implement operations against `RepositorySource` so every surface shares one code path,
  and add new limits to `llmscribe/core/limits.py`.
- Source lives under `src/llmscribe/` (src-layout). Import it as `llmscribe.core`,
  `llmscribe.cli`, `llmscribe.gui` — not with bare `core`/`cli`/etc.

## Good first issues

Issues labelled [`good first issue`](https://github.com/AMRITO-KUNDU/llmscribe/labels/good%20first%20issue)
are scoped to be self-contained. If one is stale or unclear, say so in the thread — that
is a documentation bug worth fixing.

## Accessibility

UI changes (website, GUI) must keep the guarantees listed in
[ACCESSIBILITY.md](ACCESSIBILITY.md): visible focus, accessible names on interactive
elements, decorative images hidden from assistive technology, and no meaning conveyed by
colour alone. Test any new interactive component with the keyboard only before opening
the pull request.

## Questions

Ask in an issue. Please keep project discussion public so the next person can find the
answer.

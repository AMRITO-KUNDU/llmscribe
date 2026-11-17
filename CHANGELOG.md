# Changelog

All notable changes to LLMScribe are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Repositioned the project around the problem it actually solves: an agent's only
  interface to a codebase is the shell, and `ls` / `find` / `grep` / `cat` are
  human-facing, OS-specific and unstructured. The README, website, `llms.txt`, package
  metadata and VISION.md now lead with that, including a Linux-vs-Windows command table.

### Added

- `--depth N` on `map` and `overview` (`max_depth=` in Python, `depth=` over MCP).
  Limits the listing to the first N path levels, like `tree -L N`. It prunes the tree
  *and* the file list, so `overview --depth 2` never reads the files it excluded.

### Fixed

- The homepage demo worked but read as broken: it told you to "select a project
  folder" when the folder field is a static sample, reported "Saved to
  project_overview.txt" when nothing had been saved, and labelled a download button
  "Open file". The copy now matches what the demo actually does.
- The website's Python API sample was wrong in three ways: it imported `search` from
  `llmscribe.core` (a module, not a function), it called `project_overview(path=...,
  format="json")` with keywords that do not exist, and it referenced
  `llmscribe.mcp.server` internals. It now shows the `Repository` API, and a test
  executes the sample straight out of `site.ts` so it cannot rot again.
- The website's JSON sample was not valid JSON. A `\n` inside a TypeScript template
  literal becomes a real newline, which is illegal inside a JSON string, and the sample
  was missing `source`, `command` and most of the `data` fields. It is now generated
  from an actual envelope.
- The Python API section and feature card still described `llmscribe.core.writer`.

## [1.4.1] — 2026-11-17

### Fixed

- The Windows GUI executable now carries the brand icon **in the window**, not only on
  the file. The icon is bundled into the one-file build (`--add-data`) and resolved via
  `sys._MEIPASS`, which is where PyInstaller unpacks; the old repo-relative path does not
  exist inside a bundle, so the window silently fell back to the default Tk feather.
- `docs/public/favicon.ico` is now a real multi-resolution icon (16, 24, 32, 48, 64, 128
  and 256 px) instead of a single 32px image, so Explorer's large-icon view and the
  Alt-Tab switcher no longer upscale a small bitmap. This also improves the browser
  favicon.
- `build_exe.py` fails the build if the icon is missing, rather than quietly producing an
  unbranded executable.

## [1.4.0] — 2026-11-17

### Added

- `CODE_OF_CONDUCT.md`, GitHub issue forms, a pull request template and `ACCESSIBILITY.md`.
- `VISION.md` — what the project is for, and what is explicitly out of scope.
- `GOVERNANCE.md` — roles, how decisions are made, maintainer boundaries, and how to
  become a maintainer.
- `SUPPORT.md` — where to ask for what, and what support actually looks like.
- This changelog.
- Dependabot configuration and a CodeQL code-scanning workflow.
- A dedicated accessibility issue template.
- `llmscribe.Repository`: a public Python API. `from llmscribe import Repository` gives
  one object with `map`, `overview`, `search`, `read`, `read_many`, `dependencies` and
  `diff`, returning the same dataclasses as the CLI and MCP server. Imported lazily, so
  `import llmscribe` stays instant.
- `examples/`: runnable scripts for RAG ingestion, PR review and a repo summary.
- Centralised versioning: `scripts/sync_version.py` propagates `__version__` to
  `server.json`, `llms.txt`, `site.ts` and `__root.tsx`, and CI fails if any of them
  drifts. `pyproject.toml` already read the version dynamically.

### Changed

- Redesigned the social preview card (`og.png`) in the project's own type
  (Instrument Serif and IBM Plex) with a framed composition and a project-tree motif.
- `og:image` is versioned (`?v=2`) so crawlers refetch instead of serving a cached image.
- Removed the word "deterministic" from the README, website, package metadata and
  docstrings, where it had become filler. It now appears exactly once, in the
  Philosophy section, stating the guarantee next to its plain-English form:
  same input, same bytes, every run.

### Fixed

- The website now declares the `.ico` favicon and an `apple-touch-icon`, so browsers
  that ignore SVG favicons (notably Safari) show an icon.
- `CODE_OF_CONDUCT.md` now names who receives a report, and gives an independent route
  for a report about the maintainer.
- Removed a stale `DirScribe` ignore rule and a duplicate cache rule from `.gitignore`.
- Piping the CLI into a program that stops early (`llmscribe overview . | head`) no longer
  dumps a `BrokenPipeError` traceback; it exits quietly with status 0.

## [1.3.0] — 2026-10-25

### Changed

- **Breaking:** the online GitHub source was removed. The `repo` and `ref` arguments are
  gone from every tool; all tools now read a local project directory.
- The MCP server is **stdio-only**. The hosted HTTP transport, the in-memory snapshot
  cache and the `uvicorn` dependency were removed.
- Local paths are allowed by default; `MCP_ALLOWED_ROOTS` restricts them, and
  `MCP_ALLOW_LOCAL_PATHS=0` disables them.

### Removed

- `llmscribe.github`, `llmscribe.mcp.asgi`, and the Docker / Render / Railway deployment files.

### Fixed

- The MCP server now reports its real version in the `initialize` handshake; it was empty.

## [1.2.1] — 2026-10-13

### Added

- MCP Registry metadata (`server.json`).

### Fixed

- CI lint failures in the CLI, GUI entrypoint and GitHub client.
- The MCP registration test, for the 2.x SDK schema field.
- The GUI download link now points at the latest GitHub Release.

## [1.2.0] — 2026-10-02

### Added

- GitHub repository source support (`repo=` / `ref=`).
- Dependency analysis (`project_dependencies`): local, stdlib, external and unresolved
  imports, plus reverse dependencies.
- Structured JSON output, stable error codes, truncation limits and agent recipes.
- `project_diff`, `format` support, and `build_exe.py` for a standalone Windows GUI.

### Changed

- MCP server refactor and CLI modernisation.

## [1.0.0] — 2026-08-24

Initial public release: CLI, MCP server, desktop GUI and Python API over a
repeatable project walk.

[Unreleased]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.4.1...HEAD
[1.4.1]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/AMRITO-KUNDU/llmscribe/releases/tag/v1.0.0

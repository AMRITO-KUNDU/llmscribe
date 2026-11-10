# Changelog

All notable changes to LLMScribe are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `CODE_OF_CONDUCT.md`, GitHub issue forms, a pull request template and `ACCESSIBILITY.md`.
- `VISION.md` — what the project is for, and what is explicitly out of scope.
- `GOVERNANCE.md` — roles, how decisions are made, maintainer boundaries, and how to
  become a maintainer.
- `SUPPORT.md` — where to ask for what, and what support actually looks like.
- This changelog.
- Dependabot configuration and a CodeQL code-scanning workflow.
- A dedicated accessibility issue template.

### Changed

- Redesigned the social preview card (`og.png`) in the project's own type
  (Instrument Serif and IBM Plex) with a framed composition and a project-tree motif.
- `og:image` is versioned (`?v=2`) so crawlers refetch instead of serving a cached image.

### Fixed

- The website now declares the `.ico` favicon and an `apple-touch-icon`, so browsers
  that ignore SVG favicons (notably Safari) show an icon.
- `CODE_OF_CONDUCT.md` now names who receives a report, and gives an independent route
  for a report about the maintainer.
- Removed a stale `DirScribe` ignore rule and a duplicate cache rule from `.gitignore`.

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
deterministic project walk.

[Unreleased]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/AMRITO-KUNDU/llmscribe/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/AMRITO-KUNDU/llmscribe/releases/tag/v1.0.0

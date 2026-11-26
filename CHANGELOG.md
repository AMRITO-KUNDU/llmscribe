# Changelog

All notable changes to LLMScribe are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] — 2026-11-26

**Behaviour change:** secrets are now masked by default in every result. If you diff
LLMScribe output against 1.4.x you will see `[REDACTED:<kind>]` where a credential used
to be. `--no-redact` restores the old output.

### Changed

- Repositioned the project around the problem it actually solves: an agent's only
  interface to a codebase is the shell, and `ls` / `find` / `grep` / `cat` are
  human-facing, OS-specific and unstructured. The README, website, `llms.txt`, package
  metadata and VISION.md now lead with that, including a Linux-vs-Windows command table.

### Added

- `--compress` reduces Python files to imports, signatures and docstrings, dropping
  bodies — roughly half the characters on a typical module. Uses the standard library
  parser, so it is a fixed syntactic transform with no inference and no ranking; files
  that fail to parse are returned untouched. `compressed_files` reports what was
  reduced. Python only, by choice: a multi-language parser would add a compiled
  dependency to a pure-Python package.
- `--max-tokens N` (`max_tokens=` in Python and MCP) spends a context budget by taking
  files in path order until it runs out — never by relevance, which would be ranking.
  Tokens are estimated at four characters. `0` or negative is rejected as
  `invalid_argument`. The ordering rule is written into VISION.md so it cannot drift.
- **Secrets are masked before they reach a model.** `core/redact.py` recognises AWS,
  GitHub, Slack, Stripe, Google and OpenAI key shapes, JWTs, bearer headers, credentials
  in connection strings, private-key blocks and `password = "..."` assignments, replacing
  each with a fixed `[REDACTED:<kind>]` marker. Applied at one choke point in
  `service.execute` so every tool is covered, and in the Python API. On by default,
  including for MCP clients; `--no-redact` / `redact=False` opts out. The result reports
  what was masked in `metadata.redacted` rather than masking silently.
- `map --sizes` / `include_sizes=True` adds each file's byte size to the listing, which
  is what `list_directory_with_sizes` gives you in the official filesystem server.
  Opt-in, so the default output is unchanged.
- `read` reports `modified` (ISO 8601 UTC) alongside `byte_size` and `line_count`.
- `read --binary` returns any file as base64 with its guessed `media_type`, for images
  and PDFs. Binaries stay excluded from `overview` and `read_many`, so the default
  cannot fill a context window with them.
- A "Where this fits" section comparing against `@modelcontextprotocol/server-filesystem`
  and stating plainly that LLMScribe is the read half: it does not write, edit or move,
  by design.
- `read` and `read_many` now report `byte_size` and `line_count` for the whole file,
  alongside the content. That is the `stat` / `wc -l` / `file` information in the same
  shape on every OS, and it stays correct when the body is clipped.
- `scripts/cross_platform_check.py` plus a `Cross-platform output` workflow that runs it
  on Ubuntu, macOS and Windows and fails if the digests differ. "Same output everywhere"
  is now enforced rather than asserted.
- `--depth N` on `map` and `overview` (`max_depth=` in Python, `depth=` over MCP).
  Limits the listing to the first N path levels, like `tree -L N`. It prunes the tree
  *and* the file list, so `overview --depth 2` never reads the files it excluded.

### Fixed

- The website's `<title>`, meta description and image alt text were duplicated in
  `__root.tsx` instead of read from `SITE`, and had drifted: the title still said "one
  file, the whole project" and the alt text "turn any repository into structured,
  LLM-ready context", neither of which describes the product. They now derive from
  `SITE`, the description is 140 characters so Google will not truncate the
  cross-platform half, and a test names the retired strings so they cannot return.
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
- The cross-platform check compared the wrong paths on macOS: `/var` is a symlink to
  `/private/var`, so the scrub replaced a path the tool never reported and the absolute
  temp directory leaked into the digest. It also wrote its report with the platform
  newline, so Windows produced CRLF and every line differed by one byte. Both were bugs
  in the harness, not the tool — which is why `read` matched on all three OSes and
  `map`/`overview`/`search` did not.

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

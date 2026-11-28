# Changelog

All notable changes to LLMScribe are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`--read-only` mode** for the MCP server (`LLMSCRIBE_READ_ONLY=1` also works). The seven
  write tools are never registered, so a client does not list them and a call fails as an
  unknown tool — stronger than refusing at call time, because a model cannot ask for what
  it cannot see.
- **`append_file`** and **`copy_file`**, bringing the surface to fourteen tools. Append is
  atomic and keeps the file's encoding; copy is byte-for-byte and binary-safe. Both are
  hidden in read-only mode.
- Every path parameter now carries a `pattern` in the tool schema, so the boundary is
  visible to the model rather than discovered by failing. It mirrors the runtime check: no
  absolute paths, no `..` segments, no backslashes, no NUL bytes.

### Added

- `read` returns a `revision` — a short fingerprint of the file's bytes — and `edit_file`
  and `write_file` accept `expect_revision`. If the file changed since it was read, the
  write is refused with `conflict` instead of overwriting someone else's change. This is
  the lost-update case: an agent reads a file, a human edits it, the agent writes, and the
  human's work disappears.

### Fixed

- The atomic write now uses `mkstemp` for its temporary file, so two concurrent writers
  cannot pick the same name, and it calls `fsync` before the replace.
- **Read-only files are no longer overwritten.** On POSIX, replacing a file depends on
  write permission on the directory, not the file, so an atomic replace would happily
  clobber a `chmod 444` file. Both the file and its directory are now checked, and the
  result is `permission_denied`.
- Filesystem failures now map to codes a caller can act on: `no_space` (and the message
  says the original is untouched), `path_too_long` (naming the 260-character Windows
  limit), `permission_denied`, and `invalid_path` for a directory target. Windows
  `winerror` values are mapped alongside POSIX errno.
- No temporary file survives a failed write.

## [3.0.1] — 2026-11-27

**If you edit files with LLMScribe, take this update.** 3.0.0 shipped an hour earlier with
a bug that silently damaged non-UTF-8 files. Everything below is a fix; nothing changed in
the API.

```bash
pip install --upgrade 'llmscribe[server]'
```

### Fixed

Five encoding defects, all the same shape: the tool believed something about a file's
bytes that was not true.

- **`edit_file` corrupted non-UTF-8 files.** It decoded with a permissive UTF-8 read and
  wrote back as UTF-8, so editing one line of a cp1252 source file re-encoded every other
  byte and destroyed the non-ASCII ones — `é` became `\ufffd`, and the edit reported
  success. It now decodes with the same detector the read side uses, writes back in the
  file's own encoding, and preserves a UTF-8 or UTF-16 byte-order mark.
- **`write_file` did the same** when replacing an existing file. It now keeps the file's
  encoding and BOM; `encoding="utf-8"` (or `--encoding utf-8`) converts deliberately.
- **A lone surrogate raised `UnicodeEncodeError`** straight through the service layer — a
  traceback rather than an error. It is now `encoding_error`, and nothing is written.
- **`read` showed `\ufffd` for bytes its encoding could not map and said nothing**, so an
  agent could not tell a file with an odd byte from a corrupted one. It now reports
  `lossy: true` and `replaced_bytes`; `overview` lists them in `lossy_files`.
- **`diff` decoded Git's output as UTF-8 with replacement.** Git does not transcode, so a
  cp1252 file's diff was mojibake. It uses the same detector as everything else now.

A text that cannot be represented in the file's encoding is refused with
`encoding_error` and the file is left byte-identical — an emoji written into a cp1252 file
fails rather than writing `?`.

18 encoding tests cover cp1252, UTF-8, UTF-8-with-BOM and UTF-16 in both directions: a
read-then-write round trip changes no bytes, and a refused conversion leaves the file
untouched.

## [3.0.0] — 2026-11-27

**This release changes what LLMScribe is allowed to do: it writes.**

If you pointed it at a repository because it could only read, that guarantee is gone.
An agent holding this can now create, edit, move and delete files. Nothing about the
install changes, but the decision does — if you want the old behaviour, pin
`llmscribe<3`.

The reversal is deliberate. An earlier VISION.md said LLMScribe would never edit your
code; that was wrong. A filesystem layer an agent cannot write through is a file viewer,
and it forces whoever is building the agent back to shell commands — the exact problem
this project exists to remove. What stays out of scope is *deciding* what to write: the
layer performs operations, it does not choose them.

### Added

- **Five write operations** — `write_file`, `edit_file`, `create_directory`, `move_file`,
  `delete_file` — on every surface: MCP, CLI, Python API and the framework adapters.
  Twelve tools now.
- Every write is confined to the project root with the same traversal and symlink checks
  the read side uses, and is atomic (temporary file then `os.replace`), so an interrupted
  write leaves the original intact rather than a half-written file.
- `edit_file` replaces an exact substring and fails with `no_match` or `ambiguous_match`
  rather than guessing which occurrence was meant.
- CLI: `write` (`tee`), `edit` (`sed`), `mkdir`, `mv`, `rm`. `write` reads stdin when no
  `--content` is given, so it composes in a pipe.
- **Line ranges on `read`**: `--lines 200:250` returns 51 lines of a 5,000-line file
  instead of all 5,000. `line_count` still reports the whole file and `returned_lines`
  reports the slice. Cannot be combined with `--compress`, since compression rewrites the
  file and line numbers would stop meaning what was asked for.
- **`read_many` accepts `start_line`/`end_line`**, applied to every file in the batch.
- **CLI aliases** for the commands agents reach for out of habit: `ls`, `tree`, `grep`,
  `find`, `cat`, `cat-many`, `deps`. Normalised to the canonical command before dispatch,
  so behaviour is identical — a test compares the JSON output of both.
- **LlamaIndex adapter** (`as_llamaindex_tools`), completing the set of five. It builds a
  callable with a real signature, because LlamaIndex derives tool parameters from the
  signature and a `**kwargs` wrapper would produce a tool that takes nothing.

### Fixed

- The CI smoke test imported `llmscribe.mcp` from a core-only wheel, which fails now that
  the server lives behind an extra. It tests both installs.
- Adapter tests were skipping silently in CI — `importorskip` plus a `dev` extra that does
  not include the frameworks. A job now installs every adapter and fails if a test skips.
- The README claimed six CLI aliases that did not exist. They exist now.

### Changed

- Brand copy rewritten in plain language across the README, the site, the PyPI summary,
  the MCP registry entry and the GitHub description. The old tagline was a list of search
  terms; the new one is a statement.

## [2.0.0] — 2026-11-26

### Upgrading from 1.x — one command

The MCP server moved behind an extra, so the core package stays at a single dependency.
If you use the MCP server, reinstall with the extra:

```bash
pip install --upgrade 'llmscribe[server]'
```

If you only use the CLI or the Python API, `pip install --upgrade llmscribe` is enough
and you get a faster, lighter install. Without the extra, `llmscribe-mcp` prints that
install line and exits, rather than failing with an ImportError — so an MCP client will
report that the server did not start until you add `[server]`.

This is the only breaking change in 2.0. The JSON envelope gained a field; nothing was
removed from it.

### Added

- **Use it as a library.** `tool_schemas("openai" | "anthropic" | "mcp" | "raw")` and
  `Repository.handlers()` let a framework register LLMScribe's seven tools without
  hand-writing definitions. `llmscribe schema --format openai` prints the same from the
  CLI. Neither path imports pydantic or mcp.
- Adapters for **LangChain**, **PydanticAI**, **smolagents** and the **Anthropic Messages
  API**, in `llmscribe.adapters`. Each imports its framework lazily and raises a
  ModuleNotFoundError naming the pip command.
- `llmscribe.tools()` returns a neutral tool list (name, description, JSON Schema,
  handler) that any framework can consume.
- Every JSON envelope now carries `schema_version` (`"1.0"`), which changes only for a
  breaking change to the output contract.
- A bound tool set drops the `path` argument: a model must not be able to repoint the
  reader at another directory. `handlers()` never raises — failures come back as
  `{"ok": false, "error": {...}}` so an agent loop survives a bad path.

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

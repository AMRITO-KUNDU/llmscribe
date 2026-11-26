<!-- mcp-name: io.github.AMRITO-KUNDU/llmscribe -->
<a name="readme-top"></a>

<p align="center">
  <img
    src="https://raw.githubusercontent.com/AMRITO-KUNDU/llmscribe/main/docs/public/favicon.svg"
    height="120"
    alt="LLMScribe logo: read-only MCP server for AI coding agents"
  >
</p>

# LLMScribe: Read-Only MCP Server and Python Library for AI Coding Agents

<p align="center">
  <a href="https://pypi.org/project/llmscribe/"><img src="https://img.shields.io/pypi/v/llmscribe" alt="PyPI version"></a>
  <a href="https://pypi.org/project/llmscribe/"><img src="https://img.shields.io/pypi/pyversions/llmscribe" alt="Supported Python versions"></a>
  <a href="https://github.com/AMRITO-KUNDU/llmscribe/actions/workflows/cross-platform.yml"><img src="https://github.com/AMRITO-KUNDU/llmscribe/actions/workflows/cross-platform.yml/badge.svg" alt="Cross-platform output check"></a>
  <a href="https://github.com/AMRITO-KUNDU/llmscribe/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AMRITO-KUNDU/llmscribe" alt="Apache-2.0 license"></a>
  <a href="https://registry.modelcontextprotocol.io/?q=llmscribe"><img src="https://img.shields.io/badge/Official%20MCP%20Registry-listed-blue" alt="Listed in the official MCP Registry"></a>
  <a href="https://github.com/AMRITO-KUNDU/llmscribe/stargazers"><img src="https://img.shields.io/github/stars/AMRITO-KUNDU/llmscribe?style=social" alt="GitHub stars"></a>
</p>

**LLMScribe gives AI coding agents structured, deterministic access to a local codebase.** It is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server, command-line tool and Python library that returns a project map, literal code search, file contents, a dependency graph and Git diffs as stable JSON, with secrets masked and identical output on Linux, macOS and Windows.

No AI, no embeddings, no ranking, no network access, no account. Licensed under Apache-2.0.

**Works with:** Claude Code, Claude Desktop, Cursor, OpenAI Codex CLI, VS Code (GitHub Copilot), Windsurf, Zed, Cline, Roo Code, Continue, JetBrains IDEs, Goose, LM Studio and any other MCP client. Also available through `pip install`, LangChain, PydanticAI, smolagents, the Anthropic Messages API and a standalone Windows EXE.

[Install](#install) · [Quick start](#quick-start) · [MCP setup](#mcp-server-setup) · [CLI](#cli-reference) · [Python API](#python-library-and-framework-adapters) · [FAQ](#faq) · [Website](https://llmscribe.vercel.app)

---

## Table of contents

- [What is LLMScribe?](#what-is-llmscribe)
- [Features](#features)
- [Install](#install)
- [Quick start](#quick-start)
- [Tools](#tools)
- [MCP server setup](#mcp-server-setup)
- [Recommended agent workflow](#recommended-agent-workflow)
- [Tool details](#tool-details)
- [CLI reference](#cli-reference)
- [Token budgets and compression](#token-budgets-and-compression)
- [Secret redaction](#secret-redaction)
- [Python library and framework adapters](#python-library-and-framework-adapters)
- [Configuration](#configuration)
- [Behavior reference](#behavior-reference)
- [Comparison](#comparison)
- [Use cases](#use-cases)
- [FAQ](#faq)
- [Architecture](#architecture)
- [Contributing](#contributing)
- [Resources](#resources)
- [License](#license)

---

## What is LLMScribe?

An AI coding agent that wants to understand your repository normally has one interface: the shell. `ls`, `find`, `grep` and `cat` were built for a person reading a terminal, not for a program building a model of a codebase. Their output is formatted for eyes, differs between operating systems, and has to be re-parsed by the agent every time.

LLMScribe replaces that with seven structured operations that behave the same everywhere:

1. **Map** the project tree without reading any file.
2. **Search** paths and contents literally.
3. **Read** one file or many.
4. **Trace dependencies** in both directions.
5. **Diff** against Git.
6. **Overview** a whole small project in one call.
7. **Return everything as JSON**, with truncation always reported.

It is deliberately **read-only**. An agent holding LLMScribe can understand your repository but structurally cannot change or delete it.

**Why this matters in practice.** On a 1.4-million-line codebase, one benchmark agent burned 6,000 seconds and produced nothing — no analysis, no output. The same model, given structured code search instead of free-form file reading, finished the same task in **89 seconds** and scored 0.90. Across another benchmark, Codex CLI completed its whole turn sequence without ever reaching the file that would have solved the task in **27–29% of runs**. The bottleneck is not the model. It is what goes into the context window.

## Features

- **Project map**: full directory tree with contents excluded, optionally limited by depth.
- **Literal code search**: results ordered by path and line, with the matched text and match type. Never a silent empty result.
- **Safe file reads**: path traversal outside the project is blocked. Every read reports `byte_size`, `line_count` and `modified` for the whole file.
- **Line ranges**: `--lines 200:250` reads part of a large file instead of all of it.
- **Batch reads**: `read_many` supports partial success, so one bad path does not fail the request.
- **Dependency graph**: imports and reverse dependencies (`used_by`) for Python, JavaScript/TypeScript, Java, Go, Rust and C/C++.
- **Git status and diff**: staged, unstaged and per-commit unified diffs.
- **Context-window control**: `--depth`, `--max-tokens` and `--compress` fit large repositories into small contexts.
- **Secret redaction**: API keys, tokens, private keys and connection-string credentials are masked by default.
- **Real `.gitignore` semantics**: nested files, wildcards, directory rules and `!` negation.
- **Deterministic output**: same input, same bytes, on every run and every OS.
- **Local-only**: no network access, no hosted service, no telemetry.

---

## Install

```bash
pip install llmscribe              # core: map, search, read, dependencies, diff
pip install 'llmscribe[server]'    # adds the MCP server (llmscribe-mcp)
pip install 'llmscribe[adapters]'  # adds LangChain, LlamaIndex, PydanticAI and smolagents adapters
```

The core package has a single dependency (`pathspec`). The MCP server and framework adapters are optional extras, so a library user never pays for a protocol server they do not run. If you run `llmscribe-mcp` without the `server` extra, it prints the install command and exits instead of raising an `ImportError`.

A standalone Windows EXE is also available from the [Releases page](https://github.com/AMRITO-KUNDU/llmscribe/releases). The desktop GUI ships either as that EXE or as `pip install 'llmscribe[gui]'`, which provides the `llmscribe-gui` command.

Git is only needed for the `diff` tool.

---

## Quick start

### Use it as an MCP server

```bash
pip install 'llmscribe[server]'
claude mcp add llmscribe -- llmscribe-mcp
```

Then ask your agent to explore the project. Setup for every other client is in [MCP server setup](#mcp-server-setup).

### Use it from the command line

```bash
pip install llmscribe

llmscribe map --depth 2              # project tree, two levels deep
llmscribe search "authentication"    # literal search across paths and contents
llmscribe read src/auth/service.py   # one file, with size, line count and mtime
llmscribe dependencies src/auth/service.py --json
```

### Use it from Python

```python
from llmscribe import Repository

repo = Repository(".")
print(repo.map().tree)
print(repo.search("auth").match_count)
```

---

## Tools

Seven tools, identical across the MCP server, CLI and Python library.

| MCP tool | CLI command | What it does |
| --- | --- | --- |
| `project_map` | `llmscribe map` (alias `ls`) | Directory tree without file contents. Supports `--depth` and `--sizes`. |
| `project_overview` | `llmscribe overview` (alias `tree`) | Tree plus supported file contents. Supports `--depth`, `--compress` and `--max-tokens`. |
| `search` | `llmscribe search` (aliases `grep`, `find`) | Literal search across file paths, names, contents and lines. |
| `read` | `llmscribe read` (alias `cat`) | One file with `byte_size`, `line_count` and `modified`. `--binary` returns base64; `--lines START:END` reads part of it. |
| `read_many` | `llmscribe read-many` (alias `cat-many`) | Up to 50 files in one call, with per-file errors. `--lines START:END` applies to every file. |
| `project_dependencies` | `llmscribe dependencies` (alias `deps`) | What a file imports and what imports it. |
| `project_diff` | `llmscribe diff` | Git status and unified diffs. |

---

## MCP server setup

LLMScribe is a standard MCP server that runs locally over stdio. Install the server extra first:

```bash
pip install 'llmscribe[server]'
```

### Standard `mcpServers` configuration

Most clients accept this block:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

If `llmscribe-mcp` is not on your `PATH`, call the module instead:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "python",
      "args": ["-m", "llmscribe.mcp"]
    }
  }
}
```

Where to put it:

| Client | Where to add it | Notes |
| --- | --- | --- |
| **Claude Desktop** | `claude_desktop_config.json` (Settings → Developer → Edit Config). macOS: `~/Library/Application Support/Claude/`. Windows: `%APPDATA%\Claude\`. | Fully quit and reopen after saving. |
| **Cursor** | `.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` for all projects | Restart, then check Customize → MCPs. |
| **Windsurf (Cascade)** | `~/.codeium/mcp_config.json` (Settings → Cascade → MCP → View Raw Config) | Press refresh after saving. |
| **Cline** | MCP Servers → Configure → Configure MCP Servers | |
| **Roo Code** | Global `mcp_settings.json` (Edit Global MCP) or `.roo/mcp.json` (Edit Project MCP) | |
| **LM Studio** | `~/.lmstudio/mcp.json` (Windows: `%USERPROFILE%\.lmstudio\mcp.json`). In-app: Program → Install → Edit mcp.json | Follows Cursor's `mcp.json` notation. |
| **JetBrains IDEs** | Settings → Tools → AI Assistant → Model Context Protocol (MCP) → Add → As JSON | You can also click Import from Claude. |

### Clients with a different format

**Claude Code**

```bash
claude mcp add llmscribe -- llmscribe-mcp
```

Confirm with `claude mcp list`. Add `--scope user` to enable it in every project, or `--scope project` to share it with your team through `.mcp.json`.

**VS Code (GitHub Copilot)** uses `servers`, not `mcpServers`. Create `.vscode/mcp.json`:

```json
{
  "servers": {
    "llmscribe": {
      "type": "stdio",
      "command": "llmscribe-mcp"
    }
  }
}
```

Open Copilot Chat in Agent mode and click the tools icon to start the server.

**OpenAI Codex CLI**: add to `~/.codex/config.toml`:

```toml
[mcp_servers.llmscribe]
command = "llmscribe-mcp"
```

**Zed**: add to your settings (or Settings → AI → MCP Servers → Add Server):

```json
{
  "context_servers": {
    "llmscribe": {
      "command": "llmscribe-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

**Continue**: add to `~/.continue/config.yaml`, or a file under `.continue/mcpServers/`:

```yaml
name: LLMScribe
version: 1.0.0
schema: v1
mcpServers:
  - name: LLMScribe
    command: llmscribe-mcp
```

**Goose**: add an extension to `~/.config/goose/config.yaml`:

```yaml
extensions:
  llmscribe:
    name: llmscribe
    enabled: true
    type: stdio
    cmd: llmscribe-mcp
    args: []
    timeout: 300
```

The server is also listed in the [official MCP Registry](https://registry.modelcontextprotocol.io/?q=llmscribe) as `io.github.AMRITO-KUNDU/llmscribe`.

---

## Recommended agent workflow

Instead of pushing a whole repository into a context window, let the agent retrieve only what it needs:

```text
1. project_map()                              what is in this project?
      ↓
2. search("authentication")                   where is the relevant code?
      ↓
3. read("src/auth/service.py")                what does it say?
      ↓
4. project_dependencies("src/auth/service.py")  what does it touch, and what touches it?
      ↓
5. read_many([...])                           pull in the related files
```

For small and medium projects, `project_overview` returns the tree and supported file contents in one call. For large repositories, stay with `map → search → read`.

---

## Tool details

### Map

Generates a clean directory tree without file contents. This is the best first step in an unfamiliar repository.

```bash
llmscribe map
llmscribe map --depth 2    # first two levels only, like `tree -L 2`
llmscribe map --sizes      # add each file's size in bytes
llmscribe map --json
```

MCP: `project_map` or `project_map(depth=2)`.

`--depth N` (or `max_depth=N` in Python) keeps the first *N* path levels. A top-level file is depth 1, so `--depth 2` keeps `a/b.py` and drops `a/b/c.py`. It prunes both the tree and the file list, so `overview --depth 2` never reads the files it excluded.

```text
src/
├── api/
│   ├── routes.py
│   └── auth.py
├── models/
│   └── user.py
└── main.py
```

### Search

Searches file paths, file names, file contents and individual lines. Search is intentionally **literal**: LLMScribe does not guess what you meant.

```bash
llmscribe search "authentication"
llmscribe search "authentication" --json
```

Each match includes the file path, line number, matching line, matched text and match type (`filename` or `content`). Results are ordered by path then line and capped at 1,000 matches. Binary and oversized files are skipped.

```json
[
  {
    "file_path": "src/auth/service.py",
    "line_number": 12,
    "line_content": "def authenticate(user, password):",
    "match_type": "content",
    "matched_text": "authenticate"
  }
]
```

### Read

Retrieves a file. Paths are validated, and traversal outside the project is rejected.

```bash
llmscribe read src/auth/service.py
llmscribe read logo.png --binary    # base64 content plus media type
```

Every read reports `byte_size`, `line_count` and `modified` (ISO 8601, UTC) for the **whole file**, even when the returned body was clipped. That is the `stat`, `wc -l` and `file` information in one consistent shape on every OS.

```json
{ "file_path": "src/main.py", "byte_size": 2841, "line_count": 96, "modified": "2026-11-21T04:13:16+00:00", "truncated": false }
```

`--binary` is the only way to retrieve a non-text file. `content` becomes base64 and `media_type` carries the guessed MIME type. Binaries are still excluded from `overview` and `read_many`, so they cannot quietly fill a context window.

**Read part of a file.** `start_line` and `end_line` are 1-based and inclusive, so asking for lines 200–250 of a 5,000-line file returns 51 lines rather than 5,000:

```bash
llmscribe read src/big.py --lines 200:250
llmscribe read src/big.py --lines 498:      # from line 498 to the end
```

```python
repo.read("src/big.py", start_line=200, end_line=250)
```

`line_count` still reports the whole file and `returned_lines` reports the slice, so an agent can always tell there is more. A range cannot be combined with `--compress`: compression rewrites the file, so line numbers would stop referring to what you asked for.

### Read many

Retrieves several files in one operation. Partial success is supported, so one problematic file does not invalidate the request.

```python
read_many(["src/auth/service.py", "src/auth/models.py", "src/api/login.py"])
```

```bash
llmscribe read-many src/auth/service.py src/api/login.py
```

### Dependencies

Shows what a file depends on and what depends on it. Useful for estimating the impact of changing a file.

```bash
llmscribe dependencies src/auth/service.py --json
```

```text
src/auth/service.py
│
├── depends on
│   ├── auth/models.py
│   ├── auth/config.py
│   └── auth/utils.py
│
└── used by
    ├── api/login.py
    └── tests/test_auth.py
```

Supported languages: Python, JavaScript/TypeScript, Java, Go, Rust and C/C++. Each reference is classified as:

- `local`: resolved to a file or directory inside the project
- `stdlib`: part of the language's standard library
- `external`: not in the project, assumed third-party
- `unresolved`: a relative or local-looking reference that matches nothing

`used_by` lists the reverse dependencies.

### Diff

Reads repository changes from Git: status, unstaged changes, staged changes, specific commits and unified diffs. This lets an agent see not only the current state of the repository but **what changed**.

```bash
llmscribe diff
```

Git runs with an argument list, a 30-second timeout, a minimal environment and without external diff or textconv drivers.

### Overview

Produces a project snapshot: directory structure, supported text file contents and structured project information.

```bash
llmscribe overview
llmscribe overview --depth 3
llmscribe overview --compress --max-tokens 20000
```

---

## CLI reference

Every command accepts `--json` (`-j`) for machine-readable output, which makes the CLI a building block for scripts, automation and developer tooling.

```bash
llmscribe map
llmscribe overview
llmscribe search "authentication"
llmscribe read src/auth/service.py
llmscribe read-many src/auth/service.py src/api/login.py
llmscribe dependencies src/auth/service.py
llmscribe diff

llmscribe map --depth 2                  # first two levels
llmscribe overview --max-tokens 20000    # fit a context budget
llmscribe search "auth" --json           # machine-readable output
llmscribe -V                             # print the version
```

**Paths are flexible.** Every command takes an optional directory, so `--path` is never required:

```bash
llmscribe .                       # map the current directory
llmscribe ./src                   # map a specific directory
llmscribe map ./src               # the same, spelled out
llmscribe search "auth" ./src     # search inside a directory
```

**Aliases** for verbs you already type:

| Alias | Command |
| --- | --- |
| `ls` | `map` |
| `tree` | `overview` |
| `grep`, `find` | `search` |
| `cat` | `read` |
| `deps` | `dependencies` |

`read` accepts several files and switches to a batch read automatically: `llmscribe cat src/main.py src/util.py`.

---

## Token budgets and compression

Large repositories do not fit in a context window. LLMScribe gives you three predictable controls.

| Control | Effect |
| --- | --- |
| `--depth N` | Limits the tree and file list to the first *N* path levels. Excluded files are never read. |
| `--max-tokens N` | Stops once content reaches roughly *N* tokens, taking files in **path order**. |
| `--compress` | Reduces Python files to imports, signatures, docstrings and class shape. |

```bash
llmscribe overview --compress
llmscribe read src/service.py --compress
llmscribe overview --compress --max-tokens 20000
```

### Compression is a syntactic transform, not a summary

`--compress` uses the standard library parser to read a Python file and re-serialise its API surface without function bodies. On a typical module that is roughly half the characters. Nothing is inferred or ranked, and the same file always produces the same bytes.

- **Python only.** Supporting more languages would mean a compiled dependency in a pure-Python package.
- **Formatting is normalised.** `"` may become `'` and blank lines collapse, so compressed output is for reading, not diffing.
- **Files that do not parse are left exactly as they are.**

### Budgets spend in a fixed order

`--max-tokens` takes files in path order until the budget is gone. Choosing files by relevance would be ranking, which this project avoids on purpose. A predictable cut beats an unpredictable one: you can always raise the budget or read a specific file. Token counts are estimated at four characters each, because an exact count would depend on which model's vocabulary you meant.

Any cut is reported through `truncated`, `truncation_note` and `omitted_files`, so truncation is never hidden.

---

## Secret redaction

LLMScribe exists to put code in front of a model, so every result is scrubbed first: file contents, search hits and diffs. The result tells you what it masked.

```json
{ "content": "API_KEY = \"[REDACTED:openai_key]\"", "metadata": { "redacted": ["openai_key"] } }
```

Detected shapes include AWS keys, GitHub and Slack tokens, Stripe and Google keys, JWTs, `Authorization: Bearer` headers, credentials inside connection strings, private-key blocks and `password = "..."` assignments.

Matching is conservative: high-confidence token shapes with fixed replacements, so ordinary code is left alone and output stays repeatable.

Redaction is **on by default everywhere**, including the MCP server. Use `--no-redact` (CLI) or `redact=False` (Python) when you need raw text. An agent cannot turn it off.

---

## Python library and framework adapters

Use LLMScribe as a library without running a server.

```python
from llmscribe import Repository, LLMScribeError

repo = Repository(".")                  # or Repository(Path("."))

print(repo.map().tree)                  # tree, no file contents
print(repo.search("auth").match_count)

match = repo.read("src/app.py")         # returns a result, never raises
if match.ok:
    print(match.content)

batch = repo.read_many(["README.md", "missing.py"])   # per-file errors, never raises
print(batch.success_count, batch.error_count)

deps = repo.dependencies("src/app.py")  # raises LLMScribeError
print(deps.file_dependencies.local_dependencies)
print(deps.used_by)                     # what imports it
```

Two error conventions:

- `read` and `read_many` **return** results carrying `ok` and `error_code`, so a batch reports per-file failures.
- `dependencies` and `diff` **raise** `LLMScribeError`, whose `.code` is a stable machine-readable string.

Every method returns the same dataclasses the CLI and MCP server produce, each with `.to_dict()` for JSON.

### Register the tools in any agent framework

```python
from llmscribe import Repository, tool_schemas

schemas = tool_schemas("openai")        # or "anthropic", "mcp", "raw"
run = Repository(".").handlers()        # tool name -> callable

result = run["project_map"](depth=2)    # {'ok': True, 'data': {...}, ...}
```

`llmscribe schema --format openai` prints the same definitions from the CLI.

### Ready-made adapters

Adapters ship for **LangChain**, **LlamaIndex**, **PydanticAI**, **smolagents** and the **Anthropic Messages API** (no SDK needed):

```python
from llmscribe import Repository
from llmscribe.adapters import as_langchain_tools, as_llamaindex_tools, as_anthropic_tools

tools = as_langchain_tools(Repository("."))            # StructuredTool objects
tools = as_llamaindex_tools(Repository("."))           # FunctionTool objects
defs, dispatch = as_anthropic_tools(Repository("."))   # Messages API shape
```

Each adapter is exercised against the real framework in CI, on every push.

Each adapter imports its framework lazily and, if it is missing, tells you which `pip` command to run.

### Guarantees that make it safe to depend on

- **Handlers never raise.** A missing file returns `{"ok": False, "error": {...}}`, so an agent loop is not broken by a bad path.
- **`path` is not a tool argument.** A bound tool set cannot be repointed at another directory by the model.
- **`schema_version` is in every JSON envelope.** It changes only for a breaking change to the output contract.

Runnable examples are in [`examples/`](https://github.com/AMRITO-KUNDU/llmscribe/tree/main/examples): chunking a repository for a RAG pipeline, reviewing what a change touches, and generating a repository summary.

---

## Configuration

LLMScribe runs entirely on your machine and needs no configuration. Two optional environment variables restrict which directories the MCP server may read:

| Variable | Description | Default |
| --- | --- | --- |
| `MCP_ALLOWED_ROOTS` | Directories the tools may read, separated by `:` on POSIX and `;` on Windows | All paths |
| `MCP_ALLOW_LOCAL_PATHS` | `0` disables local path access entirely | Enabled |

---

## Behavior reference

### Ignore rules

Defaults (`.git`, `node_modules`, `venv`, `dist`, `build`, `.env`, `*.log` and more), the root `.gitignore` and nested `.gitignore` files are applied with real Git semantics: wildcards, directories, `!` negation and root-anchored patterns. Hidden files are included unless ignored. Symlinks are never followed or listed.

### Supported text files

Known source, config and documentation extensions, plus names such as `Dockerfile`, `Makefile`, `LICENSE` and `.gitignore`. Other files appear in the tree but cannot be read or searched.

### Limits

Defined in one place, `llmscribe.core.limits`:

| Limit | Value |
| --- | --- |
| Content characters per `project_overview` / `read_many` | 400,000 |
| Files per `read_many` | 50 |
| Search matches | 1,000 |
| Map entries | 20,000 |
| Size per file | 2 MiB |
| Diff characters | 200,000 |
| Scanned entries | 100,000 |

Anything cut is reported through `truncated`, `truncation_note` and `omitted_files`.

### Error codes

Every failure has a stable, machine-readable code:

`invalid_argument` · `invalid_path` · `file_not_found` · `unsupported_file_type` · `binary_file` · `file_too_large` · `read_error` · `not_a_repository` · `git_unavailable` · `unsupported_operation` · `internal_error`

```json
{"ok": false, "tool": "...", "error": {"code": "...", "message": "..."}}
```

### Deterministic and cross-platform, verified in CI

[`scripts/cross_platform_check.py`](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/scripts/cross_platform_check.py) builds a fixed fixture project, runs `map`, `overview`, `search`, `read`, `read_many` and `dependencies`, scrubs the absolute path and digests each result. The [cross-platform workflow](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/.github/workflows/cross-platform.yml) runs it on Ubuntu, macOS and Windows and **fails the build if the digests differ**:

```text
llmscribe <version>
python 3.12
map            <sha256>
map_depth2     <sha256>
overview       <sha256>
search         <sha256>
read           <sha256>
read_many      <sha256>
dependencies   <sha256>
combined       <sha256>   <- must be identical on all three
```

The fixture is written as bytes, not text, so the files are byte-identical on every platform. Writing text would turn `\n` into `\r\n` on Windows and make the comparison meaningless.

### Upgrading from older versions

- Legacy tool names (`project_get_file`, `project_get_files`, `project_search`, `project_list_files`) were replaced by `read`, `read_many` and `search`.
- Error code `path_traversal` is now `invalid_path`. `not_text_file` is now `unsupported_file_type`.
- In `project_dependencies` results, `all_local_files`, `all_external_deps` and `all_unresolved` were replaced by `used_by` and per-category lists. `stdlib_dependencies` was added.
- `llmscribe.core` functions raise `LLMScribeError`, not `FileNotFoundError`, for a bad root.
- **1.3.0:** online GitHub sources were removed, and LLMScribe is now local-only. The `repo` and `ref` arguments, the in-memory snapshot cache, the `llmscribe.github` package and the hosted HTTP transport are gone. Point the tools at a local `path`.

See the [changelog](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CHANGELOG.md) for full release notes.

---

## Comparison

### LLMScribe vs shell commands

| What the agent needs | Linux / macOS | Windows | LLMScribe |
| --- | --- | --- | --- |
| List a directory | `ls -la` | `dir /a` | `map` |
| Find files by name | `find . -name '*.py'` | `Get-ChildItem -Recurse -Filter *.py` | `search` |
| Search inside files | `grep -rn 'auth' .` | `Select-String -Pattern auth` | `search` |
| Read a file | `cat app.py` | `type app.py` | `read` |
| Compare versions | `diff -ru old new` | `fc /r` (not recursive) | `diff` |

Shell output is made for eyes (columns, colour, locale-dependent sort order, warnings mixed with results), is not portable between operating systems, and forces the agent to re-parse text. LLMScribe returns the same JSON and the same bytes everywhere.

### LLMScribe vs the filesystem MCP server

`@modelcontextprotocol/server-filesystem` is a good tool that does something LLMScribe deliberately does not: it **writes** (`write_file`, `edit_file`, `move_file`, `create_directory`). LLMScribe is the read half. Run both if your agent needs to change files as well as understand them.

| | server-filesystem | LLMScribe |
| --- | --- | --- |
| Read / write / move / create | Yes | **Read only** |
| Binary and media reads | Yes | Opt-in (`read --binary`) |
| File size and mtime | `get_file_info` | On every read, plus `map --sizes` |
| `.gitignore`-aware | No | Yes, real pathspec semantics |
| Dependency graph (imports **and** `used_by`) | No | Yes |
| Git diff and status | No | Yes |
| Truncation reported | No | Yes, with `omitted_files` |
| Secret redaction | No | Yes, on by default |

An agent holding a write-capable server can delete your repository. One holding LLMScribe structurally cannot, which is a property of the design and not a missing feature.

---

## Use cases

- Giving AI coding agents (Claude Code, Cursor, Codex, Copilot) reliable codebase context
- Building MCP applications and local LLM tools
- Code search and repository explorer interfaces
- Impact analysis before changing a file
- Chunking repositories for RAG and code analysis pipelines
- Documentation generation and repository summaries
- Automation scripts that need stable, parseable project data
- Exploring unfamiliar open-source projects

---

## FAQ

### What is LLMScribe?

LLMScribe is an open-source, read-only MCP server, CLI and Python library that gives AI coding agents structured access to a local codebase: project map, literal search, file reads, dependency graph and Git diff, returned as deterministic JSON.

### How do I install the LLMScribe MCP server?

Run `pip install 'llmscribe[server]'`, then add `llmscribe-mcp` as a command in your client's MCP configuration. For Claude Code that is `claude mcp add llmscribe -- llmscribe-mcp`. See [MCP server setup](#mcp-server-setup) for other clients.

### Which AI coding tools does LLMScribe work with?

Any MCP client, including Claude Code, Claude Desktop, Cursor, OpenAI Codex CLI, VS Code with GitHub Copilot, Windsurf, Zed, Cline, Roo Code, Continue, JetBrains IDEs, Goose and LM Studio.

### Does LLMScribe use AI or embeddings?

No. There are no models, no embeddings and no semantic ranking. Search is literal, and compression is a fixed syntactic transform. The same input always produces the same bytes.

### Does LLMScribe send my code anywhere?

No. It runs entirely on your machine with no network access, account, hosted service or telemetry.

### Can an agent modify my files through LLMScribe?

No. LLMScribe is read-only by design. It has no write, edit, move or delete operations.

### How do I fit a large repository into a context window?

Start with `llmscribe map --depth 2`, then use `search` and `read --lines 200:250` to pull in only the part that matters. For overviews, combine `--depth`, `--compress` and `--max-tokens`. Anything omitted is reported in `omitted_files`.

### Are secrets and API keys exposed to the model?

High-confidence secret shapes (cloud keys, tokens, JWTs, private keys, connection-string credentials) are masked in file contents, search results and diffs by default, and the result lists what was redacted.

### Which languages does dependency analysis support?

Python, JavaScript/TypeScript, Java, Go, Rust and C/C++. Compression (`--compress`) supports Python only.

### Does LLMScribe work on Windows?

Yes. CI runs on Ubuntu, macOS and Windows and fails if the output differs between them.

### How is LLMScribe different from the filesystem MCP server?

The filesystem server reads and writes. LLMScribe only reads, but adds a dependency graph, Git diff, `.gitignore` semantics, secret redaction and explicit truncation reporting. See the [comparison](#comparison).

### Can I use LLMScribe without MCP?

Yes. Use the `llmscribe` CLI, the `Repository` Python class, or the LangChain, PydanticAI, smolagents and Anthropic adapters.

### What license is LLMScribe under?

Apache License 2.0.

---

## Architecture

All interfaces share one core engine, so behavior is consistent everywhere.

```text
                         Repository
                             │
                             ▼
                        Local Project
                             │
                             ▼
                     LLMScribe Core
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
       ▼                     ▼                     ▼
      CLI                   MCP                   GUI
       │                     │
       └──────────────┬──────┘
                      ▼
              Structured Output
                   / JSON
```

**In scope:** repository extraction, literal search, structured project data, file retrieval, dependency information, Git information and multiple interfaces.

**Out of scope:** AI-generated answers, embedding-based search, semantic ranking, autonomous coding, an AI coding agent and a general-purpose Git client. See [VISION.md](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/VISION.md).

---

## Contributing

Contributions are welcome: repository extraction, search, dependency analysis, interfaces, integrations and documentation.

Start with the [vision](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/VISION.md), which sets out what is in scope, then the [contributing guide](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md).

- Expect a first response within about **7 days**. This is a part-time project, and pinging a quiet thread is welcome.
- Issues labelled **`good first issue`** are scoped to be self-contained.
- Ask questions in an [issue](https://github.com/AMRITO-KUNDU/llmscribe/issues) so the next person can find the answer.
- LLMScribe is maintained by [@AMRITO-KUNDU](https://github.com/AMRITO-KUNDU). [GOVERNANCE.md](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/GOVERNANCE.md) describes how decisions are made.

Report vulnerabilities as described in [SECURITY.md](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/SECURITY.md).

<a href="https://github.com/AMRITO-KUNDU/llmscribe/graphs/contributors">
  <img alt="LLMScribe contributors" src="https://contrib.rocks/image?repo=AMRITO-KUNDU/llmscribe"/>
</a>

---

## Resources

- [Website and docs](https://llmscribe.vercel.app)
- [PyPI package](https://pypi.org/project/llmscribe/)
- [Official MCP Registry listing](https://registry.modelcontextprotocol.io/?q=llmscribe) (`io.github.AMRITO-KUNDU/llmscribe`)
- [Issues](https://github.com/AMRITO-KUNDU/llmscribe/issues) · [Changelog](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CHANGELOG.md) · [Support](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/SUPPORT.md)
- [Contributing](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md) · [Vision](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/VISION.md) · [Governance](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/GOVERNANCE.md)
- [Code of Conduct](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CODE_OF_CONDUCT.md) · [Accessibility](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/ACCESSIBILITY.md) · [Security](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/SECURITY.md)

### Star history

<a href="https://www.star-history.com/?repos=amrito-kundu%2Fllmscribe&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=amrito-kundu/llmscribe&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=amrito-kundu/llmscribe&type=date&legend=top-left" />
   <img alt="LLMScribe GitHub star history chart" src="https://api.star-history.com/chart?repos=amrito-kundu/llmscribe&type=date&legend=top-left" />
 </picture>
</a>

---

## License

LLMScribe is licensed under the [Apache License 2.0](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/LICENSE).

<div align="center">

<a href="#readme-top">↑ Back to top</a>

</div>

<!-- mcp-name: io.github.AMRITO-KUNDU/llmscribe -->
<h3 align="center">
  <a name="readme-top"></a>
  <img
    src="https://raw.githubusercontent.com/AMRITO-KUNDU/llmscribe/main/docs/public/favicon.svg"
    height="200"
    alt="LLMScribe"
  >
</h3>

<div align="center">
  <a href="https://github.com/AMRITO-KUNDU/llmscribe/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/AMRITO-KUNDU/llmscribe" alt="License">
  </a>
  <a href="https://pypi.org/project/llmscribe/">
    <img src="https://img.shields.io/pypi/v/llmscribe" alt="PyPI Version">
  </a>
  <a href="https://pepy.tech/project/llmscribe">
    <img src="https://static.pepy.tech/badge/llmscribe" alt="Downloads">
  </a>
  <a href="https://github.com/AMRITO-KUNDU/llmscribe/graphs/contributors">
    <img src="https://img.shields.io/github/contributors/AMRITO-KUNDU/llmscribe.svg" alt="GitHub Contributors">
  </a>
  <a href="https://llmscribe.vercel.app">
    <img src="https://img.shields.io/badge/Visit-llmscribe.vercel.app-orange" alt="Visit llmscribe.vercel.app">
  </a>
  <a href="https://registry.modelcontextprotocol.io/?q=llmscribe">
    <img src="https://img.shields.io/badge/Official%20MCP%20Registry-active-blue" alt="Official MCP Registry">
  </a>
</div>

<div>
  <p align="center">
    <a href="https://x.com/amritokundu719">
      <img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X" />
    </a>
    <a href="https://github.com/AMRITO-KUNDU">
      <img src="https://img.shields.io/badge/Follow%20on%20GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="Follow on GitHub" />
    </a>
  </p>
</div>

---

# **LLMScribe**

**Turn any code repository into clean, structured, deterministic data.** No AI. No embeddings. No hidden ranking. Open source and available as a [free hosted MCP](#mcp).


<a href="https://github.com/AMRITO-KUNDU/llmscribe">
  <img src="https://img.shields.io/github/stars/AMRITO-KUNDU/llmscribe.svg?style=social&label=Star&maxAge=2592000" alt="GitHub stars">
</a>

---

## The problem

Your agent does not have an intelligence problem. It has a **retrieval** problem.

On a 1.4-million-line codebase, one benchmark agent burned 6,000 seconds and produced nothing — no analysis, no output, zero score. The same model, given structured code search instead of free-form file reading, finished the same task in **89 seconds** and scored 0.90. Across another benchmark, Codex CLI completed its entire turn sequence without ever reaching the file that would have solved the task in **27–29% of runs**. Handed the right context up front, its score nearly doubled.

The bottleneck is not the model. It is what goes into the context window.

What users keep reporting:

- The agent explores 200 files to change one line, and admits it is "looking at unnecessary files"
- Nine searches and fourteen files to find one constant, because the search itself is not ranked
- The same files re-read in a loop, with no reasoning between the reads
- Stale fixtures, mock data and outdated comments read as current truth
- Search reporting "no matches found" when a plain `grep` finds the text immediately
- Truncation that hides itself, and build output filling the window with noise

## What LLMScribe does about it

| The failure | What LLMScribe does |
| --- | --- |
| Reads 200 files to change one line | `project_map` returns the whole tree with contents excluded, before a single file is read |
| Re-reads the same files in a loop | Output is deterministic — same input, same bytes, every run |
| Misses the file that actually mattered | `project_dependencies` resolves local, stdlib, external and unresolved imports, plus reverse dependencies |
| Search returns nothing when the text exists | `search` returns path, line, matched text and match type, or a stable error code — never a silent empty |
| Stale fixtures read as current truth | Nothing is inferred, embedded or ranked; you get the files as they are, plus a Git diff |
| Build output and binaries fill the context | Real `.gitignore` semantics; binaries and oversized files are skipped |
| Context silently truncated | Every cut is reported: `truncated`, `truncation_note`, `omitted_files` |

> The file an agent needs next is usually the one *structurally* related to the file it is already looking at — a dependent, a sibling module, a test fixture. That is a graph question, not a similarity question, which is why LLMScribe ships dependency analysis and a real tree instead of embeddings.

---

## Feature Overview

**Core Tools**

| Feature | Description |
|---------|-------------|
| [**Map**](#map) | Generate a clean directory tree without dumping file contents |
| [**Search**](#search) | Search file paths, file names, file contents, and individual lines |
| [**Read**](#read) | Safely retrieve a specific file |

**More**

| Feature | Description |
|---------|-------------|
| [**Read Many**](#read-many) | Retrieve multiple files in a single operation |
| [**Dependencies**](#dependencies) | See what a file depends on and what depends on it |
| [**Diff**](#diff) | Inspect Git status and unified diffs |
| [**Overview**](#overview) | Export the complete structure and supported file contents |

---

## Quick Start

Install LLMScribe from PyPI:

```bash
pip install llmscribe
```

Then point it at any project directory, or (through the MCP tools) at a public GitHub repo. No API key needed.

> The `project_map(...)`, `search(...)`, `read(...)` snippets below show **MCP tool calls**. The same operations are available from the CLI (local directories) and from Python through `llmscribe.core` (see [Python API](#python-api)).

### Map

Generate a clean directory tree without file contents. This is the best first step when exploring an unfamiliar repository.

```python
project_map()

# or a public GitHub repo, no clone needed
project_map(repo="owner/repo")
```

<details>
<summary><b>CLI / MCP</b></summary>

**CLI**
```bash
llmscribe map
llmscribe map --json
```

**MCP**
```text
project_map
```
</details>

Output:
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

Search across file paths, file names, file contents, and individual lines. Search is intentionally deterministic: LLMScribe does not try to guess what you meant.

```python
search(query="authentication")

# or a public GitHub repo
search(query="authentication", repo="owner/repo")
```

<details>
<summary><b>CLI / MCP</b></summary>

**CLI**
```bash
llmscribe search "authentication"
llmscribe search "authentication" --json
```

**MCP**
```text
search
```
</details>

Each match includes the file path, line number, the matching line, the matched text and the match type (`filename` or `content`). Results are ordered by path then line and limited to 1,000 matches; binary and oversized files are skipped.

Output (`--json`, `data.matches`):
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

Safely retrieve the contents of a specific file. LLMScribe validates paths and prevents path traversal outside the project.

```python
read(file_path="src/auth/service.py")

# or a public GitHub repo
read(file_path="src/main.py", repo="owner/repo")
```

<details>
<summary><b>CLI / MCP</b></summary>

**CLI**
```bash
llmscribe read src/auth/service.py
```

**MCP**
```text
read
```
</details>

> `path` and `repo` are mutually exclusive. Use `path` for a local project and `repo` for a public GitHub repository.

---

## Power Your Agent

Instead of throwing an entire repository into a context window, an agent can progressively retrieve exactly what it needs:

```text
1. project_map()
      ↓
2. search("authentication")
      ↓
3. read("src/auth/service.py")
      ↓
4. project_dependencies("src/auth/service.py")
      ↓
5. read_many([...])
```

### MCP

Connect any MCP-compatible client (Cursor, Claude, Windsurf, and more) to your repository.

**Free hosted MCP.** No installation required:

```json
{
  "mcpServers": {
    "llmscribe": {
      "url": "https://llmscribe.onrender.com/mcp"
    }
  }
}
```

For clients that support custom remote connectors, simply provide the endpoint: `https://llmscribe.onrender.com/mcp`

> The public endpoint is convenient for experimentation. For private code or production workloads, self-host LLMScribe instead.

**Local MCP.** Runs on your machine, over stdio:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

<details>
<summary><b>Alternative: Python module</b></summary>

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
</details>

**Available tools**

```text
project_map
project_overview
search
read
read_many
project_dependencies
project_diff
```

---

## More Tools

### Read Many

Retrieve multiple files in a single operation. Partial success is supported, so one problematic file does not invalidate the entire request.

```python
read_many([
    "src/auth/service.py",
    "src/auth/models.py",
    "src/api/login.py"
])
```

```bash
llmscribe read-many src/auth/service.py src/api/login.py
```

### Dependencies

Inspect the dependency relationships around a file. LLMScribe identifies local dependencies, external dependencies, unresolved dependencies, and the files that depend on this file.

```python
project_dependencies("src/auth/service.py")
```

```bash
llmscribe dependencies src/auth/service.py --json
```

Output:
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

This is particularly useful when determining the potential impact of modifying a file.

### Diff

Inspect repository changes using Git. Supports Git status, unstaged changes, staged changes, specific commits, and unified diffs.

```bash
llmscribe diff
```

This lets applications and agents understand not only the current repository, but also **what changed**.

### Overview

Generate a complete project snapshot containing the directory structure, supported text file contents, and structured project information.

```bash
llmscribe overview
```

Best for small and medium-sized projects. For large repositories, use the recommended workflow instead:

```text
map → search → read
```

---

## CLI

Every command can return machine-readable JSON with `--json`, which makes the CLI a building block for scripts, automation, and developer tools.

```bash
llmscribe map
llmscribe overview
llmscribe search "authentication"
llmscribe read src/auth/service.py
llmscribe read-many src/auth/service.py src/api/login.py
llmscribe dependencies src/auth/service.py
llmscribe diff

# machine-readable output
llmscribe map --json
llmscribe search "auth" --json
llmscribe dependencies src/auth/service.py --json
```

---

## Self-Hosting

Run your own HTTP MCP server for private repositories, teams, internal developer tools, and production applications.

### Run locally

```bash
pip install llmscribe

MCP_TRANSPORT=http MCP_ALLOW_LOCAL_PATHS=1 llmscribe-mcp
```

The server will be available at `http://localhost:8000/mcp`, with `GET /health` and `GET /info` for monitoring.

> Over HTTP the `path` argument is **disabled by default** so a hosted server does not expose its own disk. Set `MCP_ALLOW_LOCAL_PATHS=1` to allow any local path (only on a machine you trust), or `MCP_ALLOWED_ROOTS=/srv/a:/srv/b` to allow specific directories. GitHub repositories (`repo=`) always work.

### Docker

```bash
docker build -t llmscribe-mcp .

docker run -p 8000:8000 -e MCP_ALLOWED_HOSTS="localhost,localhost:*,mcp.example.com" llmscribe-mcp
```

The image runs `python -m llmscribe.mcp` with `MCP_TRANSPORT=http`, as an unprivileged user, and has a `/health` with a `healthcheck`.

### Railway

```bash
railway up
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `http` | `stdio` |
| `HOST` | HTTP bind address | `0.0.0.0` |
| `PORT` | HTTP port | `8000` |
| `MCP_ALLOWED_HOSTS` | Accepted `Host` values for `/mcp` (comma-separated, `host:*` for any port, `*` for any). Default: loopback plus `RENDER_EXTERNAL_HOSTNAME` / `RAILWAY_PUBLIC_DOMAIN` | loopback |
| `MCP_ALLOWED_ORIGINS` | Accepted `Origin` values for `/mcp` (requests without an `Origin`, i.e. all non-browser clients, are always accepted). Default: loopback, `claude.ai`, the platform hostname; `*` allows any | see left |
| `MCP_ALLOW_LOCAL_PATHS` | `1` allows any local `path` over HTTP | off |
| `MCP_ALLOWED_ROOTS` | Directories (separated by `:` / `;`) allowed as `path` over HTTP | none |
| `GITHUB_TOKEN` / `GH_TOKEN` | Token for private repositories and higher rate limits (sent only to `api.github.com`) | none |
| `LLMSCRIBE_CACHE_MAX_ENTRIES` | GitHub snapshots kept in memory (`0` disables) | `8` |
| `LLMSCRIBE_CACHE_TTL_SECONDS` | Snapshot lifetime | `300` |

Run a single process (the cache and MCP sessions live in memory). `PORT` without `MCP_TRANSPORT` still selects HTTP for backward compatibility, but set `MCP_TRANSPORT=http` explicitly.
---

## Python API

```python
from pathlib import Path
from llmscribe.core import project_map, search_project, read_file, read_files, analyze_dependencies, get_git_diff, LLMScribeError

root = Path(".")
print(project_map(root).tree)
print(search_project("auth", root).to_dict())
print(read_files(["README.md", "missing.py"], root).to_dict())   # per-file errors, never raises
try:
    analyze_dependencies("src/app.py", root)
except LLMScribeError as err:      # err.code is a stable machine-readable code
    print(err.code, err.message)
```

## Behavior reference

**Ignore rules.** Defaults (`.git`, `node_modules`, `venv`, `dist`, `build`, `.env`, `*.log`, …), the root `.gitignore` and nested `.gitignore` files are applied with real Git semantics (wildcards, directories, `!` negation, root-anchored patterns). Hidden files are included unless ignored; symlinks are never followed or listed.

**Supported text files.** Known source/config/doc extensions plus names such as `Dockerfile`, `Makefile`, `LICENSE`, `.gitignore`. Other files appear in the tree but cannot be read or searched.

**Limits** (single source: `llmscribe.core.limits`): 400,000 content characters per overview/read_many, 50 files per `read_many`, 1,000 search matches, 20,000 map entries, 2 MiB per file, 200,000 diff characters, 100 MiB archive download, 250 MiB / 100,000 entries per archive. Anything cut is reported (`truncated`, `truncation_note`, `omitted_files`).

**Errors.** Every failure has a stable code: `invalid_argument`, `invalid_path`, `file_not_found`, `unsupported_file_type`, `binary_file`, `file_too_large`, `read_error`, `repository_not_found`, `not_a_repository`, `repository_too_large`, `github_rate_limited`, `github_auth_required`, `github_unavailable`, `git_unavailable`, `unsupported_operation`, `internal_error`. JSON: `{"ok": false, "tool": "...", "error": {"code": "...", "message": "..."}}`.

**Dependencies.** Python, JavaScript/TypeScript, Java, Go, Rust, C/C++. Each reference is `local`, `stdlib`, `external` (not in the repository, assumed third-party) or `unresolved` (relative/local reference that matches nothing); `used_by` lists reverse dependencies. Works identically for local and GitHub sources.

**GitHub.** Public repositories (and private ones with `GITHUB_TOKEN`) are fetched as one zip archive and cached in memory per owner/repo/ref/credential. Nothing is cloned or written to disk. `project_diff` on GitHub uses the compare API and requires `commit` (base) with optional `ref` (head); `staged` is local only.

**Git diff (local).** Runs `git` with an argument list, a 30 s timeout, a minimal environment, and without external diff/textconv drivers.

### Migration notes

- Legacy tool names (`project_get_file`, `project_get_files`, `project_search`, `project_list_files`) are gone; use `read`, `read_many`, `search`.
- Error code `path_traversal` is now `invalid_path`; `not_text_file` is `unsupported_file_type`.
- `project_dependencies` results: `all_local_files`/`all_external_deps`/`all_unresolved` were replaced by `used_by` and per-category lists (`stdlib_dependencies` added).
- `llmscribe.core` functions raise `LLMScribeError` (not `FileNotFoundError`) for a bad root; the dependency-provider classes and `llmscribe.github.provider` helpers were removed.
- Over HTTP, local `path` access now requires `MCP_ALLOW_LOCAL_PATHS` or `MCP_ALLOWED_ROOTS`.

---

## Architecture

All interfaces share one core engine, so behavior stays consistent everywhere.

```text
                         Repository
                             │
               ┌─────────────┴─────────────┐
               │                           │
          Local Project               GitHub Repo
               │                           │
               └─────────────┬─────────────┘
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

---

## Philosophy

LLMScribe intentionally stays simple. The goal is not to make the repository "smarter." The goal is to make the repository **accessible to software**.

**We provide**

- Repository extraction
- Deterministic search
- Structured project data
- File retrieval
- Dependency information
- Git information
- Multiple interfaces

**We don't provide**

- ❌ AI-generated answers
- ❌ Embedding-based search
- ❌ Semantic ranking
- ❌ Autonomous coding
- ❌ An AI coding agent
- ❌ A generic Git client

---

## Use Cases

- AI coding agents
- MCP applications
- Developer tools
- Code search interfaces
- Repository explorers
- Documentation systems
- Code analysis pipelines
- Automation scripts
- Local LLM applications
- Exploring unfamiliar open-source projects

---

## Open Source vs Hosted

LLMScribe is open source under the **Apache License 2.0**. Run it locally, inspect the source, modify it, self-host it, and build your own integrations.

The hosted MCP endpoint provides a convenient zero-install option for trying it out, while the open-source project gives you complete control.

---

## Resources

- **Website:** https://llmscribe.vercel.app
- **GitHub:** https://github.com/AMRITO-KUNDU/llmscribe
- **PyPI:** https://pypi.org/project/llmscribe/
- **Official MCP Registry:** https://registry.modelcontextprotocol.io/?q=llmscribe (`io.github.AMRITO-KUNDU/llmscribe`)
- **Public MCP:** https://llmscribe.onrender.com/mcp
- **Issues:** https://github.com/AMRITO-KUNDU/llmscribe/issues
- **Contributing:** https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md

---

## Contributing

Contributions are welcome. If you want to improve repository extraction, search, dependency analysis, interfaces, integrations, or documentation, check the [contributing guide](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md) before opening a pull request.

<a href="https://github.com/AMRITO-KUNDU/llmscribe/graphs/contributors">
  <img alt="Contributors" src="https://contrib.rocks/image?repo=AMRITO-KUNDU/llmscribe"/>
</a>

---

## License

LLMScribe is licensed under the **Apache License 2.0**. See the [LICENSE](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/LICENSE) file for details.

<div align="center">

*Repository data, structured.*

<a href="#readme-top">↑ Back to top</a>

</div>

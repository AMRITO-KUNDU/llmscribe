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

**Turn any code repository into clean, structured, deterministic data.** No AI. No embeddings. No hidden ranking. Apache-2.0, and it runs entirely on your machine — no network, no account.


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

Then point it at any project directory on your machine. No API key, no network access, no account.

> The `project_map(...)`, `search(...)`, `read(...)` snippets below show **MCP tool calls**. The same operations are available from the CLI (local directories) and from Python through `llmscribe.core` (see [Python API](#python-api)).

### Map

Generate a clean directory tree without file contents. This is the best first step when exploring an unfamiliar repository.

```python
project_map()
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

LLMScribe is a standard Model Context Protocol server that runs locally over stdio, so any MCP-compatible client can use it against a project directory on your machine.

**Config** — put this in your client (see the per-app setup below):

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
<summary><b>Use the Python module instead of the command</b></summary>

If `llmscribe-mcp` is not on your `PATH`, point the client at the module:

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

#### Per-app setup

Each client reads a different configuration file. The blocks below were checked against each tool's official documentation.

<details>
<summary><b>Claude Desktop</b></summary>

Edit `claude_desktop_config.json` (in the app: **Settings → Developer → Edit Config**):

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

Fully quit and reopen Claude Desktop after saving.

</details>

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add llmscribe -- llmscribe-mcp
```

Confirm with `claude mcp list`. Add `--scope user` to make it available in every project, or `--scope project` to share it with your team via `.mcp.json`.

</details>

<details>
<summary><b>Cursor</b></summary>

Create `.cursor/mcp.json` in your project (or `~/.cursor/mcp.json` for all projects):

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

Restart Cursor, then check **Customize → MCPs**.

</details>

<details>
<summary><b>VS Code (GitHub Copilot)</b></summary>

Create `.vscode/mcp.json` in your workspace. Note that VS Code uses `servers`, not `mcpServers`:

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

Then open Copilot Chat in **Agent** mode and click the tools icon to start the server.

</details>

<details>
<summary><b>Windsurf (Cascade)</b></summary>

Edit `~/.codeium/mcp_config.json` (in the app: **Windsurf Settings → Cascade → MCP → View Raw Config**):

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

Press the refresh button after saving.

</details>

<details>
<summary><b>Cline</b></summary>

Open the Cline panel → **MCP Servers** → **Configure** → **Configure MCP Servers**, then add:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```


</details>

<details>
<summary><b>Roo Code</b></summary>

Edit the global `mcp_settings.json` (**Edit Global MCP**), or create `.roo/mcp.json` in your project (**Edit Project MCP**):

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```


</details>

<details>
<summary><b>LM Studio</b></summary>

In the app: **Program** tab → **Install → Edit mcp.json** (the file is `~/.lmstudio/mcp.json` on macOS/Linux, `%USERPROFILE%\.lmstudio\mcp.json` on Windows):

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

LM Studio follows Cursor's `mcp.json` notation.

</details>

<details>
<summary><b>Zed</b></summary>

Add to your Zed settings (in the app: **Settings → AI → MCP Servers → Add Server**, or `zed: open settings file`):

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


</details>

<details>
<summary><b>Continue</b></summary>

Add to `~/.continue/config.yaml` (or a standalone file under `.continue/mcpServers/`):

```yaml
name: LLMScribe
version: 1.0.0
schema: v1
mcpServers:
  - name: LLMScribe
    command: llmscribe-mcp
```

Continue also picks up Cursor/Claude/Cline JSON configs dropped into `.continue/mcpServers/`.

</details>

<details>
<summary><b>JetBrains IDEs (IntelliJ, WebStorm, …)</b></summary>

**Settings → Tools → AI Assistant → Model Context Protocol (MCP) → Add → As JSON**:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

You can also click **Import from Claude** to reuse an existing Claude Desktop configuration.

</details>

<details>
<summary><b>Goose</b></summary>

Add an extension to `~/.config/goose/config.yaml`:

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


</details>

<details>
<summary><b>OpenAI Codex CLI</b></summary>

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.llmscribe]
command = "llmscribe-mcp"
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

## Configuration

LLMScribe runs entirely on your machine and needs no configuration. Two optional environment variables restrict which directories the MCP server may read:

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ALLOWED_ROOTS` | Directories (separated by `:` on POSIX, `;` on Windows) the tools may read | all paths |
| `MCP_ALLOW_LOCAL_PATHS` | `0` disables local path access entirely | enabled |

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

**Limits** (single source: `llmscribe.core.limits`): 400,000 content characters per overview/read_many, 50 files per `read_many`, 1,000 search matches, 20,000 map entries, 2 MiB per file, 200,000 diff characters, 100,000 scanned entries. Anything cut is reported (`truncated`, `truncation_note`, `omitted_files`).

**Errors.** Every failure has a stable code: `invalid_argument`, `invalid_path`, `file_not_found`, `unsupported_file_type`, `binary_file`, `file_too_large`, `read_error`, `not_a_repository`, `git_unavailable`, `unsupported_operation`, `internal_error`. JSON: `{"ok": false, "tool": "...", "error": {"code": "...", "message": "..."}}`.

**Dependencies.** Python, JavaScript/TypeScript, Java, Go, Rust, C/C++. Each reference is `local`, `stdlib`, `external` (not in the repository, assumed third-party) or `unresolved` (relative/local reference that matches nothing); `used_by` lists reverse dependencies.

**Git diff (local).** Runs `git` with an argument list, a 30 s timeout, a minimal environment, and without external diff/textconv drivers.

### Migration notes

- Legacy tool names (`project_get_file`, `project_get_files`, `project_search`, `project_list_files`) are gone; use `read`, `read_many`, `search`.
- Error code `path_traversal` is now `invalid_path`; `not_text_file` is `unsupported_file_type`.
- `project_dependencies` results: `all_local_files`/`all_external_deps`/`all_unresolved` were replaced by `used_by` and per-category lists (`stdlib_dependencies` added).
- `llmscribe.core` functions raise `LLMScribeError` (not `FileNotFoundError`) for a bad root.
- **1.3.0:** the online GitHub source was removed — LLMScribe is now local-only. The `repo` and `ref` arguments, the in-memory snapshot cache, the `llmscribe.github` package, and the hosted HTTP transport are gone. Point the tools at a local `path`.

---

## Architecture

All interfaces share one core engine, so behavior stays consistent everywhere.

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

## Open Source

LLMScribe is open source under the **Apache License 2.0**. Inspect the source, modify it, and build your own integrations. There is no hosted service and no telemetry — it reads your files, and nothing leaves your machine.

---

## Resources

- **Website:** https://llmscribe.vercel.app
- **GitHub:** https://github.com/AMRITO-KUNDU/llmscribe
- **PyPI:** https://pypi.org/project/llmscribe/
- **Official MCP Registry:** https://registry.modelcontextprotocol.io/?q=llmscribe (`io.github.AMRITO-KUNDU/llmscribe`)
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

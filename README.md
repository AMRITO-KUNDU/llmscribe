<h3 align="center">
  <a name="readme-top"></a>
  <img
    src="https://raw.githubusercontent.com/AMRITO-KUNDU/llmscribe/main/docs/public/favicon.svg"
    height="120"
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
    <img src="https://img.shields.io/github/contributors/AMRITO-KUNDU/llmscribe.svg" alt="Contributors">
  </a>
  <a href="https://llmscribe.vercel.app">
    <img src="https://img.shields.io/badge/Visit-llmscribe.vercel.app-orange" alt="Website">
  </a>

</div>

<div align="center">
  <p>
    <a href="https://x.com/amritokundu719">
      <img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X">
    </a>
    <a href="https://github.com/AMRITO-KUNDU">
      <img src="https://img.shields.io/badge/Follow%20on%20GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="Follow on GitHub">
    </a>
  </p>
</div>

---

# LLMScribe

**Turn any code repository into clean, structured, deterministic data.**

LLMScribe is an open-source repository extractor and code-context tool for **local projects and public GitHub repositories**.

Search, map, read, inspect dependencies, view changes, and export project data through a simple CLI, GUI, or MCP server.

No AI. No embeddings. No hidden ranking.

Just your repository, structured for humans and machines.

<a href="https://github.com/AMRITO-KUNDU/llmscribe">
  <img src="https://img.shields.io/github/stars/AMRITO-KUNDU/llmscribe.svg?style=social&label=Star&maxAge=2592000" alt="GitHub stars">
</a>

---

## Why LLMScribe?

Code repositories contain a huge amount of information, but the default ways of exploring them are designed mainly for humans.

LLMScribe turns that repository into a **clean, queryable data layer**.

- **Deterministic** — Same input, predictable output. No LLM, embeddings, or AI ranking.
- **Repository-first** — Works with local projects and public GitHub repositories.
- **Structured output** — Machine-readable JSON for every operation.
- **Fast discovery** — Map a project, search it, then retrieve exactly what you need.
- **Dependency-aware** — Understand local, external, and unresolved dependencies.
- **Git-aware** — Inspect status and unified diffs.
- **Multiple interfaces** — CLI, MCP, GUI, and programmatic core.
- **Agent-ready** — Give coding agents structured repository data instead of raw terminal output.
- **Open source** — Apache-2.0, self-hostable, and free forever.

> **LLMScribe doesn't try to be the intelligence. It provides the data that intelligence needs.**

---

## What Can LLMScribe Do?

| Capability | What it does |
|---|---|
| **Project Map** | Generate a clean directory tree without dumping file contents |
| **Search** | Search file paths and file contents |
| **Read** | Retrieve a specific file safely |
| **Read Many** | Retrieve multiple relevant files in one operation |
| **Dependencies** | Inspect what a file depends on and what depends on it |
| **Project Diff** | Inspect Git status and unified changes |
| **Project Overview** | Export the complete structure and supported file contents |
| **GitHub Repositories** | Run the same operations against public GitHub repositories |
| **JSON Output** | Get machine-readable results from every CLI operation |

---

## How It Works

LLMScribe follows a simple repository exploration workflow:

```text
Repository
    │
    ▼
Project Map
    │
    ▼
Search
    │
    ├──► Read
    │
    ├──► Read Many
    │
    └──► Dependencies
```

Instead of throwing an entire repository into a context window, an application or agent can progressively retrieve exactly the information it needs.

### Example

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

This makes LLMScribe useful for both **human developers and AI-powered development tools**.

---

# Interfaces

LLMScribe has multiple ways to access the same underlying repository engine.

```text
                    LLMScribe Core
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         CLI            MCP            GUI
          │              │
          └─────── JSON / Structured ───┘
```

All interfaces use the same core functionality, so the behavior stays consistent across environments.

---

## MCP

LLMScribe includes an MCP server for AI coding tools and other MCP-compatible applications.

The MCP interface exposes focused repository primitives instead of trying to become an AI agent itself.

### Available tools

```text
project_map
project_overview
search
read
read_many
project_dependencies
project_diff
```

This works well with tools such as Cursor, Claude, Windsurf, and other MCP clients.

### Free Public MCP

You can use the hosted MCP endpoint without installing LLMScribe:

```text
https://llmscribe.onrender.com/mcp
```

For example:

```json
{
  "mcpServers": {
    "llmscribe": {
      "url": "https://llmscribe.onrender.com/mcp"
    }
  }
}
```

For clients that support custom remote connectors, simply provide the MCP endpoint.

> The public endpoint is convenient for experimentation. For private code or production workloads, self-host LLMScribe instead.

---

# GitHub Repository Support

LLMScribe can work directly with public GitHub repositories.

The same repository operations can be used without cloning the repository locally.

```python
project_map(repo="owner/repo")

search(
    query="authentication",
    repo="owner/repo"
)

read(
    file_path="src/main.py",
    repo="owner/repo"
)
```

This makes LLMScribe useful for:

- Exploring unfamiliar open-source projects
- Giving agents structured access to GitHub repositories
- Building repository analysis tools
- Extracting project data
- Creating developer tooling on top of repository data

`path` and `repo` are mutually exclusive.

---

# Tools

## `project_map`

Generate a clean directory tree without file contents.

Useful as the first step when exploring an unfamiliar repository.

```text
src/
├── api/
│   ├── routes.py
│   └── auth.py
├── models/
│   └── user.py
└── main.py
```

---

## `search`

Search across:

- File paths
- File names
- File contents
- Individual lines

Example:

```text
search("authentication")
```

Returns structured results containing information such as:

- File path
- Line number
- Matching text
- Match type

Search is intentionally deterministic.

LLMScribe does not try to guess what you meant.

---

## `read`

Safely retrieve the contents of a specific file.

```text
read("src/auth/service.py")
```

LLMScribe validates paths and prevents path traversal outside the project.

---

## `read_many`

Retrieve multiple files in a single operation.

```text
read_many([
    "src/auth/service.py",
    "src/auth/models.py",
    "src/api/login.py"
])
```

Useful when several files are already known to be relevant.

Partial success is supported, so one problematic file does not necessarily invalidate the entire request.

---

## `project_dependencies`

Inspect the dependency relationships around a file.

It can identify:

```text
Local dependencies
External dependencies
Unresolved dependencies
Files that depend on this file
```

Example:

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

---

## `project_diff`

Inspect repository changes using Git.

Supports:

- Git status
- Unstaged changes
- Staged changes
- Specific commits
- Unified diffs

Example:

```bash
llmscribe diff
```

This allows applications and agents to understand not only the current repository, but also **what changed**.

---

## `project_overview`

Generate a complete project snapshot containing:

- Directory structure
- Supported text file contents
- Structured project information

This is useful for small and medium-sized projects where retrieving the entire repository at once is practical.

For large repositories, the recommended workflow is:

```text
map → search → read
```

rather than loading everything.

---

# CLI

Install LLMScribe from PyPI:

```bash
pip install llmscribe
```

Then use the CLI:

```bash
llmscribe map

llmscribe overview

llmscribe search "authentication"

llmscribe read src/auth/service.py

llmscribe read-many src/auth/service.py src/api/login.py

llmscribe dependencies src/auth/service.py

llmscribe diff
```

Every command can return machine-readable JSON:

```bash
llmscribe map --json

llmscribe search "auth" --json

llmscribe dependencies src/auth/service.py --json
```

This makes the CLI useful not only interactively, but also as a building block for scripts, automation, and developer tools.

---

# Local Projects

LLMScribe can inspect a project directly from your machine.

```bash
llmscribe map
```

Or use the MCP server locally:

```bash
llmscribe-mcp
```

For Cursor or Claude Desktop:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

Alternative Python module:

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

---

# Self-Hosted MCP

LLMScribe can also be deployed as your own HTTP MCP server.

This is useful for:

- Private repositories
- Teams
- Internal developer tools
- Production applications
- Custom integrations

### Run locally

```bash
pip install llmscribe

MCP_TRANSPORT=http python -m llmscribe.mcp.server
```

The server will be available at:

```text
http://localhost:8000/mcp
```

### Docker

```bash
docker build -t llmscribe-mcp .

docker run -p 8000:8000 llmscribe-mcp
```

### Railway

```bash
railway up
```

or:

```bash
railway deploy
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MCP_TRANSPORT` | `stdio` or `http` | `stdio` |
| `HOST` | HTTP bind address | `0.0.0.0` |
| `PORT` | HTTP port | `8000` |

---

# Designed for Machines, Useful for Humans

LLMScribe is designed around a simple idea:

> **Repository data should be easy to retrieve, not difficult to extract.**

Traditional terminal commands are excellent for humans, but applications and AI agents often need:

```text
structured data
predictable schemas
specific files
specific lines
dependency relationships
repository changes
```

LLMScribe provides those primitives without inserting an AI layer between the repository and the consumer.

That makes it useful as a foundation for:

- AI coding agents
- MCP applications
- Developer tools
- Code search interfaces
- Repository explorers
- Documentation systems
- Code analysis pipelines
- Automation scripts
- Local LLM applications
- Custom developer workflows

---

# Project Philosophy

LLMScribe intentionally stays simple.

### We provide

- Repository extraction
- Deterministic search
- Structured project data
- File retrieval
- Dependency information
- Git information
- Multiple interfaces

### We don't provide

- ❌ AI-generated answers
- ❌ Embedding-based search
- ❌ Semantic ranking
- ❌ Autonomous coding
- ❌ An AI coding agent
- ❌ A generic Git client

The goal is not to make the repository "smarter."

The goal is to make the repository **accessible to software**.

---

# Architecture

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

The core extraction and analysis logic is shared across interfaces.

---

# Open Source

LLMScribe is open source under the **Apache License 2.0**.

You can:

- Run it locally
- Inspect the source
- Modify it
- Self-host it
- Build integrations
- Use it in your own developer tools

The hosted MCP endpoint provides a convenient zero-install option, while the open-source project gives you complete control.

---

# Roadmap

The focus is on making the existing repository primitives better rather than adding unnecessary features.

### Core

- [ ] Faster repository search
- [ ] Better language-aware search
- [ ] Improved large-repository handling
- [ ] More accurate dependency analysis
- [ ] Better repository metadata
- [ ] More robust file detection and filtering

### Integrations

- [ ] More MCP client compatibility
- [ ] Better local LLM integrations
- [ ] More developer-tool integrations
- [ ] Improved GitHub repository workflows

### Developer Experience

- [ ] Better documentation
- [ ] More examples
- [ ] More language support
- [ ] Expanded test coverage
- [ ] Performance benchmarks

---

# Resources

- **Website:** https://llmscribe.vercel.app
- **GitHub:** https://github.com/AMRITO-KUNDU/llmscribe
- **PyPI:** https://pypi.org/project/llmscribe/
- **Public MCP:** https://llmscribe.onrender.com/mcp
- **Issues:** https://github.com/AMRITO-KUNDU/llmscribe/issues
- **Contributing:** https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md

---

# Contributing

Contributions are welcome.

If you want to improve repository extraction, search, dependency analysis, interfaces, integrations, or documentation, check the contributing guide before opening a pull request.

<a href="https://github.com/AMRITO-KUNDU/llmscribe/graphs/contributors">
  <img alt="Contributors" src="https://contrib.rocks/image?repo=AMRITO-KUNDU/llmscribe"/>
</a>

---

# License

LLMScribe is licensed under the **Apache License 2.0**.

---

<div align="center">

**LLMScribe**

*Repository data, structured.*

<a href="#readme-top">↑ Back to top</a>

</div>

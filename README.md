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

_Pst. Hey, you, join our stargazers :)_

<a href="https://github.com/AMRITO-KUNDU/llmscribe">
  <img src="https://img.shields.io/github/stars/AMRITO-KUNDU/llmscribe.svg?style=social&label=Star&maxAge=2592000" alt="GitHub stars">
</a>

---

## Why LLMScribe?

- **Deterministic**: Same input, predictable output. No LLM, embeddings, or AI ranking
- **Repository-first**: Works with local projects and public GitHub repositories, no cloning required
- **Structured output**: Machine-readable JSON for every operation
- **Fast discovery**: Map a project, search it, then retrieve exactly what you need
- **Dependency-aware**: Understand local, external, and unresolved dependencies
- **Git-aware**: Inspect status and unified diffs
- **Agent ready**: Connect LLMScribe to any AI agent or MCP client with a single config block
- **Multiple interfaces**: CLI, MCP, GUI, and a programmatic core, all sharing the same engine
- **Open source**: Apache-2.0, self-hostable, and free forever

> **LLMScribe doesn't try to be the intelligence. It provides the data that intelligence needs.**

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

Then point it at any project directory, or at a public GitHub repo. No API key needed.

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

Each result includes the file path, line number, matching text, and match type.

Output:
```json
[
  {
    "file_path": "src/auth/service.py",
    "line": 12,
    "text": "def authenticate(user, password):",
    "match_type": "content"
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

MCP_TRANSPORT=http python -m llmscribe.mcp.server
```

The server will be available at `http://localhost:8000/mcp`.

### Docker

```bash
docker build -t llmscribe-mcp .

docker run -p 8000:8000 llmscribe-mcp
```

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

<h3 align="center">
  <a name="readme-top"></a>
  <!-- Replace with your actual logo when ready -->
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
    <img src="https://img.shields.io/github/contributors/AMRITO-KUNDU/llmscribe.svg" alt="GitHub Contributors">
  </a>
  <a href="https://llmscribe.vercel.app">
    <img src="https://img.shields.io/badge/Visit-llmscribe.vercel.app-orange" alt="Visit Website">
  </a>

</div>

<div>
  <p align="center">
    <a href="https://twitter.com/amritokundu719">
      <img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X" />
    </a>
    <a href="https://github.com/AMRITO-KUNDU">
      <img src="https://img.shields.io/badge/Follow%20on%20GitHub-181717?style=for-the-badge&logo=github&logoColor=white" alt="Follow on GitHub" />
    </a>
  </p>
</div>

---

# **LLMScribe**

**Give AI agents clean, deterministic, structured context from any local project or GitHub repository.**  
Open source and available as a [free public MCP endpoint](https://llmscribe-production.up.railway.app/mcp).

_Pst. Hey, you, join our stargazers :)_

<a href="https://github.com/AMRITO-KUNDU/llmscribe">
  <img src="https://img.shields.io/github/stars/AMRITO-KUNDU/llmscribe.svg?style=social&label=Star&maxAge=2592000" alt="GitHub stars">
</a>

---

## Why LLMScribe?

- **Deterministic by design**: No embeddings, no ranking, no hallucinations — pure structured code context
- **Agent-first**: Built specifically for Cursor, Claude Desktop, Windsurf, and any MCP client
- **Local + Remote**: Work with any local folder *or* any public GitHub repository (`repo="owner/repo"`)
- **Zero config public MCP**: Paste one URL and start using tools immediately
- **Seven focused tools**: Exactly the primitives agents need — map, search, read, dependencies, diff
- **Shared core**: Same logic powers the MCP server, CLI, and GUI — consistent results everywhere
- **Open source**: Apache-2.0 — transparent, self-hostable, and free forever

---

## Feature Overview

**Core Tools**

| Feature                        | Description                                                              |
| ------------------------------ | ------------------------------------------------------------------------ |
| [**project_map**](#project_map) | Directory tree without file contents — perfect first step for agents    |
| [**search**](#search)          | Keyword search across paths *and* file contents                          |
| [**read / read_many**](#read)  | Safe single or batch file reading with path-traversal protection         |
| [**project_dependencies**](#project_dependencies) | Local / external / unresolved dependency graph for any file |
| [**project_diff**](#project_diff) | Git status + unified diffs (staged, unstaged, or specific commits)     |
| [**project_overview**](#project_overview) | Full tree + contents of all supported files (small/medium repos) |

**More**

| Feature                     | Description                                           |
| --------------------------- | ----------------------------------------------------- |
| Free Public MCP             | Use instantly without installing anything             |
| Self-hosted HTTP / Docker   | FastAPI + FastMCP production server                   |
| Modern CLI                  | Same capabilities as the MCP tools                    |
| JSON mode                   | Machine-readable output for every command             |
| GitHub repo support         | `repo="owner/repo"` works on every tool               |

---

## Quick Start

### Free Public MCP (Recommended)

No installation required. Works with Claude, Cursor, Claude Desktop, and any MCP client.

#### Claude / Claude Desktop / claude.ai
1. Go to **Connectors → Add custom connector**
2. Paste: `https://llmscribe-production.up.railway.app/mcp`

#### Cursor
```json
{
  "mcpServers": {
    "llmscribe": {
      "url": "https://llmscribe-production.up.railway.app/mcp"
    }
  }
}
```

Then just call tools with `repo="owner/repo"` or a local path.

### Local Installation

```bash
pip install llmscribe
```

### Running the MCP Server (stdio)

```bash
llmscribe-mcp
```

#### Cursor / Claude Desktop config
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

---

## Power Your Agent

### Recommended Agent Workflow

```
project_map → search → read / read_many
```

**Example: Understand a new repository**
1. `project_map()` → get the overall structure
2. `search("main")` or `search("FastAPI")` → find entry points
3. `read("src/main.py")` or `read_many([...])` → pull the relevant files

**Example: Analyze dependencies**
1. `search("import")` or `search("from fastapi")`
2. `project_dependencies("src/api/main.py")`
3. `read_many()` on the returned dependency files

### GitHub Repository Support

Every tool accepts a remote GitHub repository:

```python
project_map(repo="owner/repo")
search(query="authentication", repo="owner/repo")
read(file_path="src/main.py", repo="owner/repo")
```

> `path` and `repo` are mutually exclusive.

---

## Tools Reference

### project_map
Generate a clean directory tree (no file contents).

**When to use**: First step when exploring an unknown codebase.

### project_overview
Full directory structure + contents of all supported text files.

**When to use**: Small-to-medium projects where you want everything in one call.

### search
Keyword search across file paths and line-by-line contents.  
This is the main discovery primitive for agents.

### read
Safely retrieve the full content of a single relative file path.  
Includes strict path-traversal protection.

### read_many
Batch-read multiple files in one call (partial success supported).

### project_dependencies
Analyze what a file depends on and what depends on it  
(local vs external vs unresolved).

### project_diff
Inspect Git status and unified diffs (staged / unstaged / specific commit).

---

## CLI Usage

LLMScribe CLI exposes the exact same capabilities as the MCP server.

```bash
llmscribe map
llmscribe overview
llmscribe search "authentication"
llmscribe read src/auth/service.py
llmscribe read-many src/auth/service.py src/api/login.py
llmscribe dependencies src/auth/service.py
llmscribe diff
```

JSON output is available on every command:

```bash
llmscribe search "auth" --json
llmscribe map --json
```

---

## Self-Hosted MCP Server

Deploy your own private or team MCP server.

### Quick Start

```bash
# Install dependencies
pip install llmscribe

# Start HTTP server
MCP_TRANSPORT=http python -m llmscribe.mcp.server
# → http://0.0.0.0:8000/mcp
```

### Docker

```bash
docker build -t llmscribe-mcp .
docker run -p 8000:8000 llmscribe-mcp
```

### Railway

```bash
railway up
# or
railway deploy
```

#### Environment Variables

| Variable        | Description                  | Default  |
|-----------------|------------------------------|----------|
| `MCP_TRANSPORT` | `stdio` or `http`            | `stdio`  |
| `HOST`          | HTTP bind address            | `0.0.0.0`|
| `PORT`          | HTTP port                    | `8000`   |

#### MCP Client Configuration

**Cursor:**
```json
{
  "mcpServers": {
    "llmscribe": {
      "url": "https://llmscribe-production.up.railway.app"
    }
  }
}
```

**Claude Desktop / Claude.ai:**
1. Go to **Connectors → Add custom connector**
2. Paste URL: `https://llmscribe-production.up.railway.app`

**General MCP Clients:**
```json
{
  "mcpServers": {
    "llmscribe": {
      "url": "http://your-server-url"
    }
  }
}
```

**Note:** The MCP server serves the protocol at the root URL (`/`) when using `streamable-http` transport.

---

## Architecture

```
                    LLMScribe Core
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         MCP            CLI            GUI
```

All interfaces share the same core functions — consistent behavior and output everywhere.

---

## Project Positioning

**LLMScribe provides clean, deterministic, structured code context.  
The AI agent provides the intelligence.**

- ✅ Deterministic (no LLM, no embeddings, no ranking)
- ✅ Structured JSON schemas
- ✅ Designed for agent workflows
- ❌ Not an AI coding agent
- ❌ Not a semantic search engine
- ❌ Not a generic Git client

---

## Resources

- [Website](https://llmscribe.vercel.app)
- [Free Public MCP](https://llmscribe-production.up.railway.app/mcp)
- [PyPI](https://pypi.org/project/llmscribe/)
- [GitHub Issues](https://github.com/AMRITO-KUNDU/llmscribe/issues)
- [Contributing Guide](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md)

---

## Open Source vs Hosted

LLMScribe is fully open source under the **Apache-2.0** license.

| Feature                    | Open Source          | Free Public MCP          |
|---------------------------|----------------------|--------------------------|
| Local projects            | ✅                   | ✅ (via tools)           |
| GitHub repositories       | ✅                   | ✅                       |
| Self-host / Docker        | ✅                   | —                        |
| Zero-install public endpoint | —                 | ✅                       |
| Private team deployment   | ✅                   | —                        |

---

## Contributing

We love contributions! Please read the [Contributing Guide](https://github.com/AMRITO-KUNDU/llmscribe/blob/main/CONTRIBUTING.md) before submitting a pull request.

### Contributors

<a href="https://github.com/AMRITO-KUNDU/llmscribe/graphs/contributors">
  <img alt="contributors" src="https://contrib.rocks/image?repo=AMRITO-KUNDU/llmscribe"/>
</a>

---

## License

This project is licensed under the **Apache License 2.0**.

---

**LLMScribe gives AI agents the structured context they need — nothing more, nothing less.**

<p align="right" style="font-size: 14px; color: #555; margin-top: 20px;">
  <a href="#readme-top" style="text-decoration: none; color: #007bff; font-weight: bold;">
    ↑ Back to Top ↑
  </a>
</p>
```
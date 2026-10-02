# LLMScribe

Turn any local project into clean, structured context for AI agents.

---

## For AI Agents (primary)

LLMScribe provides a deterministic code-context infrastructure layer for AI agents. It is NOT an AI-powered coding/search agent.

### Installation

```bash
pip install llmscribe
```

### Running the MCP Server

```bash
llmscribe-mcp
```

### MCP Client Configurations

#### Cursor / Claude Desktop / Standard MCP Clients:

```json
{
  "mcpServers": {
    "llmscribe": {
      "command": "llmscribe-mcp"
    }
  }
}
```

#### Alternative Module Invocation:

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

## Tools Reference

LLMScribe MCP provides exactly 7 tools:

### 1. `project_map`
* **Purpose**: Generates directory tree structure without file contents.
* **Parameters**: `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Exploring repository structure before selecting specific files.

### 2. `project_overview`
* **Purpose**: Generates full directory structure and full contents of all supported text files.
* **Parameters**: `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Getting a complete overview of small-to-medium codebases in one call.

### 3. `search`
* **Purpose**: Keyword search across file paths and line-by-line file contents. Main discovery primitive for AI agents.
* **Parameters**: `query` (*str*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Locating specific symbols, function definitions, or import statements.

### 4. `read`
* **Purpose**: Retrieves full content of a single specific relative file path, with strict path traversal security checks.
* **Parameters**: `file_path` (*str*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Reading a specific file into context safely.

### 5. `read_many`
* **Purpose**: Retrieves full contents of multiple relative file paths in a single call, handling partial success if some paths fail.
* **Parameters**: `file_paths` (*list[str]*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Batch fetching multiple source files efficiently.

### 6. `project_dependencies`
* **Purpose**: Analyze file dependencies - what files this file depends on, what files depend on this file, local vs external vs unresolved.
* **Parameters**: `file_path` (*str*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Understanding dependency relationships and import graphs.

### 7. `project_diff`
* **Purpose**: Inspects Git status and unified diffs for staged, unstaged, or specific commits.
* **Parameters**: `path` (*Optional[str]*), `staged` (*bool*), `commit` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Reviewing uncommitted edits or verifying changes.

---

## Architecture

LLMScribe uses a shared core architecture:

```
                    LLMScribe Core
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
         MCP            CLI            GUI
```

Both the MCP server and CLI share the same underlying core functions, ensuring consistent behavior and output across all interfaces.

---

## Agent Workflow

Recommended workflow sequence for AI agents:

```
project_map → search → read/read_many
```

### Example: Understand a New Repository
1. **`project_map()`**: Get the overall directory tree to understand repository architecture.
2. **`search("main")`**: Search for key entrypoints or symbol definitions.
3. **`read("src/main.py")` or `read_many(["src/main.py", "src/utils.py"])`**: Read the relevant source files.

### Example: Analyze Dependencies
1. **`search("FastAPI")`**: Find files using FastAPI.
2. **`project_dependencies("src/api/main.py")`**: Analyze dependencies for key files.
3. **`read_many()`**: Read all dependency files together.

---

## CLI Usage

LLMScribe CLI exposes the same core capabilities as the MCP server with a clean command-oriented interface.

```
LLMScribe — code context for AI agents

Usage:
  llmscribe <command> [options]

Commands:
  map              Show project structure
  overview         Generate project overview
  search           Search project code
  read             Read a file or line range
  read-many        Read multiple files
  dependencies     Show file dependencies
  diff             Show project changes

Other:
  version          Show version
  help             Show help
```

### Command Examples:

```bash
# Show project structure
llmscribe map

# Generate full project overview  
llmscribe overview

# Search project code
llmscribe search "authentication"

# Read specific files
llmscribe read src/auth/service.py
llmscribe read-many src/auth/service.py src/api/login.py

# Analyze dependencies
llmscribe dependencies src/auth/service.py

# Show git changes
llmscribe diff

# JSON output for scripts/AI agents
llmscribe search "auth" --json
llmscribe map --json
```

---

## JSON Mode

All tools support `format="json"` for structured, machine-readable output:

### Example JSON Response (search):

```json
{
  "ok": true,
  "tool": "search", 
  "path": "/path/to/project",
  "data": {
    "query": "authentication",
    "root_path": "/path/to/project",
    "matches": [
      {
        "file_path": "src/auth/service.py",
        "line_number": 10,
        "line_content": "from fastapi.security import OAuth2PasswordBearer",
        "match_type": "content",
        "matched_text": "auth"
      }
    ],
    "file_count": 5,
    "match_count": 12,
    "truncated": false,
    "truncation_limit": 1000
  },
  "metadata": {
    "query": "authentication",
    "file_count": 5,
    "match_count": 12,
    "truncated": false
  }
}
```

---

## Project Positioning

**LLMScribe provides clean, deterministic, structured code context. The AI agent provides the intelligence.**

- ✅ **Deterministic**: No LLM, embeddings, or AI ranking
- ✅ **Structured**: Consistent JSON output schemas
- ✅ **Agent-friendly**: Designed specifically for AI agent workflows
- ❌ **NOT** an AI coding agent
- ❌ **NOT** a semantic search engine
- ❌ **NOT** a generic Git client

---

## GitHub Repository Support

All tools can inspect remote GitHub repositories directly. Use `repo` parameter instead of `path`.

### Example:
```python
# Map a remote repo
project_map(repo="owner/repo")

# Search code in a remote repo
search(query="FastAPI", repo="owner/repo")
```

> **Note**: `path` and `repo` are mutually exclusive.

---

## Install

```bash
pip install llmscribe
```

## Version

**LLMScribe v1.2.0**

This release includes:
- Final MCP toolset with exactly 7 tools
- Modern command-oriented CLI
- Improved search with structured output
- New dependency analysis with provider abstraction
- Machine-readable JSON output for all commands

## License

Apache License 2.0

## Repository

[GitHub Repository](https://github.com/AMRITO-KUNDU/LLMScribe)

## Issues & Support

[GitHub Issues](https://github.com/AMRITO-KUNDU/LLMScribe/issues)
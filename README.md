# LLMScribe

Turn any local project into clean, structured context for AI agents.

---

## For AI Agents (primary)

LLMScribe provides a lightweight Model Context Protocol (MCP) server that gives AI coding agents (Cursor, Claude Desktop, Windsurf, Roo Code, Goose, etc.) fast, composable tools to inspect project structures, read source files, search codebases, and view Git diffs without heavy dependencies.

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

## GitHub Repository Support

LLMScribe tools can inspect remote GitHub repositories directly without cloning! All 7 MCP tools accept optional `repo` and `ref` parameters.

### Example MCP Calls:
```python
# Map a remote repo on main branch
project_map(repo="owner/repo")

# Search code in a specific release tag or branch
project_search(query="FastAPI", repo="https://github.com/owner/repo", ref="v1.0.0")

# Fetch git diff between commit range on remote GitHub repo
project_diff(repo="owner/repo", commit="main..feature")
```

### GitHub Authentication & Rate Limits
Set `GITHUB_TOKEN` or `GH_TOKEN` environment variable to authenticate requests, access private repositories, and raise GitHub API rate limits (5,000 requests/hr vs 60 requests/hr for unauthenticated calls).

```bash
export GITHUB_TOKEN="ghp_your_personal_access_token"
```

> **Note**: `path` and `repo` are mutually exclusive. Passing both in a tool call returns an `invalid_argument` error code.

---

## Agent Recipes

Copy-paste recommended workflow sequences for AI agents:

### Recipe 1: Understand a New Repository
1. **`project_map(repo="owner/repo")`**: Get the overall directory tree to understand repository architecture.
2. **`project_search(query, repo="owner/repo")`**: Search for key entrypoints or symbol definitions (e.g. `"main"`, `"FastAPI"`, `"App"`).
3. **`project_get_files(file_paths, repo="owner/repo")`**: Batch-fetch the relevant source files discovered during step 2.

### Recipe 2: Review Local or Remote Changes
1. **`project_diff(staged=False)`** or **`project_diff(repo="owner/repo", commit="v1.0.0..v1.1.0")`**: Get modified files (`changed_files`) and the git diff summary.
2. **`project_get_files(file_paths=changed_files)`**: Fetch the complete, updated content of all modified files for full review context.

### Recipe 3: Load a Specific Feature Area
1. **`project_list_files(extension=".py")`**: Filter and list all Python files (or any target extension).
2. **`project_get_files(file_paths)`**: Load target module files into context in a single call.

---

## Tools Reference

All tools support optional `path` (local filesystem) or `repo` + `ref` (GitHub repository), and `format` (`"markdown"` or `"json"`, default: `"markdown"`). Default local path resolves to current working directory (`cwd`).

### 1. `project_overview`
* **Purpose**: Generates full directory structure and full contents of all supported text files.
* **Parameters**: `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Getting a complete overview of small-to-medium codebases in one call.

### 2. `project_map`
* **Purpose**: Generates directory tree structure and text file path listing without file contents.
* **Parameters**: `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Exploring repository structure before selecting specific files to read.

### 3. `project_search`
* **Purpose**: Keyword search across relative file paths and line-by-line file contents.
* **Parameters**: `query` (*str*), `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Locating specific symbols, function definitions, or import statements.

### 4. `project_list_files`
* **Purpose**: Lists all text files in the project, respecting `.gitignore` rules.
* **Parameters**: `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `extension` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Discovering files of a specific extension or building a file index.

### 5. `project_get_file`
* **Purpose**: Retrieves full content of a single specific relative file path, with strict path traversal security checks.
* **Parameters**: `file_path` (*str*), `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Reading a specific file into context safely.

### 6. `project_get_files`
* **Purpose**: Retrieves full contents of multiple relative file paths in a single call, handling partial success if some paths fail.
* **Parameters**: `file_paths` (*list[str]*), `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Batch fetching multiple source files efficiently.

### 7. `project_diff`
* **Purpose**: Inspects Git status (`changed_files`) and unified diffs for staged, unstaged, or specific commits.
* **Parameters**: `path` (*Optional[str]*), `repo` (*Optional[str]*), `ref` (*Optional[str]*), `staged` (*bool*), `commit` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Reviewing uncommitted edits or verifying changes before completing a task.

---

## JSON Mode & Envelope

When specifying `format="json"`, tools return a structured response envelope with metadata (`path` is set to `/path/to/project` for local or `github.com/owner/repo@ref` for GitHub):

### `project_overview` JSON Example:

```json
{
  "ok": true,
  "tool": "project_overview",
  "path": "/path/to/project",
  "data": {
    "tree": "project/\n├── src\n│   └── main.py\n└── README.md\n",
    "files": [
      {
        "path": "src/main.py",
        "content": "print('hello world')\n"
      },
      {
        "path": "README.md",
        "content": "# Project Docs\n"
      }
    ]
  },
  "metadata": {
    "file_count": 2,
    "character_count": 84
  }
}
```

### JSON Error Envelope Example:

```json
{
  "ok": false,
  "tool": "project_get_file",
  "error": {
    "code": "path_traversal",
    "message": "Path traversal attempt detected. '../outside.txt' is outside root directory."
  }
}
```

---

## Stable Error Codes

LLMScribe uses a standardized closed set of error codes across both JSON (`error.code`) and Markdown mode (`Error [{code}]: ...`):

| Error Code | Description |
|---|---|
| `invalid_path` | Target project directory does not exist. |
| `not_a_directory` | Provided path exists but is not a directory. |
| `invalid_argument` | Missing or invalid parameter (e.g. empty file path or specifying both `path` and `repo`). |
| `empty_query` | Search query string is empty. |
| `file_not_found` | Requested file path does not exist. |
| `not_a_file` | Target path exists but is a directory, not a file. |
| `not_text_file` | Target file does not have a supported text extension. |
| `path_traversal` | Requested file path attempts to escape project root directory. |
| `git_unavailable` | Target directory is not a Git repository or `git` executable is unavailable. |
| `invalid_ref` | Provided commit ref or GitHub reference contains invalid/unsafe characters. |
| `git_error` | Git command execution failed. |
| `repo_not_found` | Target GitHub repository or reference was not found (404). |
| `auth_required` | GitHub token authentication required or token invalid (401/403). |
| `rate_limited` | GitHub API rate limit exceeded (403 Rate Limit). |
| `github_unavailable` | GitHub service error or network request failure (5xx / network error). |
| `read_error` | File read I/O error occurred. |
| `internal_error` | Unexpected internal exception. |

---

## Limits & Truncation Guards

To prevent prompt context blow-ups, LLMScribe enforces deterministic guards:

* **`project_get_files` Batch Limit**: Maximum of 50 files per call. If more are requested, the first 50 are processed and `metadata.truncated = true` is reported.
* **Content Character Caps**: Total content output is capped at 400,000 characters for `project_overview` and `project_get_files`. If capped, `metadata.truncated = true` and `metadata.truncation_note` are surfaced.
* **`project_diff` Character Cap**: Diff outputs are capped at 200,000 characters with `metadata.truncated = true`.

---

## CLI / GUI / CUI (secondary)

Human developer interfaces:

* **Standalone Windows Executable**: Download `LLMScribe-GUI.exe` directly from GitHub Releases (no Python required).
* **CLI**: `llmscribe --path /path/to/project --output summary.txt`
* **GUI (from Python)**: `llmscribe-gui`
* **CUI**: `llmscribe-cui`

### Building the Standalone Executable from Source

To build `LLMScribe-GUI.exe` locally using PyInstaller:

```bash
pip install pyinstaller
python build_exe.py
```

The compiled binary will be placed at `dist/LLMScribe-GUI.exe`.

---

## Install from Source

```bash
git clone https://github.com/AMRITO-KUNDU/LLMScribe.git
cd LLMScribe
pip install -e .
```

---

## License

[Apache-2.0](LICENSE)

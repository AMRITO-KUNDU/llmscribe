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

## Agent Recipes

Copy-paste recommended workflow sequences for AI agents:

### Recipe 1: Understand a New Repository
1. **`project_map()`**: Get the overall directory tree to understand repository architecture.
2. **`project_search(query)`**: Search for key entrypoints or symbol definitions (e.g. `"main"`, `"FastAPI"`, `"App"`).
3. **`project_get_files(file_paths)`**: Batch-fetch the relevant source files discovered during step 2.

### Recipe 2: Review Local Changes
1. **`project_diff(staged=False)`**: Get modified files (`changed_files`) and the git diff summary.
2. **`project_get_files(file_paths=changed_files)`**: Fetch the complete, updated content of all modified files for full review context.

### Recipe 3: Load a Specific Feature Area
1. **`project_list_files(extension=".py")`**: Filter and list all Python files (or any target extension).
2. **`project_get_files(file_paths)`**: Load target module files into context in a single call.

---

## Tools Reference

All tools support an optional `format` parameter (`"markdown"` or `"json"`, default: `"markdown"`). Default path resolves to the current working directory (`cwd`).

### 1. `project_overview`
* **Purpose**: Generates full directory structure and full contents of all supported text files.
* **Parameters**: `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Getting a complete overview of small-to-medium codebases in one call.

### 2. `project_map`
* **Purpose**: Generates directory tree structure and text file path listing without file contents.
* **Parameters**: `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Exploring repository structure before selecting specific files to read.

### 3. `project_search`
* **Purpose**: Keyword search across relative file paths and line-by-line file contents.
* **Parameters**: `query` (*str*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Locating specific symbols, function definitions, or import statements.

### 4. `project_list_files`
* **Purpose**: Lists all text files in the project, respecting `.gitignore` rules.
* **Parameters**: `path` (*Optional[str]*), `extension` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Discovering files of a specific extension or building a file index.

### 5. `project_get_file`
* **Purpose**: Retrieves full content of a single specific relative file path, with strict path traversal security checks.
* **Parameters**: `file_path` (*str*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Reading a specific file into context safely.

### 6. `project_get_files`
* **Purpose**: Retrieves full contents of multiple relative file paths in a single call, handling partial success if some paths fail.
* **Parameters**: `file_paths` (*list[str]*), `path` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Batch fetching multiple source files efficiently.

### 7. `project_diff`
* **Purpose**: Inspects Git status (`changed_files`) and unified diffs for staged, unstaged, or specific commits.
* **Parameters**: `path` (*Optional[str]*), `staged` (*bool*), `commit` (*Optional[str]*), `format` (*str* = `"markdown"`)
* **When to use**: Reviewing uncommitted edits or verifying changes before completing a task.

---

## JSON Mode & Envelope

When specifying `format="json"`, tools return a structured response envelope with metadata:

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
| `invalid_argument` | Missing or invalid parameter (e.g. empty file path). |
| `empty_query` | Search query string is empty. |
| `file_not_found` | Requested file path does not exist. |
| `not_a_file` | Target path exists but is a directory, not a file. |
| `not_text_file` | Target file does not have a supported text extension. |
| `path_traversal` | Requested file path attempts to escape project root directory. |
| `git_unavailable` | Target directory is not a Git repository or `git` executable is unavailable. |
| `invalid_ref` | Provided commit ref contains invalid/unsafe characters. |
| `git_error` | Git command execution failed. |
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

* **CLI**: `llmscribe --path /path/to/project --output summary.txt`
* **GUI**: `llmscribe-gui`
* **CUI**: `llmscribe-cui`

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

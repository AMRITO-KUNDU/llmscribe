# LLMScribe

Turn any local project into clean, structured context for AI agents.

---

## For AI Agents (primary)

LLMScribe provides a lightweight Model Context Protocol (MCP) server that gives AI coding agents (Cursor, Claude Desktop, Windsurf, Roo Code, Goose, etc.) fast tools to inspect project structures, read source files, search codebases, and view Git diffs without heavy dependencies.

### Installation

```bash
pip install llmscribe
```

### Running the MCP Server

```bash
llmscribe-mcp
```

### Configuration Examples

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

### Tools

All tools support an optional `format` parameter (`"markdown"` or `"json"`, default: `"markdown"`). Default path resolves to the current working directory (`cwd`).

#### 1. `project_overview`
* **Purpose**: Generates full directory structure and full contents of all supported text files.
* **Parameters**:
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: When an agent needs a complete overview of small-to-medium codebases in one prompt.

#### 2. `project_map`
* **Purpose**: Generates directory tree structure only, omitting file contents.
* **Parameters**:
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: When exploring project layout or finding file locations in large repositories.

#### 3. `project_search`
* **Purpose**: Simple keyword search across relative file paths and line-by-line file contents.
* **Parameters**:
  * `query` (*str*): Keyword to search.
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: Locating specific symbols, function calls, or file names without loading full file contents.

#### 4. `project_list_files`
* **Purpose**: Lists all text files in the project, respecting `.gitignore` rules.
* **Parameters**:
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `extension` (*Optional[str]*): Optional file extension filter (e.g. `".py"` or `"py"`).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: Discovering files of a specific type or getting an index of all readable project paths.

#### 5. `project_get_file`
* **Purpose**: Retrieves full content of a single specific relative file path, with strict path traversal security checks.
* **Parameters**:
  * `file_path` (*str*): Relative path to target file.
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: Reading a specific file into context safely.

#### 6. `project_get_files`
* **Purpose**: Retrieves full contents of multiple relative file paths in a single call, handling partial success if some paths fail.
* **Parameters**:
  * `file_paths` (*list[str]*): List of relative file paths.
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: Batch fetching multiple source files efficiently.

#### 7. `project_diff`
* **Purpose**: Inspects Git status and unified diffs for staged, unstaged, or specific commits.
* **Parameters**:
  * `path` (*Optional[str]*): Target project path (default: current working directory).
  * `staged` (*bool*): If `True`, returns staged diff (`git diff --cached`).
  * `commit` (*Optional[str]*): Safe commit ref to diff against (e.g. `"HEAD~1"` or `"main"`).
  * `format` (*str*): Output format (`"markdown"` or `"json"`, default: `"markdown"`).
* **When to use**: Reviewing uncommitted changes or verifying commits before completing code modifications.

---

### JSON Mode

When specifying `format="json"`, tools return a structured response envelope:

```json
{
  "ok": true,
  "tool": "project_get_file",
  "path": "/path/to/project",
  "data": {
    "file_path": "src/main.py",
    "content": "print('hello world')\n"
  }
}
```

Error response envelope example:

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

## CLI / GUI / CUI (secondary)

Human developer tools included with LLMScribe:

* **Command Line Interface (CLI)**:
  ```bash
  llmscribe --path /path/to/project --output project_summary.txt
  ```
* **Desktop Graphical App (GUI)**:
  ```bash
  llmscribe-gui
  ```
* **Terminal Menu (CUI)**:
  ```bash
  llmscribe-cui
  ```

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

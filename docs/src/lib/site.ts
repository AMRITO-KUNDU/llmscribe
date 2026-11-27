export const SITE = {
  name: "LLMScribe",
  version: "3.0.0",
  tagline: "The filesystem layer for AI agents.",
  description:
    "Read, search, trace and change a codebase through one interface, with identical output on Linux, macOS and Windows. Runs entirely on your machine.",
  author: "Amrito Kundu",
  github: "https://github.com/AMRITO-KUNDU/llmscribe",
  pypi: "https://pypi.org/project/llmscribe/",
  releases: "https://github.com/AMRITO-KUNDU/llmscribe/releases/latest",
  issues: "https://github.com/AMRITO-KUNDU/llmscribe/issues",
  registry: "https://registry.modelcontextprotocol.io/?q=llmscribe",
  registryName: "io.github.AMRITO-KUNDU/llmscribe",
  licenseUrl: "https://github.com/AMRITO-KUNDU/llmscribe/blob/main/LICENSE",
  license: "Apache License 2.0",
  python: "3.10+",
  install: "pip install llmscribe",
} as const;

export const NAV = [
  { href: "#mcp", label: "For AI Agents" },
  { href: "#connect", label: "Connect" },
  { href: "#interfaces", label: "4 Interfaces" },
  { href: "#tools", label: "MCP Tools" },
  { href: "#output", label: "Output & JSON" },
  { href: "#install", label: "Install" },
  { href: "#faq", label: "FAQ" },
] as const;

export const EXTENSIONS = [
  ".py",
  ".js",
  ".ts",
  ".jsx",
  ".tsx",
  ".java",
  ".go",
  ".rs",
  ".md",
  ".json",
  ".yaml",
  ".toml",
  ".html",
  ".css",
  ".sh",
  ".sql",
];

export const IGNORED = [
  ".git",
  "node_modules",
  "venv",
  "__pycache__",
  "dist",
  "build",
  ".idea",
  ".vscode",
  ".DS_Store",
  "Thumbs.db",
  ".gitignore rules",
];

export const SAMPLE_TREE = `Selected Files Directory Structure:

my-project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md`;

export const SAMPLE_CONTENTS = `File Contents:

--- src/main.py ---
def hello():
    print("Hello world")

--- src/utils.py ---
def add(a: int, b: int) -> int:
    return a + b

--- tests/test_main.py ---
from src.main import hello

def test_hello():
    hello()

--- pyproject.toml ---
[project]
name = "my-project"
version = "1.2.0"
requires-python = ">=3.10"

--- README.md ---
# my-project

A sample project exported with LLMScribe.`;

export const SAMPLE_FULL = `${SAMPLE_TREE}

${SAMPLE_CONTENTS}
`;

export const SAMPLE_JSON = `{
  "ok": true,
  "tool": "project_overview",
  "source": "local",
  "path": "/path/to/project",
  "data": {
    "root_path": "/path/to/project",
    "tree": "my-project/\\n├── src\\n│   └── main.py\\n└── README.md",
    "files": [
      {
        "path": "README.md",
        "content": "# my-project\\n"
      },
      {
        "path": "src/main.py",
        "content": "def hello():\\n    print(\\"Hello world\\")\\n"
      }
    ],
    "file_count": 2,
    "character_count": 101,
    "truncated": false,
    "truncation_note": "",
    "truncation_limit": 400000,
    "omitted_files": [],
    "skipped_files": [],
    "skipped_count": 0,
    "warnings": []
  },
  "metadata": {
    "file_count": 2,
    "character_count": 101,
    "truncated": false
  },
  "command": "overview"
}`;

export const PYTHON_API = `from llmscribe import Repository, LLMScribeError

repo = Repository(".")                      # or Repository("/path/to/project")

tree = repo.map()                           # directory tree, no file contents
found = repo.search("auth")                 # literal matches, ordered
file = repo.read("src/main.py")             # .ok / .error_code, never raises

print(tree.tree)
print(found.match_count)
if file.ok:
    print(file.content)

deps = repo.dependencies("src/main.py")     # raises LLMScribeError
print(deps.file_dependencies.local_dependencies)
print(deps.used_by)                         # what imports it`;

// Connection instructions for popular MCP clients. Each entry was verified against
// the client's official documentation. Every client connects over stdio.

export type ConnectApp = {
  app: string;
  where: string;
  config: string;
  lang?: string;
  note?: string;
};

export const CONNECT: ConnectApp[] = [
  {
    app: "Claude Desktop",
    where: "claude_desktop_config.json (Settings → Developer → Edit Config)",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
    note: "macOS: ~/Library/Application Support/Claude/ · Windows: %APPDATA%\\Claude\\. Quit and reopen after saving.",
  },
  {
    app: "Claude Code",
    where: "terminal",
    lang: "bash",
    config: `claude mcp add llmscribe -- llmscribe-mcp`,
    note: "Verify with `claude mcp list`.",
  },
  {
    app: "Cursor",
    where: ".cursor/mcp.json (or ~/.cursor/mcp.json)",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
    note: "Restart Cursor, then Customize → MCPs.",
  },
  {
    app: "VS Code (Copilot)",
    where: ".vscode/mcp.json",
    lang: "json",
    config: `{
  "servers": {
    "llmscribe": {
      "type": "stdio",
      "command": "llmscribe-mcp"
    }
  }
}`,
    note: "Uses `servers`, not `mcpServers`.",
  },
  {
    app: "Windsurf (Cascade)",
    where: "~/.codeium/mcp_config.json",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
    note: "Windsurf Settings → Cascade → MCP → View Raw Config.",
  },
  {
    app: "Cline",
    where: "MCP Servers → Configure → Configure MCP Servers",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
  },
  {
    app: "Roo Code",
    where: "mcp_settings.json (global) or .roo/mcp.json (project)",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
  },
  {
    app: "LM Studio",
    where: "~/.lmstudio/mcp.json",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
    note: "Program tab → Install → Edit mcp.json. Follows Cursor notation.",
  },
  {
    app: "Zed",
    where: "settings.json (Settings → AI → MCP Servers)",
    lang: "json",
    config: `{
  "context_servers": {
    "llmscribe": {
      "command": "llmscribe-mcp",
      "args": [],
      "env": {}
    }
  }
}`,
    note: "Zed uses `context_servers`.",
  },
  {
    app: "Continue",
    where: "~/.continue/config.yaml",
    lang: "yaml",
    config: `name: LLMScribe
version: 1.0.0
schema: v1
mcpServers:
  - name: LLMScribe
    command: llmscribe-mcp`,
    note: "Also reads Cursor/Claude/Cline JSON dropped into .continue/mcpServers/.",
  },
  {
    app: "JetBrains IDEs",
    where: "Settings → Tools → AI Assistant → MCP → Add",
    lang: "json",
    config: `{
  "mcpServers": {
    "llmscribe": { "command": "llmscribe-mcp" }
  }
}`,
    note: "IntelliJ, WebStorm, … Can also Import from Claude.",
  },
  {
    app: "Goose",
    where: "~/.config/goose/config.yaml",
    lang: "yaml",
    config: `extensions:
  llmscribe:
    name: llmscribe
    enabled: true
    type: stdio
    cmd: llmscribe-mcp
    args: []
    timeout: 300`,
  },
  {
    app: "OpenAI Codex CLI",
    where: "~/.codex/config.toml",
    lang: "toml",
    config: `[mcp_servers.llmscribe]
command = "llmscribe-mcp"`,
  },
];

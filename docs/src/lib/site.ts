export const SITE = {
  name: "LLMScribe",
  version: "1.1.0",
  tagline: "Turn any project folder into clean, structured context for AI agents & developers.",
  description:
    "LLMScribe provides a lightweight Model Context Protocol (MCP) server for AI coding agents (Cursor, Claude, Windsurf, Roo Code, Goose), a standalone Windows GUI, a Python CLI, and a terminal menu.",
  author: "Amrito Kundu",
  github: "https://github.com/AMRITO-KUNDU/LLMScribe",
  pypi: "https://pypi.org/project/llmscribe/",
  issues: "https://github.com/AMRITO-KUNDU/LLMScribe/issues",
  licenseUrl: "https://github.com/AMRITO-KUNDU/LLMScribe/blob/main/LICENSE",
  license: "Apache License 2.0",
  python: "3.10+",
  install: "pip install llmscribe",
} as const;

export const NAV = [
  { href: "#mcp", label: "For AI Agents" },
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
version = "1.1.0"
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
  "path": "/path/to/project",
  "data": {
    "tree": "my-project/\n├── src\n│   └── main.py\n└── README.md\n",
    "files": [
      {
        "path": "src/main.py",
        "content": "def hello():\n    print(\"Hello world\")\n"
      },
      {
        "path": "README.md",
        "content": "# my-project\n"
      }
    ]
  },
  "metadata": {
    "file_count": 2,
    "character_count": 92
  }
}`;

export const PYTHON_API = `from pathlib import Path
from llmscribe.core.writer import run, build_project_summary
from llmscribe.mcp import project_overview, project_diff

# 1. Direct Python Core Usage
text = build_project_summary(Path("/path/to/project"))

# 2. Call MCP tools programmatically (JSON mode or Markdown)
json_overview = project_overview("/path/to/project", format="json")
diff_markdown = project_diff("/path/to/project", staged=False)`;

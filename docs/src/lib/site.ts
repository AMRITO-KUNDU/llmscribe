export const SITE = {
  name: "LLMScribe",
  version: "1.0.0",
  tagline: "Turn any project folder into one clean text file that AI tools can read.",
  description:
    "LLMScribe walks a project, builds a directory tree, and dumps the full contents of every source file into a single .txt file. Perfect for pasting into ChatGPT, Claude, Grok, Cursor, or any other AI coding assistant.",
  author: "Amrito Kundu",
  github: "https://github.com/AMRITO-KUNDU/LLMScribe",
  pypi: "https://pypi.org/project/llmscribe/",
  issues: "https://github.com/AMRITO-KUNDU/LLMScribe/issues",
  licenseUrl:
    "https://github.com/AMRITO-KUNDU/LLMScribe/blob/main/LICENSE",
  license: "Apache License 2.0",
  python: "3.10+",
  install: "pip install llmscribe",
} as const;

export const NAV = [
  { href: "#how", label: "How it works" },
  { href: "#interfaces", label: "Interfaces" },
  { href: "#output", label: "Output" },
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
version = "0.1.0"
requires-python = ">=3.10"

--- README.md ---
# my-project

A tiny sample app used in the LLMScribe walkthrough.`;

export const SAMPLE_FULL = `${SAMPLE_TREE}

${SAMPLE_CONTENTS}
`;

export const PYTHON_API = `from pathlib import Path
from llmscribe.core.writer import run, build_project_summary

# Write a file
run(
    project_path=Path("/path/to/project"),
    output_file=Path("summary.txt"),
    tree_only=False,
)

# Or just get the text
text = build_project_summary(Path("/path/to/project"))`;

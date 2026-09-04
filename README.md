# LLMScribe

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/AMRITO-KUNDU/llmscribe)

**Export an entire project folder into a single, LLM-ready text file** — directory tree plus full contents of every supported source file.

Ideal for feeding codebases to AI coding assistants, code reviews, documentation, debugging, and sharing projects without the noise of build artifacts and dependencies.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI](#cli)
  - [GUI App](#gui-app)
  - [Terminal Menu (CUI)](#terminal-menu-cui)
  - [Python API](#python-api)
- [Output Format](#output-format)
- [What Gets Included](#what-gets-included)
- [What Gets Ignored](#what-gets-ignored)
- [Project Structure](#project-structure)
- [Core API Reference](#core-api-reference)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| **Directory tree** | Visual `├──` tree of your project structure |
| **Tree-only mode** | Export just the structure with `--tree-only` or the GUI checkbox |
| **Full file contents** | Complete, untruncated contents of every supported text file |
| **Smart filtering** | Skips build outputs, dependencies, IDE files, and OS noise by default |
| **`.gitignore` aware** | Automatically loads and respects the project's own `.gitignore` |
| **Three interfaces** | Desktop GUI, interactive terminal menu, and scriptable CLI |
| **Embeddable core** | Import `llmscribe.core` into other Python projects |
| **Zero dependencies** | Pure standard library (Tkinter only needed for GUI) |
| **Cross-platform** | Windows, macOS, and Linux |

---

## Quick Start

```bash
pip install llmscribe          # or: pip install -e . from source
llmscribe --path /path/to/project
```

This writes `project_overview.txt` in the current directory containing the tree + full file contents.

---

## Installation

### From PyPI

```bash
pip install llmscribe
```

This installs three commands: `llmscribe`, `llmscribe-gui`, and `llmscribe-cui`.

### From source (development)

```bash
git clone https://github.com/AMRITO-KUNDU/llmscribe.git
cd llmscribe
pip install -e .
```

Editable install (`-e`) picks up local code changes immediately.

### Publishing (maintainers)

```bash
pip install build twine
python -m build
twine upload dist/*
```

For automated releases, configure PyPI Trusted Publishing and push a tag such as `v1.0.0`. The workflow in `.github/workflows/publish.yml` handles the rest.

---

## Usage

### CLI

Scriptable interface for automation and CI.

```bash
# Basic usage
llmscribe --path /path/to/project

# Custom output file
llmscribe --path /path/to/project --output ~/exports/my_project.txt

# Tree only (no file contents)
llmscribe --path /path/to/project --tree-only

# GUI folder picker
llmscribe --gui

# Interactive (prompts for path, falls back to GUI picker)
llmscribe

# Version
llmscribe --version
```

| Flag | Default | Description |
|------|---------|-------------|
| `--path PATH` | — | Project folder to scan |
| `--output FILE` | `project_overview.txt` | Output path (parent dirs created automatically) |
| `--tree-only` | `false` | Export only the directory tree |
| `--gui` | `false` | Open a GUI folder picker |
| `--version` | — | Print version and exit |

```bash
llmscribe --help
```

### GUI App

Desktop app with a two-panel layout: controls on the left, live preview on the right.

```bash
llmscribe-gui
# or
llmscribe --gui
# or without console scripts
python -m llmscribe.gui
```

1. Select the project folder (folder icon or type the path).
2. Adjust the output path if needed (defaults to `<project>/project_overview.txt`).
3. Optionally enable **Tree only**.
4. Click **Generate**. Preview updates; use **Copy output** or **Open file**.

Scanning runs in a background thread so the UI stays responsive.

### Terminal Menu (CUI)

Interactive numbered menu for terminal users.

```bash
llmscribe-cui
```

```
LLMScribe CUI
1) Enter project folder path
2) Open GUI folder picker
3) Quit
Choose an option [1-3]:
```

You can also pass flags to skip the menu:

```bash
llmscribe-cui --path /path/to/project --output summary.txt
llmscribe-cui --gui --tree-only
```

### Python API

```python
from pathlib import Path
from llmscribe.core.writer import build_project_summary, run

# Return summary as a string
summary = build_project_summary(Path("/path/to/project"), tree_only=False)

# Generate and write to disk
run(
    project_path=Path("/path/to/project"),
    output_file=Path("summary.txt"),
    tree_only=False,
)
```

Lower-level components:

```python
from pathlib import Path
from llmscribe.core.tree_builder import DEFAULT_IGNORE, generate_tree, load_gitignore
from llmscribe.core.file_reader import extract_contents
from llmscribe import __version__

project = Path("/path/to/project")
ignore = [*DEFAULT_IGNORE, *load_gitignore(project)]

tree = generate_tree(project, ignore)
contents = extract_contents(project, ignore)

print(tree)
print(contents)
print(f"LLMScribe {__version__}")
```

---

## Output Format

Plain UTF-8 text with two sections:

```text
Selected Files Directory Structure:

my-project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md

File Contents:

--- src/main.py ---
<full contents of main.py>

--- src/utils.py ---
<full contents of utils.py>

...
```

In tree-only mode only the directory structure is written. Files are processed in sorted order; contents are never truncated.

---

## What Gets Included

Files whose extension is in the allowlist below are read in full:

| Category | Extensions |
|----------|------------|
| Python | `.py` |
| JavaScript / TypeScript | `.js` `.ts` `.jsx` `.tsx` |
| Systems | `.c` `.cpp` `.cc` `.cxx` `.h` `.hpp` `.rs` `.go` `.zig` `.v` `.d` `.nim` `.cr` |
| JVM & others | `.java` `.scala` `.kt` `.clj` `.cljs` `.rb` `.php` `.swift` `.dart` `.lua` `.pl` `.pm` `.r` `.m` `.hs` `.ml` `.fs` `.fsx` `.vb` `.cs` `.ex` `.exs` `.elm` `.pony` `.tcl` `.tk` |
| Web | `.html` `.htm` `.css` `.scss` `.sass` `.less` `.vue` `.svelte` `.pug` `.ejs` `.hbs` `.handlebars` `.mustache` `.twig` `.jsp` `.asp` `.aspx` `.erb` `.haml` |
| Config & manifests | `.json` `.xml` `.yaml` `.yml` `.toml` `.ini` `.cfg` `.conf` `.properties` `.env` `.dotenv` `.lock` `.sum` `.mod` `.gradle` `.pom` `.gitignore` `.gitattributes` `.editorconfig` `.prettierrc` `.eslintrc` `.babelrc` `.nimble` |
| Shell & scripts | `.sh` `.bash` `.zsh` `.fish` `.ps1` `.bat` `.cmd` `.awk` `.sed` |
| Documentation | `.md` `.rst` `.adoc` `.tex` `.bib` `.txt` |
| Data (text) | `.csv` `.tsv` `.sql` |
| Logs | `.log` |

Binary formats (PDF, DOCX, images, databases, etc.) are excluded.

---

## What Gets Ignored

Default ignore patterns (applied together with the project's `.gitignore`):

| Category | Patterns |
|----------|----------|
| Version control | `.git` `.svn` `.hg` |
| Dependencies | `node_modules` `vendor` `packages` |
| Python | `venv` `__pycache__` `.eggs` `*.egg-info` |
| Build outputs | `dist` `build` `target` `out` `bin` `obj` |
| IDEs | `.idea` `.vscode` `.vs` |
| OS artifacts | `.DS_Store` `Thumbs.db` `desktop.ini` |
| Logs & temp | `logs` `tmp` `temp` `.tmp` `.cache` `*.log` |
| Coverage | `.coverage` `coverage` `.nyc_output` |
| Secrets | `.env` `.env.*` `secrets` |

Any non-comment patterns from the project's own `.gitignore` are loaded and applied on top of these defaults. Common Git-style globs, anchored rules, and negation (`!`) are supported.

---

## Project Structure

```text
llmscribe/
├── src/
│   └── llmscribe/
│       ├── __init__.py          # Package version
│       ├── core/                # Scanning & writing logic
│       │   ├── file_reader.py   # Extension allowlist + content extraction
│       │   ├── tree_builder.py  # Directory tree + ignore engine
│       │   └── writer.py        # Orchestrates tree + contents
│       ├── cli/                 # Scriptable CLI
│       ├── cui/                 # Interactive terminal menu
│       └── gui/                 # Tkinter desktop app
├── tests/
├── pyproject.toml
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

---

## Core API Reference

### `llmscribe.core.writer`

#### `build_project_summary(project_path: Path, tree_only: bool = False) → str`

Builds and returns the complete summary string.

#### `run(project_path: Path, output_file: Path, tree_only: bool = False) → None`

Generates the summary and writes it to `output_file`. Creates parent directories as needed. Prints progress and line count.

### `llmscribe.core.file_reader`

- `extract_contents(root, ignore_patterns) → str` — walks the tree and concatenates supported file contents with `--- path ---` headers.
- `is_text_file(path) → bool` — checks against the extension allowlist.
- `TEXT_FILE_EXTENSIONS` — the set of supported suffixes.

### `llmscribe.core.tree_builder`

- `generate_tree(root, ignore_patterns) → str` — visual directory tree.
- `load_gitignore(root) → list[str]` — non-comment patterns from `.gitignore`.
- `should_ignore(path, ignore_patterns, root=None) → bool`
- `DEFAULT_IGNORE` — built-in ignore set.
- `IgnoreMatcher` — Git-style matcher used internally.

---

## Requirements

- **Python 3.10** or higher
- **Tkinter** — only required for the GUI (`llmscribe-gui`, `llmscribe --gui`, or CUI option 2). The core library and non-GUI CLI work without it.

On Linux you may need to install the system package:

```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

No third-party Python packages are required.

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

Please keep the pure-stdlib design and add tests for new behavior.

---

## License

LLMScribe is licensed under the [Apache License 2.0](LICENSE).

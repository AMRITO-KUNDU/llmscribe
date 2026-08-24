# LLMScribe

LLMScribe is an open-source Python tool that exports an entire software project into a single readable text file. It generates a directory tree followed by the full contents of every supported source file, making it ideal for AI coding assistants, code reviews, documentation, debugging, and sharing codebases.

It ships with three interfaces so you can use whichever fits your workflow: a graphical desktop app, an interactive terminal menu, and a scriptable CLI.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [CLI](#cli)
  - [GUI App](#gui-app)
  - [Terminal Menu (CUI)](#terminal-menu-cui)
  - [Python API](#python-api)
- [Output Format](#output-format)
- [What Gets Included](#what-gets-included)
- [What Gets Ignored](#what-gets-ignored)
- [Core API Reference](#core-api-reference)
- [License](#license)

---

## Features

- **Directory tree** — generates a visual `├──` tree of your project structure.
- **Tree-only mode** — export only the project directory tree without reading or including file contents, via the `--tree-only` CLI flag or the "Tree only" checkbox in the GUI.
- **Full file content extraction** — reads every supported text file and appends its complete, untruncated contents below the tree.
- **Smart filtering** — skips build outputs, dependency folders, IDE files, and OS noise out of the box.
- **`.gitignore` aware** — loads and respects the project's own `.gitignore` automatically.
- **Three interfaces** — GUI desktop app, interactive terminal menu, and a fully scriptable CLI.
- **Embeddable core** — the `llmscribe.core` package can be imported directly into other Python projects.
- **Cross-platform** — runs on Windows, macOS, and Linux anywhere Python 3.10+ is available.
- **Installable like any real CLI** — `pip install llmscribe` gives you the `llmscribe`, `llmscribe-gui`, and `llmscribe-cui` commands, usable from any terminal.

---

## Project Structure

```
LLMScribe/
├── src/
│   └── llmscribe/             # Installable package (import as `llmscribe.*`)
│       ├── __init__.py        # Package version
│       ├── core/               # All scanning and writing logic
│       │   ├── __init__.py     # Public API surface
│       │   ├── file_reader.py  # Extension allowlist + full file reading
│       │   ├── tree_builder.py # Directory tree + ignore rule engine
│       │   └── writer.py       # Orchestrates tree + contents into output
│       ├── cli/                 # Scriptable command-line interface
│       │   ├── __init__.py
│       │   └── main.py
│       ├── cui/                 # Interactive terminal menu
│       │   ├── __init__.py
│       │   └── main.py
│       └── gui/                 # Tkinter desktop application
│           ├── __init__.py
│           ├── __main__.py      # `python -m llmscribe.gui` entrypoint
│           └── app.py
├── pyproject.toml
├── LICENSE
├── README.md
└── CONTRIBUTING.md
```

---

## Requirements

- **Python 3.10** or higher
- **Tkinter (GUI only)** — required only for `llmscribe-gui`, `llmscribe --gui`, and the GUI picker in the CUI. The core library and non-GUI CLI work without Tkinter. It ships with most Python installers; on Linux it may need to be installed separately:

  ```bash
  # Debian / Ubuntu
  sudo apt install python3-tk

  # Fedora
  sudo dnf install python3-tkinter

  # Arch
  sudo pacman -S tk
  ```

No third-party Python packages are required — the standard library is sufficient.

Headless Linux servers can use the CLI and library integration without Tkinter. If GUI mode is requested without it, LLMScribe prints an installation hint.

---

## Installation

**From PyPI (once published):**

```bash
pip install llmscribe
```

This installs three console commands anywhere on your system: `llmscribe`, `llmscribe-gui`, and `llmscribe-cui`.

**From source (development):**

```bash
git clone https://github.com/AMRITO-KUNDU/LLMScribe.git
cd LLMScribe
pip install -e .
```

`pip install -e .` (editable install) picks up local code changes immediately without reinstalling — use this while developing.

**Publishing to PyPI yourself:**

```bash
pip install build twine
python -m build
twine upload dist/*
```

For automated releases, configure PyPI Trusted Publishing for the GitHub
repository and create a tag such as `v1.0.0`. The workflow in
`.github/workflows/publish.yml` then builds and publishes the wheel and source
distribution without storing a PyPI token in GitHub secrets.

---

## Usage

### CLI

The CLI is designed for scripting, automation, and CI pipelines. All options are passed as flags.

**Basic usage:**

```bash
# Scan a project and write to the default output file
llmscribe --path /path/to/project

# Specify a custom output file
llmscribe --path /path/to/project --output ~/exports/my_project.txt

# Export only the directory tree
llmscribe --path /path/to/project --tree-only

# Open a GUI folder picker instead of typing a path
llmscribe --gui

# Run interactively (prompts for a path, then falls back to the GUI picker)
llmscribe

# Check the installed version
llmscribe --version
llmscribe-cui --version
```

**All flags:**

| Flag | Default | Description |
|---|---|---|
| `--path PATH` | _(none)_ | Path to the project folder to scan. |
| `--output FILE` | `project_overview.txt` | Where to write the output. Parent directories are created automatically. |
| `--tree-only` | `false` | Export only the directory tree and skip file contents. |
| `--gui` | `false` | Open a GUI folder picker dialog instead of reading `--path`. |
| `--version` | — | Print the installed LLMScribe version and exit. |

**Getting help:**

```bash
llmscribe --help
```

---

### GUI App

The desktop app is the easiest way to use LLMScribe. It provides a two-panel layout: controls on the left, a live preview of the generated output on the right.

**Launch:**

```bash
llmscribe-gui
# or
llmscribe --gui
# or, without installing console scripts
python -m llmscribe.gui
```

**Workflow:**

1. Click the folder icon next to **Project Folder** and select your project root, or type the path directly.
2. The **Output File** field auto-populates to `<project>/project_overview.txt`. Change it if needed.
3. Tick **Tree only (skip file contents)** if you just want the directory structure without reading any file contents.
4. Click **Generate**. The preview pane fills with the output and the line count appears in the header.
5. Use **Copy output** to copy the full text to the clipboard, or **Open file** to open the saved file in your system's default text editor.

The GUI runs the scan in a background thread so the window stays responsive on large projects.

---

### Terminal Menu (CUI)

The CUI is an interactive numbered menu intended for terminal users and for embedding LLMScribe into other projects or scripts that call it as a subprocess.

**Launch:**

```bash
llmscribe-cui
```

**Menu:**

```
LLMScribe CUI
1) Enter project folder path
2) Open GUI folder picker
3) Quit
Choose an option [1-3]:
```

You can also pass flags to skip the menu entirely:

```bash
llmscribe-cui --path /path/to/project --output summary.txt
llmscribe-cui --gui --output summary.txt --tree-only
```

---

### Python API

Import LLMScribe's core directly into your own Python scripts or tools.

**Generate a summary string:**

```python
from pathlib import Path
from llmscribe.core.writer import build_project_summary

summary = build_project_summary(
    Path("/path/to/project"),
    tree_only=True,
)
```

**Generate and save to a file:**

```python
from pathlib import Path
from llmscribe.core.writer import run

run(
    project_path=Path("/path/to/project"),
    output_file=Path("summary.txt"),
    tree_only=True,
)
```

**Use individual components:**

```python
from pathlib import Path
from llmscribe.core.tree_builder import DEFAULT_IGNORE, generate_tree, load_gitignore
from llmscribe.core.file_reader import extract_contents
from llmscribe import __version__

project = Path("/path/to/project")
ignore = [*DEFAULT_IGNORE, *load_gitignore(project)]

tree     = generate_tree(project, ignore)
contents = extract_contents(project, ignore)

print(tree)
print(contents)
print(f"Using LLMScribe {__version__}")
```

---

### Tree-only Output

When tree-only mode is used (`--tree-only` on the CLI/CUI, or the checkbox in the GUI), only the project directory structure is exported — no files are opened or read.

```text
my-project/
├── src/
│   ├── main.py
│   └── utils.py
├── tests/
└── README.md
```

---

## Output Format

The output is a plain UTF-8 text file with two sections:

```
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

... (and so on for every included file)
```

Files are listed in sorted order, and each file's contents are included in full — nothing is cut off or truncated.

---

## What Gets Included

LLMScribe reads files with the following extensions:

| Category | Extensions |
|---|---|
| Python | `.py` |
| JavaScript / TypeScript | `.js` `.ts` `.jsx` `.tsx` |
| Systems languages | `.c` `.cpp` `.cc` `.cxx` `.h` `.hpp` `.rs` `.go` `.zig` |
| JVM languages | `.java` `.scala` `.kt` `.clj` `.cljs` |
| Other languages | `.rb` `.php` `.swift` `.dart` `.lua` `.pl` `.r` `.hs` `.ml` `.fs` `.vb` `.cs` `.ex` `.exs` `.nim` `.cr` `.d` `.elm` `.v` |
| Web | `.html` `.htm` `.css` `.scss` `.sass` `.less` `.vue` `.svelte` `.pug` `.ejs` `.hbs` `.mustache` `.twig` `.jsp` `.asp` `.aspx` `.erb` `.haml` |
| Config & manifests | `.json` `.xml` `.yaml` `.yml` `.toml` `.ini` `.cfg` `.conf` `.properties` `.env` `.dotenv` `.lock` `.sum` `.mod` `.gradle` `.pom` `.gitignore` `.gitattributes` `.editorconfig` `.prettierrc` `.eslintrc` `.babelrc` |
| Shell & scripts | `.sh` `.bash` `.zsh` `.fish` `.ps1` `.bat` `.cmd` `.awk` `.sed` |
| Documentation | `.md` `.rst` `.adoc` `.tex` `.bib` `.txt` |
| Data (text-based) | `.csv` `.tsv` `.sql` |
| Logs | `.log` |

Binary formats (`.pdf`, `.docx`, `.epub`, `.db`, `.sqlite`, `.parquet`, images, etc.) are intentionally excluded — they cannot be read as text.

---

## What Gets Ignored

The following are skipped automatically regardless of the project being scanned:

**Directories:**

| Category | Names |
|---|---|
| Version control | `.git` `.svn` `.hg` |
| Dependencies | `node_modules` `vendor` `packages` |
| Python envs | `venv` `__pycache__` `.eggs` `*.egg-info` |
| Build outputs | `dist` `build` `target` `out` `bin` `obj` |
| IDEs | `.idea` `.vscode` `.vs` |
| OS artifacts | `.DS_Store` `Thumbs.db` `desktop.ini` |
| Logs & temp | `logs` `tmp` `temp` `.tmp` `.cache` |
| Test coverage | `.coverage` `coverage` `.nyc_output` |
| Secrets | `.env` `.env.*` `secrets` |

**Additionally:** any pattern present in the project's `.gitignore` file is loaded and applied on top of the defaults above.

---

## Core API Reference

### `llmscribe.core.writer`

#### build_project_summary(project_path, tree_only=False) → str

Builds and returns the complete summary string for a project.

| Parameter | Type | Description |
|---|---|---|
| `project_path` | `Path` | Resolved path to the project root. |
| `tree_only` | `bool` | Export only the directory tree, skipping file contents. |

#### run(project_path, output_file, tree_only=False) → None

Generates the summary and writes it to `output_file`. Prints progress and the final line count to stdout. Creates parent directories of `output_file` if they do not exist.

---

### `llmscribe.core.file_reader`

#### `extract_contents(root, ignore_patterns) → str`

Walks `root` recursively, reads every file whose extension is in `TEXT_FILE_EXTENSIONS` and which does not match `ignore_patterns`, and returns all contents concatenated with `--- relative/path ---` headers. Files are read in full.

#### `is_text_file(path) → bool`

Returns `True` if `path.suffix.lower()` is in `TEXT_FILE_EXTENSIONS`.

---

### `llmscribe.core.tree_builder`

#### `generate_tree(root, ignore_patterns) → str`

Returns a multi-line string representing the directory tree rooted at `root`, skipping anything that matches `ignore_patterns`.

#### `load_gitignore(root) → list[str]`

Parses `root/.gitignore` and returns ordered non-comment, non-empty pattern strings. Common Git-style globs, anchored rules, and negation rules are supported. Returns an empty list if no `.gitignore` exists.

#### `should_ignore(path, ignore_patterns) → bool`

Returns `True` if `path` matches the supplied ignore rules.

---

## License

LLMScribe is licensed under the [Apache License 2.0](LICENSE).

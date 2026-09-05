# LLMScribe

**Turn any project folder into one clean text file that AI tools can read.**

LLMScribe walks a project, builds a directory tree, and dumps the full contents of every source file into a single `.txt` file.  
Perfect for pasting into ChatGPT, Claude, Grok, Cursor, or any other AI coding assistant.

No configuration needed. Works on Windows, macOS, and Linux.

---

## Install

You need Python 3.10 or newer.

```bash
pip install llmscribe
```

That’s it. Three commands are now available on your system:

| Command          | What it is                          |
|------------------|-------------------------------------|
| `llmscribe`      | Normal command-line tool            |
| `llmscribe-gui`  | Desktop window (graphical app)      |
| `llmscribe-cui`  | Simple text menu in the terminal    |

---

## How to use it on your computer

### 1. Desktop app (easiest – recommended for most people)

Open a terminal (or Command Prompt / PowerShell on Windows) and type:

```bash
llmscribe-gui
```

A window will appear.

1. Click the folder icon and choose the project folder you want to export.
2. (Optional) Change the output file name.
3. (Optional) Tick **Tree only** if you only want the folder structure.
4. Click **Generate**.
5. When it finishes you can **Copy** the text or **Open** the saved file.

You can also start the same window with:

```bash
llmscribe --gui
```

or

```bash
python -m llmscribe.gui
```

---

### 2. Command line (fastest once you know the path)

Open a terminal in the folder that contains your project (or use a full path).

**Most common usage:**

```bash
llmscribe --path /path/to/your/project
```

This creates a file called `project_overview.txt` in the current folder.

**Useful variations:**

```bash
# Save to a specific place
llmscribe --path ~/Documents/my-app --output ~/Desktop/my-app.txt

# Only the folder tree (no file contents)
llmscribe --path ~/Documents/my-app --tree-only

# Let a folder picker appear instead of typing the path
llmscribe --gui
```

---

### 3. Interactive text menu

If you prefer a simple numbered menu:

```bash
llmscribe-cui
```

You will see:

```
LLMScribe CUI
1) Enter project folder path
2) Open GUI folder picker
3) Quit
Choose an option [1-3]:
```

Type `1` and press Enter, then paste or type the path to your project.  
Or type `2` to open the same graphical folder picker used by the desktop app.

---

## What the output looks like

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
def hello():
    print("Hello world")

--- src/utils.py ---
...
```

You can paste this whole file straight into an AI chat.

---

## Common questions

**“I don’t have a terminal / I don’t know how to open one”**  
- **Windows**: Press `Win + R`, type `cmd` or `powershell`, press Enter.  
- **macOS**: Press `Cmd + Space`, type `Terminal`, press Enter.  
- **Linux**: Press `Ctrl + Alt + T` (most distributions).

**“The GUI doesn’t open / complains about Tkinter”**  
On some Linux systems you need to install the system package first:

```bash
# Ubuntu / Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

The normal command-line mode (`llmscribe --path ...`) works even without Tkinter.

**“Where does the file get saved?”**  
By default it is saved as `project_overview.txt` in the folder where you ran the command.  
Use `--output` to put it anywhere you like.

---

## Advanced usage (for developers)

### Use it from Python code

```python
from pathlib import Path
from llmscribe.core.writer import run, build_project_summary

# Write a file
run(
    project_path=Path("/path/to/project"),
    output_file=Path("summary.txt"),
    tree_only=False,
)

# Or just get the text
text = build_project_summary(Path("/path/to/project"))
```

### Install from source

```bash
git clone https://github.com/AMRITO-KUNDU/llmscribe.git
cd llmscribe
pip install -e .
```

---

## What files are included / ignored

**Included** – any file with a common source or text extension  
(`.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.java`, `.go`, `.rs`, `.md`, `.json`, `.yaml`, `.toml`, `.html`, `.css`, `.sh`, … and many more).

**Ignored automatically**  
- `.git`, `node_modules`, `venv`, `__pycache__`, `dist`, `build`  
- IDE folders (`.idea`, `.vscode`)  
- OS junk (`.DS_Store`, `Thumbs.db`)  
- Anything listed in the project’s own `.gitignore`

---

## License

Apache License 2.0 – see [LICENSE](LICENSE).

---

Made for people who just want to give their whole project to an AI without fighting with copy-paste.

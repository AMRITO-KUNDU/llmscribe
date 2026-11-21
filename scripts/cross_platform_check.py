#!/usr/bin/env python3
"""Prove that LLMScribe returns identical output on Linux, macOS and Windows.

Builds a fixed fixture project, runs the read-only operations over it, strips the
one thing that legitimately differs between machines (the absolute temp path), and
prints a digest per operation.

CI runs this on all three operating systems and diffs the resulting files. If they
match, "same output everywhere" is a demonstrated fact rather than a claim.

    python scripts/cross_platform_check.py            # print the digests
    python scripts/cross_platform_check.py --out f.txt
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

from llmscribe import Repository, __version__

# Written as bytes, never as text: Path.write_text would translate \n to \r\n on
# Windows and the fixture itself would stop being identical across platforms.
FIXTURE: dict[str, bytes] = {
    "README.md": b"# demo\n",
    ".gitignore": b"*.log\n",
    "src/main.py": b"from src.util import helper\n\n\ndef main():\n    return helper()\n",
    "src/util.py": b"def helper():\n    return 'auth'\n",
    "src/nested/deep.py": b"x = 1\n",
    "tests/test_main.py": b"from src.main import main\n",
    "unicode.md": "# caf\u00e9 \u4e2d\u6587 \U0001f680\n".encode(),
    "ignored.log": b"this file is gitignored and must not appear\n",
}


def build_fixture(base: Path) -> Path:
    """Create the project under a FIXED directory name.

    The tree's first line is the directory name, so a random temp name would make
    every machine's output differ for no interesting reason.
    """
    root = base / "my-project"
    for rel, data in FIXTURE.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


# Fields that legitimately differ per machine or per run. ``modified`` is the file's
# mtime: the fixture is written fresh on every runner, so the value can never match.
VOLATILE_KEYS = {"modified"}


def scrub(value: Any, root: Path) -> Any:
    """Replace machine-specific values so only real differences remain."""
    if isinstance(value, str):
        forms = {
            str(root),
            root.as_posix(),
            str(root).replace("\\", "/"),
            str(root.resolve()),
            root.resolve().as_posix(),
        }
        # longest first, so a prefix cannot be replaced before the full path
        for form in sorted(forms, key=len, reverse=True):
            value = value.replace(form, "<ROOT>")
        return value
    if isinstance(value, list):
        return [scrub(item, root) for item in value]
    if isinstance(value, dict):
        return {
            key: ("<VOLATILE>" if key in VOLATILE_KEYS and item else scrub(item, root))
            for key, item in value.items()
        }
    return value


def digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main(argv: list[str]) -> int:
    # Resolve first. On macOS /var is a symlink to /private/var, so the tool reports a
    # different absolute path than mkdtemp handed out and the scrub below would miss it.
    base = Path(tempfile.mkdtemp(prefix="llmscribe-xplat-")).resolve()
    try:
        root = build_fixture(base)
        repo = Repository(root)

        results = {
            "map": repo.map().to_dict(),
            "map_depth2": repo.map(max_depth=2).to_dict(),
            "overview": repo.overview().to_dict(),
            "overview_compressed": repo.overview(compress=True).to_dict(),
            "search": repo.search("auth").to_dict(),
            "read": repo.read("src/main.py").to_dict(),
            "read_many": repo.read_many(["README.md", "src/util.py"]).to_dict(),
            "dependencies": repo.dependencies("src/main.py").to_dict(),
        }

        lines = [f"llmscribe {__version__}", f"python {sys.version_info.major}.{sys.version_info.minor}"]
        per_op = {name: digest(scrub(payload, root)) for name, payload in results.items()}
        lines += [f"{name:14} {value}" for name, value in per_op.items()]
        lines.append(f"{'combined':14} {digest(per_op)}")
        report = "\n".join(lines) + "\n"

        if "--out" in argv:
            # newline="\n" matters: on Windows write_text would emit CRLF and every
            # line of the report would differ from the other runners by one byte.
            Path(argv[argv.index("--out") + 1]).write_text(report, encoding="utf-8", newline="\n")
        print(report, end="")
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

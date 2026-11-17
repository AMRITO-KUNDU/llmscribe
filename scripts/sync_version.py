#!/usr/bin/env python3
"""Propagate the single version source to every file that repeats it.

The version is defined once, in ``src/llmscribe/__init__.py``::

    __version__ = "1.4.0"

``pyproject.toml`` already reads that dynamically (``dynamic = ["version"]``), so the
package metadata follows automatically. The remaining files cannot: they are JSON,
TypeScript and plain text, read by tools that never import Python. This script writes
the same value into them.

    python scripts/sync_version.py           # write the value everywhere
    python scripts/sync_version.py --check   # exit 1 if anything has drifted

CI runs the ``--check`` form, so a version bump that misses a file fails the build
instead of shipping inconsistent metadata.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "llmscribe" / "__init__.py"

VERSION_RE = re.compile(r'(?m)^__version__\s*=\s*"([^"]+)"')

# (path, pattern) — group 2 is the version, groups 1 and 3 are preserved verbatim.
# Each pattern is deliberately narrow: site.ts also contains "version" inside code
# samples, and those must not be rewritten.
TARGETS: list[tuple[Path, re.Pattern[str]]] = [
    (ROOT / "server.json", re.compile(r'("version":\s*")([^"]+)(")')),
    (ROOT / "docs" / "public" / "llms.txt", re.compile(r"(?m)^(- Latest version:\s*)(\S+)(\s*)$")),
    (ROOT / "docs" / "src" / "lib" / "site.ts", re.compile(r'(?m)^(  version:\s*")([^"]+)(")')),
    (ROOT / "docs" / "src" / "routes" / "__root.tsx", re.compile(r'(?m)^(  softwareVersion:\s*")([^"]+)(")')),
]


def current_version() -> str:
    """Read ``__version__`` without importing the package (avoids loading core)."""
    match = VERSION_RE.search(SOURCE.read_text(encoding="utf-8"))
    if not match:
        raise SystemExit(f"no __version__ assignment found in {SOURCE.relative_to(ROOT)}")
    return match.group(1)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    version = current_version()
    drift: list[str] = []
    unfound: list[str] = []

    for path, pattern in TARGETS:
        rel = path.relative_to(ROOT)
        if not path.exists():
            unfound.append(f"{rel} (missing)")
            continue

        text = path.read_text(encoding="utf-8")
        matches = pattern.findall(text)
        if not matches:
            unfound.append(str(rel))
            continue

        if check:
            drift.extend(f"{rel}: has {hit[1]}, expected {version}" for hit in matches if hit[1] != version)
            continue

        path.write_text(pattern.sub(lambda m: m.group(1) + version + m.group(3), text), encoding="utf-8")
        print(f"  {rel}: wrote {version} ({len(matches)} occurrence(s))")

    if unfound:
        print("could not find the version field in:", file=sys.stderr)
        for item in unfound:
            print(f"  {item}", file=sys.stderr)
        return 2

    if check:
        if drift:
            print(f"version drift (source of truth is {version}):", file=sys.stderr)
            for line in drift:
                print(f"  {line}", file=sys.stderr)
            print("\nfix with: python scripts/sync_version.py", file=sys.stderr)
            return 1
        print(f"all {len(TARGETS)} targets match {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

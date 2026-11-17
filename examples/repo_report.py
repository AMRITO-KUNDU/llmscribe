"""A one-screen summary of a repository.

    python examples/repo_report.py path/to/project

File and directory counts, plus the most-imported modules - a quick way to find the
centre of gravity in an unfamiliar codebase before you read anything.
"""

from __future__ import annotations

import sys
from collections import Counter

from llmscribe import LLMScribeError, Repository

MAX_ANALYSED = 400  # dependency analysis runs per file; keep it bounded


def main(root: str) -> int:
    repo = Repository(root)
    tree = repo.map()

    dirs = {f.rsplit("/", 1)[0] for f in tree.files if "/" in f}
    print(f"root    {repo.root}")
    print(f"files   {tree.file_count}")
    print(f"dirs    {len(dirs)}")

    counts: Counter[str] = Counter()
    analysed = 0
    for path in tree.files:
        if not path.endswith(".py") or analysed >= MAX_ANALYSED:
            continue
        analysed += 1
        try:
            deps = repo.dependencies(path)
        except LLMScribeError:
            continue
        for target in deps.file_dependencies.local_dependencies:
            counts[target] += 1

    if counts:
        print(f"\nmost imported (from {analysed} python file(s)):")
        for path, n in counts.most_common(10):
            print(f"  {n:3}x  {path}")
    else:
        print("\nno local imports found")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))

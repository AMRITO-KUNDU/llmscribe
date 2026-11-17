"""Show what a change touches, before you review it.

    python examples/pr_review.py                # working tree
    python examples/pr_review.py --staged       # staged only
    python examples/pr_review.py --commit HEAD~1

Prints the changed files, then for each one the files that import it. Those are the
places most likely to break, and the places a reviewer usually forgets to look.
"""

from __future__ import annotations

import sys

from llmscribe import LLMScribeError, Repository


def main(argv: list[str]) -> int:
    staged = "--staged" in argv
    commit = argv[argv.index("--commit") + 1] if "--commit" in argv else None

    repo = Repository(".")

    try:
        diff = repo.diff(staged=staged, commit=commit)
    except LLMScribeError as err:
        print(f"cannot diff this directory: [{err.code}] {err.message}", file=sys.stderr)
        return 1

    changed = diff.changed_files
    print(f"{len(changed)} changed file(s)")

    for path in changed:
        print(f"\n  {path}")
        try:
            deps = repo.dependencies(path)
        except LLMScribeError:
            print("    (not analysable - binary, missing, or not a source file)")
            continue

        used_by = deps.used_by
        if used_by:
            print(f"    imported by {len(used_by)}:")
            for other in used_by[:8]:
                print(f"      {other}")
            if len(used_by) > 8:
                print(f"      ... and {len(used_by) - 8} more")
        else:
            print("    imported by: nothing")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

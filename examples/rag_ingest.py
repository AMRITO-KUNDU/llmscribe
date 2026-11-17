"""Turn a repository into chunks you can embed.

    python examples/rag_ingest.py path/to/project > chunks.jsonl

One JSON object per line: ``{"path": ..., "chunk": ...}``. Feed the lines to whatever
embedder you use. LLMScribe does not embed anything itself - this just gets your code
into the shape an embedding pipeline wants, with the file path kept as metadata so a
retrieved chunk can point back at the file it came from.
"""

from __future__ import annotations

import json
import sys

from llmscribe import Repository

CHUNK_CHARS = 4000
KEEP = (".py", ".md", ".ts", ".tsx", ".js", ".go", ".rs", ".java", ".rb", ".sql",
        ".toml", ".yaml", ".yml", ".css", ".html")


def main(root: str) -> int:
    repo = Repository(root)

    wanted = [f for f in repo.map().files if f.endswith(KEEP)]
    if not wanted:
        print("no matching files", file=sys.stderr)
        return 1

    # read_many reports per-file failures instead of raising, so one unreadable
    # file cannot take the whole run down.
    batch = repo.read_many(wanted)

    for result in batch.results:
        if not result.ok:
            print(json.dumps({"path": result.file_path, "error": result.error_code}), file=sys.stderr)
            continue
        text = result.content
        for start in range(0, len(text), CHUNK_CHARS):
            print(json.dumps({"path": result.file_path, "chunk": text[start : start + CHUNK_CHARS]}))

    print(
        f"{batch.success_count}/{batch.file_count} files, {batch.error_count} error(s)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
    except BrokenPipeError:
        # piped into `head` and the reader went away; that is not an error
        raise SystemExit(0) from None

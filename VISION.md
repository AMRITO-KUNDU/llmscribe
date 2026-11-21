# Vision

LLMScribe exists to be **the filesystem layer AI agents are missing** — and nothing else.

## The problem it solves

An agent that wants to look at code has exactly one interface: the shell. `ls`, `find`,
`grep`, `cat`, `dir`, `Select-String`. Those commands were designed for a human reading
a terminal. They print columns and colour, they sort differently by locale, they report
errors on the same stream as results, and they are not the same commands on Linux, macOS
and Windows.

So the agent spends its budget re-parsing text, and what it learns on your laptop does
not transfer to CI or to a contributor's Windows machine.

LLMScribe replaces that with one structured interface: a directory tree, a literal
search that reports what it found, a dependency graph, a safe file reader, and a Git
diff. Same seven operations, same JSON, same bytes, on every OS.

The same input always produces the same bytes. That is the whole point — an agent can
rely on it, and a human can audit it.

## What is in scope

- Repeatable extraction: trees, file contents, search, dependencies, diffs.
- Masking secrets in everything it returns, by default.
- A local-first design: your code is read from disk and never uploaded.
- One core with several surfaces: CLI, MCP server, desktop GUI, Python API.
- Doing a few things precisely, with explicit limits and stable error codes.
- Documentation that makes the behaviour predictable.

## What is explicitly out of scope

These come up often. They are not "not yet" — they are decisions:

- **AI features of any kind.** No summaries, no generated answers, no "explain this
  file". LLMScribe supplies context; the model supplies the intelligence.
- **Embeddings, semantic search, or relevance ranking.** Ranking is a guess, and a
  guess is not reproducible. Search here is exact and ordered.
- **A hosted service or any network call.** No accounts, no telemetry, no cloud
  fetching of repositories.
- **Autonomous coding.** LLMScribe is not an agent and does not edit your code.
- **Being a general Git client.** `project_diff` reports status and diffs; it is not
  a replacement for `git`.
- **Multi-repository or monorepo-wide orchestration.** One project directory per call.

## Secrets are masked by default

LLMScribe's job is to put code in front of a model, which makes it the last place a
credential should pass unmasked. A hardcoded key in `src/config.py` would otherwise
travel to whatever provider the agent is talking to.

So redaction is **on by default** on every surface, including the MCP server. There is a
`--no-redact` escape hatch on the CLI and `redact=False` in the Python API, but an agent
cannot turn it off: a model that can see raw secrets will eventually read one.

Matching is deliberately conservative — high-confidence token shapes only, each with a
fixed replacement, so the output stays repeatable and ordinary code is not mangled. When
something is masked the result says so, in `metadata.redacted`. Silence would be
indistinguishable from "no secrets here".

## Budgets are spent in a fixed order

`--max-tokens` fills a context budget by taking files in **path order** until the budget
is gone. That is the only acceptable rule: the moment files are chosen by relevance,
likelihood or "importance", the tool is ranking, and ranking is what this project exists
to avoid.

The consequence is that a budget may cut off a file that mattered. That is a known and
accepted cost — a predictable wrong answer beats an unpredictable right one, because the
caller can always raise the budget or read a specific file.

Token counts are estimated at four characters each. An exact count needs a
model-specific vocabulary, and adding one would make the same file cost different
amounts depending on which model you meant.

## How a proposal is judged

A feature request is evaluated against four questions:

1. Does it stay repeatable — same input, same output?
2. Does it work entirely locally?
3. Does it remove a step the agent or user would otherwise do by hand?
4. Can it be expressed with the existing limits and error model, without a new concept?

A "no" to any of the first three usually means no. The fourth is negotiable.

Proposals that fail these tests are still welcome — they often point at a real problem
that has a smaller, in-scope answer. Say what you are trying to achieve, not only the
shape of the solution you have in mind.

# Vision

LLMScribe exists to give AI coding agents **structured, deterministic access to a
codebase** — and nothing else.

## The problem it solves

An agent's bottleneck is usually not reasoning, it's retrieval. Faced with a large
project it guesses which files matter, re-reads the same ones, and burns context on
build output and stale fixtures. LLMScribe replaces that guesswork with a small set
of tools whose output is predictable: a directory tree, a search that reports what it
found, a dependency graph, a safe file reader, and a Git diff.

The same input always produces the same bytes. That is the whole point — an agent can
rely on it, and a human can audit it.

## What is in scope

- Deterministic extraction: trees, file contents, search, dependencies, diffs.
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

## How a proposal is judged

A feature request is evaluated against four questions:

1. Does it stay deterministic — same input, same output?
2. Does it work entirely locally?
3. Does it remove a step the agent or user would otherwise do by hand?
4. Can it be expressed with the existing limits and error model, without a new concept?

A "no" to any of the first three usually means no. The fourth is negotiable.

Proposals that fail these tests are still welcome — they often point at a real problem
that has a smaller, in-scope answer. Say what you are trying to achieve, not only the
shape of the solution you have in mind.

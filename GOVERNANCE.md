# Governance

This document describes who decides what in LLMScribe, and how that can change.

## Current model

LLMScribe is a **single-maintainer project** (a "benevolent dictator" model, in the
usual open source sense). One person has final say on direction, scope and releases.

That is not a claim about the value of other people's work — it is an honest
description of who is accountable. It keeps decisions fast while the project is small,
and it makes the answer to "who do I ask?" unambiguous.

## Roles

**User** — anyone who runs LLMScribe.

**Contributor** — anyone who opens an issue, reviews a pull request, improves docs, or
gets a pull request merged. No application, no ceremony.

**Maintainer** — currently [@AMRITO-KUNDU](https://github.com/AMRITO-KUNDU).
Responsible for scope, code review, releases, security reports and conduct.

## How decisions are made

- **Small changes** (bug fixes, docs, tests, refactors that don't change behaviour):
  decided in the pull request. If CI is green and it doesn't contradict
  [VISION.md](VISION.md), expect a merge.
- **Behaviour changes** (new tool, new argument, changed output): discussed in an
  issue first. The maintainer decides, with reasons recorded in the issue.
- **Scope changes**: measured against [VISION.md](VISION.md). If a proposal doesn't
  fit, the answer comes with a pointer to which criterion it failed.
- **Disagreements**: argued on the merits in public. Being the maintainer is a tiebreak,
  not an argument.

Discussion happens in issues and pull requests, in public, by default. If a decision is
made somewhere private, the reasoning is written back into the relevant issue.

## Maintainer availability and boundaries

This is a part-time, unpaid project. To keep it sustainable — and to make the answer
predictable rather than personal — here is what to expect:

- **Response window:** about 7 days for a first reply. Silence is not rejection; ping the thread.
- **Not offered:** paid support, consulting, private debugging of your project, or a
  guaranteed date for any fix.
- **What gets prioritised:** security and correctness first, then work that fits
  [VISION.md](VISION.md), then everything else.
- **Saying no is normal.** A closed issue or an unmerged pull request is a decision about
  scope or timing, not a judgement of the work.

If the project grows past what one person can carry, this section changes first — before
anything else does.

## Releases

- [Semantic Versioning](https://semver.org/). Breaking changes bump the major version.
- The version lives in exactly one place: `src/llmscribe/__init__.py`.
- Every release is tagged, published to PyPI, and recorded in [CHANGELOG.md](CHANGELOG.md).
- Maintainers cut releases; contributors do not bump versions in pull requests.

## Becoming a maintainer

There is no formal ladder, because there is currently one maintainer and no queue of
candidates. In practice, a maintainer would be someone who has:

1. contributed several merged changes across more than one area,
2. shown they understand the scope in [VISION.md](VISION.md) — including saying no,
3. reviewed other people's work constructively,
4. and wants the responsibility, not just the title.

If you are doing that work, say so in an issue. The first step would be review rights
on pull requests, not commit access.

## Changing this document

Governance changes go through a pull request to this file, with the reasoning in the
description. The maintainer merges it, as with any other change.

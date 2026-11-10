# Accessibility

LLMScribe is a developer tool, but that is not an excuse for it to be unusable.
This page describes what the project does today, where it falls short, and how
to report a barrier you hit.

## Commitment

Accessibility issues are treated as bugs, not feature requests. If something is
unusable with a screen reader, keyboard only, or at high zoom, please report it
using the channels below.

## What the project does today

**Website** (`docs/`)

- Semantic landmarks: the primary and mobile navigation are `<nav>` elements with
  accessible names, and the logo links are labelled.
- A skip-to-content link is the first focusable element on the page.
- Decorative SVGs are hidden from assistive technology (`aria-hidden`), so they
  are not announced as noise.
- Visible focus rings on buttons and tabs (`focus-visible`), rather than relying
  on colour alone.
- The animated terminal mock honours `prefers-reduced-motion: reduce`.
- Text is checked against WCAG AA contrast (4.5:1) — including the social card.

**CLI** (`llmscribe`)

- Output is plain text with no ANSI colour codes, so it reads cleanly with a
  screen reader and pipes predictably.
- No meaning is carried by colour alone: results and errors are labelled in words,
  and every failure carries a stable, machine-readable error code.

**MCP server** (`llmscribe-mcp`)

- All output is text (Markdown or JSON). Truncation is reported explicitly
  (`truncated`, `truncation_note`, `omitted_files`) rather than silently applied.

## Known limitations

- **The desktop GUI is the weakest surface.** It is built on Tkinter and
  CustomTkinter, which expose a limited accessibility tree on most platforms.
  Screen-reader support for its custom-drawn widgets is **not verified**, and it
  has not been tested with a screen reader. Keyboard navigation works for standard
  controls but has not been audited end to end.
- **No formal audit has been run.** Nothing here has been tested against WCAG 2.2
  AA as a whole, or with NVDA, JAWS, VoiceOver or TalkBack.
- **The website has not been tested at 200% zoom or 400% reflow** on small
  viewports.
- **Documentation is English-only.** LLMScribe handles non-ASCII file contents,
  but the interface and docs are not localised.

Where a limitation is listed above, treat it as unverified rather than working.

## Reporting a barrier

Open an issue using the [bug report form](https://github.com/AMRITO-KUNDU/llmscribe/issues/new/choose)
and add `accessibility` to the title. Please include:

- the surface (website, CLI, MCP server, or GUI),
- the assistive technology and version, if any,
- what you expected to happen, and what happened instead.

If the barrier is also a security concern, follow [SECURITY.md](SECURITY.md)
instead of opening a public issue.

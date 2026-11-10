# Accessibility

LLMScribe is a developer tool, but that is not an excuse for it to be unusable.
This page states what the project aims for, what it does today, where it falls short,
and how to report a barrier.

## Commitment

Accessibility issues are treated as bugs, not feature requests. If something is unusable
with a screen reader, keyboard only, or at high zoom, please report it — see
[Reporting a barrier](#reporting-a-barrier).

## Goals

- **Target:** [WCAG 2.2 AA](https://www.w3.org/TR/WCAG22/) for the website, where it is
  feasible for a static documentation-style site.
- **Priority 1 — keyboard:** every interactive element on the website is reachable and
  operable with the keyboard alone, with a visible focus indicator.
- **Priority 2 — screen readers:** interactive elements expose an accessible name and
  role, and decorative images are hidden from assistive technology.
- **Priority 3 — contrast and zoom:** text meets a 4.5:1 contrast ratio, and the layout
  reflows without loss of content at 200% zoom.
- **CLI and MCP output:** plain text, no colour-only meaning, so it works with a screen
  reader and pipes predictably.

These are targets, not certified results. Nothing here has been formally audited.

## Supported environments

| Surface | Environment | Status |
|---|---|---|
| Website | Current Chrome, Firefox, Safari, Edge | Supported |
| Website | Mobile browsers, narrow viewports | Supported, untested at 400% reflow |
| CLI | Any POSIX terminal, Windows Terminal | Supported — plain text output |
| MCP server | Any MCP client over stdio | Supported — text or JSON output |
| Desktop GUI | Windows (primary), macOS, Linux | **Partial** — see limitations |

## What the project does today

**Website** (`docs/`)

- Semantic landmarks: primary and mobile navigation are `<nav>` elements with accessible
  names, and the logo links are labelled.
- A skip-to-content link is the first focusable element on the page.
- Decorative SVGs are hidden from assistive technology (`aria-hidden`).
- Visible focus rings on buttons and tabs (`focus-visible`), rather than relying on
  colour alone.
- The animated terminal mock honours `prefers-reduced-motion: reduce`.
- Text colours are checked against WCAG AA (4.5:1) — including the social preview card.

**CLI** (`llmscribe`)

- Output is plain text with no ANSI colour codes.
- No meaning is carried by colour alone: results and errors are labelled in words, and
  every failure carries a stable, machine-readable error code.

**MCP server** (`llmscribe-mcp`)

- All output is text (Markdown or JSON). Truncation is reported explicitly
  (`truncated`, `truncation_note`, `omitted_files`) rather than silently applied.

## Known limitations

- **The desktop GUI is the weakest surface.** It is built on Tkinter and CustomTkinter,
  which expose a limited accessibility tree on most platforms. Screen-reader support for
  its custom-drawn widgets is **not verified** and has not been tested with a screen
  reader. Keyboard navigation works for standard controls but has not been audited end
  to end.
- **No formal audit has been run.** Nothing here has been tested against WCAG 2.2 AA as a
  whole, or with NVDA, JAWS, VoiceOver or TalkBack.
- **The website has not been tested at 200% zoom or 400% reflow** on small viewports.
- **Documentation is English-only.** LLMScribe handles non-ASCII file contents, but the
  interface and docs are not localised.

Where a limitation is listed above, treat it as unverified rather than working.

## Contributor requirements

For any change that touches the website or the GUI:

- **Keyboard test:** operate the changed component with the keyboard only, before opening
  the pull request.
- **Names and roles:** interactive elements need an accessible name; decorative images
  need `aria-hidden` or empty `alt`.
- **Colour:** never convey meaning by colour alone, and keep text at 4.5:1 or better.
- **Motion:** new animation must respect `prefers-reduced-motion`.
- **Docs:** mention any new known limitation on this page.

These are review criteria, not an automated gate — there is no accessibility linter in CI
yet.

## Reporting a barrier

Open an [accessibility issue](https://github.com/AMRITO-KUNDU/llmscribe/issues/new?template=accessibility.yml).
The template asks for the surface, the assistive technology and version, and whether you
found a workaround — the details that a general bug report doesn't prompt for.

If the barrier is also a security concern, follow [SECURITY.md](SECURITY.md) instead of
opening a public issue.

# Security Policy

## Reporting a Vulnerability

If you find a security issue, please do not open a public issue. Contact the maintainer privately with a description, reproduction steps and the potential impact.

## What LLMScribe enforces

- **Paths:** absolute paths, `..` segments (also percent-encoded or backslash forms), NUL bytes and symlinks are rejected; reads stay inside the project root.
- **GitHub input:** `owner/repo`, github.com URLs and SSH URLs are validated; refs are restricted to safe characters.
- **Archives:** extracted in memory only; members with unsafe paths or symlinks are skipped; entry count, uncompressed size and per-file size are bounded.
- **HTTP to GitHub:** HTTPS only, timeouts, bounded responses, redirects limited to GitHub hosts; the token is sent only to `api.github.com` and is redacted from all output.
- **Subprocesses:** `git` only, argument lists (no shell), timeout, minimal environment, bounded output, no external diff/textconv drivers.
- **Hosted MCP:** Host/Origin validation on `/mcp`, request-size limit, and local `path` access disabled by default over HTTP.

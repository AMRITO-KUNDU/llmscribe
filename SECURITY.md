# Security Policy

## Reporting a Vulnerability

If you find a security issue, please do not open a public issue. Contact the maintainer privately with a description, reproduction steps and the potential impact.

## What LLMScribe enforces

- **Local only:** LLMScribe never sends your code anywhere. It makes no network requests and has no hosted component, so there is nothing to leak.
- **Paths:** absolute paths, `..` segments (also percent-encoded or backslash forms), NUL bytes and symlinks are rejected; reads stay inside the project root.
- **Files:** binary files and files over the size limit are refused; every failure returns a stable, machine-readable error code instead of a traceback.
- **Subprocesses:** `git` only, argument lists (no shell), a timeout, a minimal environment, bounded output, and no external diff/textconv drivers.
- **Local access policy:** every local path is allowed by default; `MCP_ALLOWED_ROOTS` restricts access to specific directories, and `MCP_ALLOW_LOCAL_PATHS=0` disables local paths entirely.

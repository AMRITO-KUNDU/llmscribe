# Security Policy

## Reporting a Vulnerability

If you find a security issue, please do not open a public issue.

Use GitHub's private vulnerability reporting on this repository (**Security → Report a vulnerability**), which opens a private advisory visible only to the maintainer. If you cannot use it, contact the maintainer directly via GitHub ([@AMRITO-KUNDU](https://github.com/AMRITO-KUNDU)) or the email address on that profile.

Please include a description, reproduction steps, affected versions, and the potential impact. Expect an acknowledgement within about 7 days.

## Supported versions

Security fixes land on the latest released minor version. Please reproduce on the newest PyPI release (`pip install -U llmscribe`) before reporting.

## What LLMScribe enforces

- **Local only:** LLMScribe never sends your code anywhere. It makes no network requests and has no hosted component, so there is nothing to leak.
- **Paths:** absolute paths, `..` segments (also percent-encoded or backslash forms), NUL bytes and symlinks are rejected; reads stay inside the project root.
- **Files:** binary files and files over the size limit are refused; every failure returns a stable, machine-readable error code instead of a traceback.
- **Subprocesses:** `git` only, argument lists (no shell), a timeout, a minimal environment, bounded output, and no external diff/textconv drivers.
- **Dependencies:** kept current by Dependabot, and scanned by CodeQL (`security-and-quality`) on every push and pull request to `main`.
- **Local access policy:** every local path is allowed by default; `MCP_ALLOWED_ROOTS` restricts access to specific directories, and `MCP_ALLOW_LOCAL_PATHS=0` disables local paths entirely.

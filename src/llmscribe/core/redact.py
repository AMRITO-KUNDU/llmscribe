"""Mask secrets before they reach a model.

LLMScribe's job is to put your code in front of a model. That makes it the last place a
credential should pass through unmasked — a hardcoded key in ``src/config.py`` would
otherwise travel to whatever provider the agent is talking to.

Only **high-confidence** patterns are matched, each with a fixed replacement, so the
output stays deterministic: the same file always produces the same masked text.

Redaction is reported, never silent. Every result says how many kinds were masked, so a
reader can tell "no secrets here" from "we took them out".
"""

from __future__ import annotations

import re

# (kind, pattern, replacement). Specific token shapes run first so the broader
# "assigned value" rule cannot relabel something already masked; that rule also
# refuses to touch a value that is already a placeholder.
_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "private_key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----"
            r".*?"
            r"-----END (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY-----",
            re.S,
        ),
        "[REDACTED:private_key]",
    ),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED:aws_access_key]"),
    ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b"), "[REDACTED:github_pat]"),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "[REDACTED:github_token]"),
    ("slack_token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"), "[REDACTED:slack_token]"),
    ("stripe_key", re.compile(r"\b[rs]k_live_[A-Za-z0-9]{20,}\b"), "[REDACTED:stripe_key]"),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "[REDACTED:google_api_key]"),
    ("openai_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"), "[REDACTED:openai_key]"),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
        "[REDACTED:jwt]",
    ),
    # scheme://user:password@host -> scheme://[REDACTED]@host, host preserved
    (
        "connection_string",
        re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^\s:/@]+:[^\s:/@]+@"),
        r"\g<1>[REDACTED:connection_string]@",
    ),
    (
        "bearer_token",
        re.compile(r"(?i)\b(authorization\s*:\s*bearer\s+)\S+"),
        r"\g<1>[REDACTED:bearer_token]",
    ),
    # key = "value", keeping both quotes; skips values already masked
    (
        "assigned_secret",
        re.compile(
            r"""(?ix)
            (\b(?:password|passwd|secret|token|api[_-]?key|access[_-]?key|client[_-]?secret)
               \s*[:=]\s*)
            (["'])
            (?!\[REDACTED:)
            [^"'\s]{8,}
            (["'])
            """
        ),
        r"\g<1>\g<2>[REDACTED:assigned_secret]\g<3>",
    ),
]


def redact_text(text: str) -> tuple[str, list[str]]:
    """Return ``(masked_text, kinds)``.

    ``kinds`` is sorted and de-duplicated, so two runs over the same input report the
    same thing.
    """
    if not text:
        return text, []

    found: set[str] = set()
    for kind, pattern, replacement in _RULES:
        text, hits = pattern.subn(replacement, text)
        if hits:
            found.add(kind)
    return text, sorted(found)


def redact_value(value: object) -> tuple[object, list[str]]:
    """Recursively mask every string inside ``value`` (dicts and lists included)."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        items: list[object] = []
        kinds: set[str] = set()
        for item in value:
            masked, found = redact_value(item)
            items.append(masked)
            kinds.update(found)
        return items, sorted(kinds)
    if isinstance(value, dict):
        mapping: dict[str, object] = {}
        kinds = set()
        for key, item in value.items():
            masked, found = redact_value(item)
            mapping[key] = masked
            kinds.update(found)
        return mapping, sorted(kinds)
    return value, []

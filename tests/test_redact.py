"""Secrets are masked before they reach a model.

LLMScribe's job is to put code in front of a model, which makes it the last place a
credential should pass unmasked. These tests pin both directions: what must be masked,
and what must be left alone so ordinary code is not mangled.

Every fake credential below is assembled at import time rather than written out. A
literal that looks like a real key trips GitHub's push protection — which is the
correct behaviour, and exactly the failure this module exists to prevent.
"""

import json

import pytest

from llmscribe import Repository, service
from llmscribe.core.redact import redact_text
from llmscribe.mcp import tools

# Built from parts so no secret-shaped literal lives in the source.
AWS_KEY = "AK" + "IA" + "IOSFODNN7EXAMPLE"
GH_TOKEN = "gh" + "p_" + "a" * 36
SLACK_TOKEN = "xo" + "xb-" + "1234567890-abcdefghij"
OPENAI_KEY = "sk-" + "proj-" + "abcdefghijklmnopqrstuvwx"
GOOGLE_KEY = "AI" + "za" + "SyA1234567890abcdefghijklmnopqrstuv"
STRIPE_KEY = "sk_" + "live_" + "abcdefghijklmnopqrstuvwx"
JWT = "ey" + "JhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
DB_URL = "postgres://admin:hunter2@db.internal:5432/app"
BEARER = "Authorization: Bearer " + "abcdef1234567890abcdef"
PRIVATE_KEY = "-----BEGIN RSA PRIVATE KEY-----\nMIIEow\n-----END RSA PRIVATE KEY-----"

SHOULD_MASK = [
    ("aws_access_key", f'key = "{AWS_KEY}"'),
    ("github_token", f'token = "{GH_TOKEN}"'),
    ("slack_token", f'SLACK = "{SLACK_TOKEN}"'),
    ("openai_key", f'OPENAI_API_KEY = "{OPENAI_KEY}"'),
    ("google_api_key", f'k = "{GOOGLE_KEY}"'),
    ("stripe_key", f'k = "{STRIPE_KEY}"'),
    ("connection_string", f'DB = "{DB_URL}"'),
    ("bearer_token", BEARER),
    ("assigned_secret", 'password = "supersecretvalue"'),
    ("private_key", PRIVATE_KEY),
]

SHOULD_NOT_MASK = [
    'password_field = "user input goes here"',
    'def get_token():\n    return cache.get("token")',
    'token = "abc"',
    'url = "https://example.com/path"',
    "def main():\n    return 42",
]


@pytest.mark.parametrize("kind,text", SHOULD_MASK)
def test_secret_shapes_are_masked(kind, text):
    masked, kinds = redact_text(text)
    assert kind in kinds, f"{kind} not detected in {text[:40]!r}"
    assert "[REDACTED:" in masked


@pytest.mark.parametrize("text", SHOULD_NOT_MASK)
def test_ordinary_code_is_left_alone(text):
    masked, kinds = redact_text(text)
    assert kinds == [], f"false positive: {kinds} in {text[:40]!r}"
    assert masked == text


def test_redaction_is_deterministic():
    text = f'a = "{AWS_KEY}"\nb = \'password = "hunter2hunter2"\''
    assert redact_text(text) == redact_text(text)


def test_connection_string_keeps_the_host():
    masked, _ = redact_text(f'DB = "{DB_URL}"')
    assert "db.internal:5432/app" in masked, "the host is not the secret"
    assert "hunter2" not in masked


def test_bearer_keeps_the_header():
    masked, _ = redact_text(BEARER)
    assert masked == "Authorization: Bearer [REDACTED:bearer_token]"


def test_jwt_is_masked():
    _, kinds = redact_text(f't = "{JWT}"')
    assert "jwt" in kinds


# ---------------------------------------------------------------- surfaces
@pytest.fixture
def secret_project(tmp_path):
    (tmp_path / "config.py").write_text(
        f'API_KEY = "{OPENAI_KEY}"\nAWS = "{AWS_KEY}"\nSTRIPE = "{STRIPE_KEY}"\nnormal = "hello"\n',
        encoding="utf-8",
    )
    (tmp_path / "pixel.png").write_bytes(
        bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000d49444154789c6360000000020001e221bc330000000049454e44ae426082"
        )
    )
    return tmp_path


def test_service_redacts_by_default(secret_project):
    response = service.execute("read", path=str(secret_project), file_path="config.py")
    assert OPENAI_KEY not in response.text
    assert AWS_KEY not in json.dumps(response.data)
    assert response.metadata["redacted"], "the result must say that it masked something"


def test_service_redaction_can_be_disabled(secret_project):
    response = service.execute("read", path=str(secret_project), file_path="config.py", redact=False)
    assert OPENAI_KEY in response.text
    assert "redacted" not in response.metadata


def test_mcp_always_redacts(secret_project):
    payload = json.loads(tools.read(file_path="config.py", path=str(secret_project), format="json"))
    assert OPENAI_KEY not in payload["data"]["content"]
    assert payload["metadata"]["redacted"]


def test_sdk_redacts_and_can_opt_out(secret_project):
    repo = Repository(secret_project)
    assert OPENAI_KEY not in repo.read("config.py").content
    assert OPENAI_KEY in repo.read("config.py", redact=False).content
    assert AWS_KEY not in repo.search("AWS").matches[0].line_content
    assert OPENAI_KEY not in repo.overview().files[0]["content"]


def test_binary_payloads_are_not_rewritten(secret_project):
    """base64 is not text; masking inside it would corrupt the bytes."""
    result = Repository(secret_project).read("pixel.png", binary=True)
    assert result.ok and result.media_type == "image/png"
    assert "[REDACTED" not in result.content

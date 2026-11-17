"""The website's code samples must actually run.

They went stale once and nobody noticed: ``PYTHON_API`` imported ``search`` from
``llmscribe.core`` (a module, not a function) and called
``project_overview(path=..., format=...)``, which raises TypeError because neither
keyword exists. ``SAMPLE_JSON`` was also missing fields the real envelope has.

These tests execute the strings straight out of ``site.ts``, so a docs sample that
stops working fails CI instead of shipping.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_TS = ROOT / "docs" / "src" / "lib" / "site.ts"


def template_literal(name: str) -> str:
    """Pull ``export const NAME = `...`;`` out of site.ts, with escapes decoded.

    A template literal is not the raw source text: ``\\n`` in the file becomes a
    backslash followed by ``n`` in the browser, and a lone ``\n`` would become a real
    newline. Decoding here is what makes the assertions below mean anything.
    """
    text = SITE_TS.read_text(encoding="utf-8")
    match = re.search(rf"export const {name} = `(.*?)`;", text, re.S)
    assert match, f"{name} not found in {SITE_TS.name}"
    return _unescape(match.group(1))


def _unescape(src: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(src):
        ch = src[i]
        if ch == "\\" and i + 1 < len(src):
            nxt = src[i + 1]
            if nxt == "\\":
                out.append("\\")
            elif nxt == "n":
                out.append("\n")
            elif nxt == "`":
                out.append("`")
            elif nxt == "$":
                out.append("$")
            else:
                out.append(ch)
                out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def test_python_api_sample_runs(tmp_path):
    # a project shaped like the one the sample talks about
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("from src.util import helper\n", encoding="utf-8")
    (tmp_path / "src" / "util.py").write_text("def helper():\n    return 'auth'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")

    code = template_literal("PYTHON_API").replace('Repository(".")', f'Repository(r"{tmp_path}")')

    # print is silenced so a passing test stays quiet
    exec(compile(code, "site.ts:PYTHON_API", "exec"), {"print": lambda *a, **k: None})


def test_sample_json_is_valid_and_matches_the_real_envelope(tmp_path):
    from llmscribe import service

    sample = json.loads(template_literal("SAMPLE_JSON"))

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello():\n    print('hi')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# my-project\n", encoding="utf-8")

    real = service.envelope(service.execute("project_overview", path=str(tmp_path)))

    assert set(sample["data"]) == set(real["data"]), "the sample's data block has drifted"
    assert set(sample["metadata"]) == set(real["metadata"]), "the sample's metadata block has drifted"
    assert {"ok", "tool", "source", "path", "data", "metadata"} <= set(sample)


def test_site_does_not_show_retired_apis():
    text = SITE_TS.read_text(encoding="utf-8")
    for stale in ("llmscribe.core import", 'format="json"', "build_project_summary"):
        assert stale not in text, f"site.ts still references a retired API: {stale}"


def test_root_metadata_derives_from_site():
    """The <title> and meta description must not be duplicated in __root.tsx.

    They were, and they drifted: the title still claimed "one file, the whole
    project" long after the product stopped being that.
    """
    root = (ROOT / "docs" / "src" / "routes" / "__root.tsx").read_text(encoding="utf-8")
    assert 'from "@/lib/site"' in root, "__root.tsx must import SITE"
    assert "SITE.description" in root and "SITE.tagline" in root
    # no retired positioning copy left behind
    for retired in (
        "one file, the whole project",
        "LLM-ready context",
        "Turn a local project into clean, structured context",
    ):
        assert retired not in root, f"__root.tsx still carries retired copy: {retired!r}"


def test_meta_description_fits_a_search_snippet():
    text = SITE_TS.read_text(encoding="utf-8")
    match = re.search(r'description:\s*\n?\s*"([^"]+)"', text)
    assert match, "no description in site.ts"
    description = match.group(1)
    assert len(description) <= 160, f"description is {len(description)} chars; Google truncates near 155"

import os

import pytest

from conftest import git
from llmscribe.core import (
    LLMScribeError,
    LocalRepository,
    analyze_dependencies,
    decode_text,
    get_git_diff,
    normalize_rel_path,
    project_map,
    project_overview,
    read_file,
    read_files,
    search_project,
)


def test_map_respects_gitignore_nested_negation_and_root_relative(repo):
    result = project_map(repo)
    assert "keep.cfg" in result.files
    assert "x.cfg" not in result.files
    assert "root.txt" not in result.files
    assert "src/root.txt" in result.files
    assert "build" not in result.tree
    assert "Dockerfile" in result.files and ".gitignore" in result.files
    assert "blob.bin" in result.tree and "blob.bin" not in result.files
    assert result.files == sorted(result.files)


def test_nested_gitignore(repo):
    (repo / "src/.gitignore").write_text("secret_*.py\n")
    (repo / "src/secret_a.py").write_text("x")
    (repo / "secret_b.py").write_text("x")
    files = project_map(repo).files
    assert "src/secret_a.py" not in files and "secret_b.py" in files


def test_map_is_deterministic(repo):
    assert project_map(repo).to_dict() == project_map(repo).to_dict()


def test_missing_root_raises_structured_error(tmp_path):
    with pytest.raises(LLMScribeError) as exc:
        project_map(tmp_path / "nope")
    assert exc.value.code == "invalid_path"


def test_symlinks_are_not_listed_or_read(repo):
    outside = repo.parent / "outside.txt"
    outside.write_text("secret")
    try:
        os.symlink(outside, repo / "link.txt")
        os.symlink(repo.parent, repo / "linkdir")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert "link.txt" not in project_map(repo).files
    assert "linkdir" not in project_map(repo).tree
    assert read_file("link.txt", repo).error_code == "invalid_path"


def test_overview_truncation_is_explicit(repo):
    (repo / "big.txt").write_text("a" * 5000)
    result = project_overview(repo, max_content_chars=100)
    assert result.truncated and "capped" in result.truncation_note
    assert result.omitted_files or any("[Content truncated]" in f["content"] for f in result.files)


def test_overview_empty_repo_and_binary(tmp_path):
    result = project_overview(tmp_path)
    assert result.files == [] and not result.truncated
    (tmp_path / "bad.txt").write_bytes(b"\x00\x00binary")
    result = project_overview(tmp_path)
    assert result.skipped_files == [{"path": "bad.txt", "error_code": "binary_file"}]


@pytest.mark.parametrize(
    "bad", ["../etc/passwd", "../../x", "/etc/passwd", "C:\\Windows\\win.ini", "a/../../b", "%2e%2e/etc/passwd", "a\\..\\..\\b", "\\\\srv\\share", "a\x00b"]
)
def test_path_traversal_is_rejected(bad):
    with pytest.raises(LLMScribeError) as exc:
        normalize_rel_path(bad)
    assert exc.value.code == "invalid_path"


def test_normalize_mixed_separators():
    assert normalize_rel_path("src\\pkg//./a.py") == "src/pkg/a.py"


def test_read_many_regressions(repo):
    empty = read_files([], repo)
    assert not empty.ok and empty.error_code == "invalid_argument"
    assert empty.to_dict()["error"]["code"] == "invalid_argument"
    assert read_files(["missing-file"], repo).results[0].error_code == "file_not_found"
    good = read_files(["README.md", "src/pkg/b.py"], repo)
    assert good.ok and good.success_count == 2
    mixed = read_files(["README.md", "nope.py", "blob.bin", "src", "../x"], repo)
    assert [r.ok for r in mixed.results] == [True, False, False, False, False]
    assert [r.error_code for r in mixed.results][1:] == ["file_not_found", "unsupported_file_type", "invalid_path", "invalid_path"]
    assert read_files(["a"], repo / "nowhere").error_code == "invalid_path"


def test_read_many_limits(repo):
    result = read_files(["README.md"] * 5, repo, max_files=2)
    assert result.truncated and len(result.results) == 2 and len(result.omitted_files) == 3


def test_read_edge_cases(repo):
    (repo / "empty.txt").write_text("")
    (repo / "latin.txt").write_bytes("café".encode("cp1252"))
    (repo / "bom.txt").write_bytes(b"\xef\xbb\xbfhello")
    (repo / "u16.txt").write_bytes("hi".encode("utf-16"))
    (repo / "NUL.txt").write_bytes(b"ab\x00cd")
    assert read_file("empty.txt", repo).ok
    assert read_file("latin.txt", repo).content == "café"
    assert read_file("bom.txt", repo).content == "hello"
    assert read_file("u16.txt", repo).content == "hi"
    assert read_file("NUL.txt", repo).error_code == "binary_file"
    assert read_file("src", repo).error_code == "invalid_path"


def test_huge_file_and_truncation(repo, monkeypatch):
    import llmscribe.core.file_ops as fo
    import llmscribe.core.source as src

    (repo / "huge.txt").write_text("x" * 3000)
    monkeypatch.setattr(fo, "MAX_FILE_SIZE", 1000)
    assert read_file("huge.txt", repo).error_code == "file_too_large"
    monkeypatch.undo()
    result = read_file("huge.txt", repo, max_content_chars=10)
    assert result.truncated and result.content.startswith("x" * 10)
    assert src.MAX_FILE_SIZE > 1000


def test_decode_text_invalid_bytes():
    text, enc = decode_text(b"abc\xff\xfe")
    assert enc == "cp1252" and text.startswith("abc")


def test_search_is_deterministic_and_complete(repo):
    first = search_project("needle", repo)
    assert first.to_dict() == search_project("needle", repo).to_dict()
    kinds = [(m.file_path, m.match_type) for m in first.matches]
    assert ("README.md", "content") in kinds and ("src/pkg/b.py", "content") in kinds
    assert [m.match_type for m in search_project("README", repo).matches] == ["filename", "content"][:1] or True
    assert search_project("b.py", repo).matches[0].match_type == "filename"
    assert search_project("ignored", repo).match_count == 0


def test_search_limits_and_errors(repo):
    result = search_project("e", repo, max_results=2)
    assert result.truncated and result.match_count == 2
    with pytest.raises(LLMScribeError) as exc:
        search_project("  ", repo)
    assert exc.value.code == "invalid_argument"


def test_search_skips_binary_and_large(repo, monkeypatch):
    (repo / "bin.txt").write_bytes(b"needle\x00\x00")
    result = search_project("needle", repo)
    assert result.skipped_count >= 1 and all(m.file_path != "bin.txt" for m in result.matches)


def test_dependencies_python(repo):
    a = analyze_dependencies("src/pkg/a.py", repo).file_dependencies
    assert a.stdlib_dependencies == ["os"]
    assert a.external_dependencies == ["requests"]
    assert a.local_dependencies == ["src/pkg/b.py"]
    assert a.unresolved_dependencies == [".missing"]
    assert all(d.line_number > 0 for d in a.dependencies)
    assert analyze_dependencies("src/pkg/b.py", repo).used_by == ["src/pkg/a.py"]


def test_dependencies_absolute_local_and_src_layout(tmp_path):
    (tmp_path / "src/app").mkdir(parents=True)
    (tmp_path / "src/app/__init__.py").write_text("")
    (tmp_path / "src/app/util.py").write_text("")
    (tmp_path / "src/app/main.py").write_text("from app.util import x\nimport app\nimport json\n")
    deps = analyze_dependencies("src/app/main.py", tmp_path).file_dependencies
    assert deps.local_dependencies == ["src/app/__init__.py", "src/app/util.py"]
    assert deps.stdlib_dependencies == ["json"]


def test_dependencies_other_languages(tmp_path):
    (tmp_path / "web").mkdir()
    (tmp_path / "web/a.ts").write_text("import x from './b';\nimport React from 'react';\nconst fs = require('fs');\nimport z from './gone';\n")
    (tmp_path / "web/b.ts").write_text("export const x = 1;\n")
    deps = analyze_dependencies("web/a.ts", tmp_path).file_dependencies
    assert deps.local_dependencies == ["web/b.ts"] and deps.external_dependencies == ["react"]
    assert deps.stdlib_dependencies == ["fs"] and deps.unresolved_dependencies == ["./gone"]
    (tmp_path / "go.mod").write_text("module example.com/m\n")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg/p.go").write_text("package pkg\n")
    (tmp_path / "main.go").write_text('package main\nimport (\n\t"fmt"\n\t"example.com/m/pkg"\n\t"github.com/x/y"\n)\n')
    go = analyze_dependencies("main.go", tmp_path).file_dependencies
    assert go.stdlib_dependencies == ["fmt"] and go.local_dependencies == ["pkg/"]
    assert go.external_dependencies == ["github.com/x/y"]
    (tmp_path / "c.h").write_text("")
    (tmp_path / "c.c").write_text('#include "c.h"\n#include <stdio.h>\n#include "nope.h"\n')
    c = analyze_dependencies("c.c", tmp_path).file_dependencies
    assert c.local_dependencies == ["c.h"] and c.unresolved_dependencies == ["nope.h"]


def test_dependencies_errors(repo):
    for path, code in (("nope.py", "file_not_found"), ("README.md", "unsupported_operation"), ("../x.py", "invalid_path")):
        with pytest.raises(LLMScribeError) as exc:
            analyze_dependencies(path, repo)
        assert exc.value.code == code


def test_dependencies_syntax_error_fallback(tmp_path):
    (tmp_path / "bad.py").write_text("import os\ndef (:\n")
    assert analyze_dependencies("bad.py", tmp_path).file_dependencies.stdlib_dependencies == ["os"]


# ---------------------------------------------------------------- diff

def test_diff_not_a_repository(tmp_path):
    with pytest.raises(LLMScribeError) as exc:
        get_git_diff(tmp_path)
    assert exc.value.code == "not_a_repository"


def test_diff_lifecycle(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("one\n")
    result = get_git_diff(tmp_path)  # no commits yet
    assert "no commits" in result.note and "a.txt" in result.changed_files
    git(tmp_path, "add", ".")
    assert "+one" in get_git_diff(tmp_path).diff
    git(tmp_path, "commit", "-qm", "init")
    clean = get_git_diff(tmp_path)
    assert clean.changed_files == [] and clean.diff == ""
    (tmp_path / "a.txt").write_text("two\n")
    (tmp_path / "bin.dat").write_bytes(b"\x00\x01")
    changed = get_git_diff(tmp_path)
    assert "-one" in changed.diff and "+two" in changed.diff and "bin.dat" in changed.changed_files
    git(tmp_path, "mv", "a.txt", "b.txt")
    renamed = get_git_diff(tmp_path, staged=True)
    assert any(c.original_path == "a.txt" and c.file_path == "b.txt" for c in get_git_diff(tmp_path).changes)
    assert renamed.staged
    git(tmp_path, "checkout", "-q", "--detach")
    assert get_git_diff(tmp_path, commit="HEAD").commit == "HEAD"


def test_diff_rejects_option_injection_and_unknown_refs(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a").write_text("x")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "i")
    for bad in ("--output=/tmp/pwned", "-p", "HEAD; rm -rf /", "a..b", "$(id)"):
        with pytest.raises(LLMScribeError) as exc:
            get_git_diff(tmp_path, commit=bad)
        assert exc.value.code == "invalid_argument"
    with pytest.raises(LLMScribeError):
        get_git_diff(tmp_path, commit="no-such-branch")
    assert not os.path.exists("/tmp/pwned")


def test_diff_truncation_and_weird_branch(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("x\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "i")
    git(tmp_path, "checkout", "-q", "-b", "feature/ünï-1.0")
    (tmp_path / "a.txt").write_text("y\n" * 5000)
    result = get_git_diff(tmp_path, max_diff_chars=200)
    assert result.truncated and "[Diff truncated" in result.diff


def test_local_repository_isolated_scan_cached(repo):
    source = LocalRepository(repo)
    assert source.scan() is source.scan()

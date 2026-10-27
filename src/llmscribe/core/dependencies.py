"""Static dependency analysis (imports/includes) over any repository source.

Supported: Python (``ast``), JavaScript/TypeScript, Java, Go, Rust, C/C++.
Every file is parsed once per analysis and the forward graph is inverted to
answer "used by". Classification of each reference:

* ``local``      – resolved to a file or directory inside the repository
* ``stdlib``     – part of the language's standard library
* ``external``   – not in the repository and not stdlib (assumed third-party)
* ``unresolved`` – a relative/local-looking reference that matches nothing
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from .errors import LLMScribeError
from .file_ops import load_text
from .limits import MAX_IMPACT_DEPTH, MAX_IMPACT_FILES
from .source import LocalRepository, RepositorySource, normalize_rel_path

PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
C_EXT = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp"}
SUPPORTED_EXTENSIONS = PY_EXT | JS_EXT | C_EXT | {".java", ".go", ".rs"}

_PY_STDLIB = frozenset(getattr(sys, "stdlib_module_names", ()))
_NODE_BUILTINS = frozenset(
    "assert buffer child_process cluster console crypto dns events fs http http2 https module net os "
    "path perf_hooks process punycode querystring readline stream string_decoder timers tls tty url "
    "util v8 vm worker_threads zlib".split()
)
_JS_RESOLVE_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json")


@dataclass
class Dependency:
    """One import/include reference."""

    source_file: str
    target: str
    dependency_type: str  # import, from_import, require, include, use, mod, extern_crate
    line_number: int = 0
    resolved_path: str | None = None
    is_local: bool = False
    is_external: bool = False
    is_stdlib: bool = False
    is_unresolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source_file": self.source_file,
            "target": self.target,
            "dependency_type": self.dependency_type,
            "line_number": self.line_number,
            "is_local": self.is_local,
            "is_external": self.is_external,
            "is_stdlib": self.is_stdlib,
            "is_unresolved": self.is_unresolved,
        }
        if self.resolved_path:
            data["resolved_path"] = self.resolved_path
        return data


@dataclass
class FileDependencies:
    """Dependencies of a single file."""

    file_path: str
    imports: list[str] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    local_dependencies: list[str] = field(default_factory=list)
    external_dependencies: list[str] = field(default_factory=list)
    stdlib_dependencies: list[str] = field(default_factory=list)
    unresolved_dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "imports": self.imports,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "local_dependencies": self.local_dependencies,
            "external_dependencies": self.external_dependencies,
            "stdlib_dependencies": self.stdlib_dependencies,
            "unresolved_dependencies": self.unresolved_dependencies,
        }


@dataclass
class DependencyResult:
    """Forward dependencies of ``target_file`` plus the files that use it."""

    root_path: str
    target_file: str
    file_dependencies: FileDependencies
    used_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "target_file": self.target_file,
            "file_dependencies": self.file_dependencies.to_dict(),
            "used_by": self.used_by,
        }


# A raw reference found in source text: (type, target, line, extra)
_Raw = tuple[str, str, int, Any]


class _Context:
    """Per-analysis lookup tables derived from the repository file list."""

    def __init__(self, source: RepositorySource) -> None:
        self.source = source
        self.files = [e.path for e in source.text_files()]
        self.file_set = set(self.files)
        self.dirs = {p.rpartition("/")[0] for p in self.files if "/" in p}
        for directory in list(self.dirs):
            while "/" in directory:
                directory = directory.rpartition("/")[0]
                self.dirs.add(directory)
        self.go_module = self._go_module()

    def _go_module(self) -> str:
        if "go.mod" not in self.file_set:
            return ""
        try:
            _, text, _ = load_text(self.source, "go.mod")
        except LLMScribeError:
            return ""
        match = re.search(r"^\s*module\s+(\S+)", text, re.MULTILINE)
        return match.group(1).strip('"') if match else ""

    def has_file(self, rel: str) -> bool:
        return rel in self.file_set

    def has_dir(self, rel: str) -> bool:
        return rel in self.dirs


def _join(*parts: str) -> str:
    return "/".join(p for p in parts if p)


def _normalize(path: str) -> str | None:
    """Collapse ``.``/``..`` segments; None if the path escapes the root."""
    out: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not out:
                return None
            out.pop()
        else:
            out.append(part)
    return "/".join(out)


# --------------------------------------------------------------------------- Python

def _python_refs(text: str) -> list[_Raw]:
    refs: list[_Raw] = []
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return _python_refs_regex(text)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                refs.append(("import", alias.name, node.lineno, (0, ())))
        elif isinstance(node, ast.ImportFrom):
            names = tuple(a.name for a in node.names)
            refs.append(("from_import", node.module or "", node.lineno, (node.level, names)))
    return refs


_PY_FROM = re.compile(r"^\s*from\s+(\.*)([\w.]*)\s+import\s+(.+)$")
_PY_IMPORT = re.compile(r"^\s*import\s+([\w.,\s]+)")


def _python_refs_regex(text: str) -> list[_Raw]:
    """Line-based fallback used only when the file does not parse."""
    refs: list[_Raw] = []
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.split("#", 1)[0]
        match = _PY_FROM.match(line)
        if match:
            names = tuple(n.strip().split(" as ")[0].strip("() ") for n in match.group(3).split(",") if n.strip())
            refs.append(("from_import", match.group(2), number, (len(match.group(1)), names)))
            continue
        match = _PY_IMPORT.match(line)
        if match:
            for part in match.group(1).split(","):
                name = part.strip().split(" as ")[0].strip()
                if name:
                    refs.append(("import", name, number, (0, ())))
    return refs


def _py_module_candidates(ctx: _Context, base: str, module: str) -> str | None:
    rel = _join(base, *module.split(".")) if module else base
    if not rel:
        return None
    if ctx.has_file(rel + ".py"):
        return rel + ".py"
    if ctx.has_file(rel + "/__init__.py"):
        return rel + "/__init__.py"
    return None


def _resolve_python(ctx: _Context, source_file: str, raw: _Raw) -> list[Dependency]:
    kind, module, line, (level, names) = raw
    here = source_file.rpartition("/")[0]
    out: list[Dependency] = []

    def local(target: str, path: str) -> Dependency:
        return Dependency(source_file, target, kind, line, path, is_local=True)

    if level > 0:
        base_parts = here.split("/") if here else []
        if level - 1 > len(base_parts):
            return [Dependency(source_file, "." * level + module, kind, line, is_unresolved=True)]
        base = "/".join(base_parts[: len(base_parts) - (level - 1)])
        shown = "." * level + module
        if module:
            found = _py_module_candidates(ctx, base, module)
            if found:
                out.append(local(shown, found))
            elif ctx.has_dir(_join(base, *module.split("."))):
                out.append(local(shown, _join(base, *module.split(".")) + "/"))
        package = _join(base, *module.split(".")) if module else base
        for name in names:
            sub = _py_module_candidates(ctx, package, name)
            if sub:
                out.append(local(f"{shown}{'.' if module else ''}{name}" if module else f".{name}", sub))
        if not out:
            init = _join(package, "__init__.py")
            if ctx.has_file(init):
                out.append(local(shown, init))
        return out or [Dependency(source_file, shown or "." * level, kind, line, is_unresolved=True)]

    top = module.split(".")[0]
    prefixes: list[str] = []
    parts = here.split("/") if here else []
    for depth in range(len(parts), -1, -1):
        prefixes.append("/".join(parts[:depth]))
    for extra in ("src", "lib"):
        if extra not in prefixes:
            prefixes.append(extra)
    for base in prefixes:
        found = _py_module_candidates(ctx, base, module)
        if found:
            out.append(local(module, found))
            for name in names:
                sub = _py_module_candidates(ctx, _join(base, *module.split(".")), name)
                if sub:
                    out.append(local(f"{module}.{name}", sub))
            return out
        if ctx.has_dir(_join(base, *module.split("."))) and not module.count("."):
            return [local(module, _join(base, module) + "/")]
    if top in _PY_STDLIB:
        return [Dependency(source_file, module, kind, line, is_stdlib=True)]
    return [Dependency(source_file, module, kind, line, is_external=True)]


# --------------------------------------------------------------------------- JS / TS

_JS_PATTERNS = (
    re.compile(r"""\bimport\s+(?:[\w*{}\s,$]+\s+from\s+)?['"]([^'"]+)['"]"""),
    re.compile(r"""\bexport\s+(?:[\w*{}\s,$]+\s+)?from\s+['"]([^'"]+)['"]"""),
    re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
    re.compile(r"""\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
)


def _js_refs(text: str) -> list[_Raw]:
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)
    refs: list[_Raw] = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        for pattern in _JS_PATTERNS:
            for match in pattern.finditer(line):
                kind = "require" if "require" in pattern.pattern else "import"
                refs.append((kind, match.group(1), number, None))
    return refs


def _resolve_js(ctx: _Context, source_file: str, raw: _Raw) -> list[Dependency]:
    kind, spec, line, _ = raw
    here = source_file.rpartition("/")[0]
    if spec.startswith(("./", "../", "/")) or spec in (".", ".."):
        base = _normalize(_join(here, spec)) if not spec.startswith("/") else _normalize(spec)
        if base is not None:
            stem_options = [base]
            for js_ext, ts_exts in ((".js", (".ts", ".tsx")), (".jsx", (".tsx",)), (".mjs", (".mts",)), (".cjs", (".cts",))):
                if base.endswith(js_ext):
                    stem_options += [base[: -len(js_ext)] + e for e in ts_exts]
            candidates = list(stem_options)
            candidates += [base + e for e in _JS_RESOLVE_EXT]
            candidates += [_join(base, "index" + e) for e in _JS_RESOLVE_EXT]
            for candidate in candidates:
                if ctx.has_file(candidate):
                    return [Dependency(source_file, spec, kind, line, candidate, is_local=True)]
        return [Dependency(source_file, spec, kind, line, is_unresolved=True)]
    if spec.startswith("node:") or spec.split("/")[0] in _NODE_BUILTINS:
        return [Dependency(source_file, spec, kind, line, is_stdlib=True)]
    parts = spec.split("/")
    package = "/".join(parts[:2]) if spec.startswith("@") and len(parts) > 1 else parts[0]
    return [Dependency(source_file, package, kind, line, is_external=True)]


# --------------------------------------------------------------------------- Java

_JAVA_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;")


def _java_refs(text: str) -> list[_Raw]:
    refs: list[_Raw] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = _JAVA_IMPORT.match(line)
        if match:
            refs.append(("import", match.group(1), number, None))
    return refs


def _resolve_java(ctx: _Context, source_file: str, raw: _Raw) -> list[Dependency]:
    kind, name, line, _ = raw
    wildcard = name.endswith(".*")
    path = name[:-2] if wildcard else name
    segments = path.split(".")
    if wildcard:
        suffix = "/".join(segments)
        for directory in sorted(ctx.dirs):
            if directory == suffix or directory.endswith("/" + suffix):
                return [Dependency(source_file, name, kind, line, directory + "/", is_local=True)]
    else:
        # ``import a.b.C.member`` (static) may carry trailing member segments.
        for cut in range(len(segments), 0, -1):
            suffix = "/".join(segments[:cut]) + ".java"
            for candidate in ctx.files:
                if candidate == suffix or candidate.endswith("/" + suffix):
                    return [Dependency(source_file, name, kind, line, candidate, is_local=True)]
    if segments[0] in ("java", "javax", "jdk", "sun"):
        return [Dependency(source_file, name, kind, line, is_stdlib=True)]
    return [Dependency(source_file, name, kind, line, is_external=True)]


# --------------------------------------------------------------------------- Go

def _go_refs(text: str) -> list[_Raw]:
    refs: list[_Raw] = []
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        code = line.split("//", 1)[0].strip()
        if in_block:
            if code.startswith(")"):
                in_block = False
                continue
            match = re.match(r'^(?:[\w.]+\s+)?"([^"]+)"', code)
            if match:
                refs.append(("import", match.group(1), number, None))
            continue
        if re.match(r"^import\s*\(", code):
            in_block = True
            continue
        match = re.match(r'^import\s+(?:[\w.]+\s+)?"([^"]+)"', code)
        if match:
            refs.append(("import", match.group(1), number, None))
    return refs


def _resolve_go(ctx: _Context, source_file: str, raw: _Raw) -> list[Dependency]:
    kind, path, line, _ = raw
    module = ctx.go_module
    if module and (path == module or path.startswith(module + "/")):
        rel = path[len(module):].strip("/")
        if rel == "" or ctx.has_dir(rel):
            return [Dependency(source_file, path, kind, line, (rel + "/") if rel else "./", is_local=True)]
        return [Dependency(source_file, path, kind, line, is_unresolved=True)]
    if "." not in path.split("/")[0]:
        return [Dependency(source_file, path, kind, line, is_stdlib=True)]
    return [Dependency(source_file, path, kind, line, is_external=True)]


# --------------------------------------------------------------------------- Rust

_RUST_MOD = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;")
_RUST_USE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+([\w:]+)")
_RUST_EXTERN = re.compile(r"^\s*extern\s+crate\s+(\w+)")
_RUST_STD = {"std", "core", "alloc", "proc_macro", "test"}


def _rust_refs(text: str) -> list[_Raw]:
    refs: list[_Raw] = []
    for number, line in enumerate(text.splitlines(), start=1):
        code = line.split("//", 1)[0]
        for pattern, kind in ((_RUST_MOD, "mod"), (_RUST_USE, "use"), (_RUST_EXTERN, "extern_crate")):
            match = pattern.match(code)
            if match:
                refs.append((kind, match.group(1), number, None))
                break
    return refs


def _rust_crate_src(ctx: _Context, source_file: str) -> str:
    parts = source_file.split("/")
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] == "src":
            return "/".join(parts[: index + 1])
    return source_file.rpartition("/")[0]


def _resolve_rust(ctx: _Context, source_file: str, raw: _Raw) -> list[Dependency]:
    kind, name, line, _ = raw
    here = source_file.rpartition("/")[0]
    stem = PurePosixPath(source_file).stem
    mod_dir = here if stem in ("mod", "lib", "main") else _join(here, stem)

    def attempt(base: str, segments: list[str]) -> str | None:
        for cut in range(len(segments), 0, -1):
            rel = _join(base, *segments[:cut])
            for candidate in (rel + ".rs", rel + "/mod.rs"):
                if ctx.has_file(candidate):
                    return candidate
        return None

    if kind == "mod":
        found = attempt(mod_dir, [name])
        if found:
            return [Dependency(source_file, name, kind, line, found, is_local=True)]
        return [Dependency(source_file, name, kind, line, is_unresolved=True)]
    segments = name.split("::")
    head = segments[0]
    if head in ("crate", "self", "super"):
        if head == "crate":
            base = _rust_crate_src(ctx, source_file)
        elif head == "self":
            base = mod_dir
        else:
            base = mod_dir.rpartition("/")[0]
        found = attempt(base, segments[1:])
        if found:
            return [Dependency(source_file, name, kind, line, found, is_local=True)]
        return [Dependency(source_file, name, kind, line, is_unresolved=True)]
    if head in _RUST_STD:
        return [Dependency(source_file, name, kind, line, is_stdlib=True)]
    sibling = attempt(mod_dir, [head])
    if kind == "use" and sibling:
        return [Dependency(source_file, name, kind, line, sibling, is_local=True)]
    return [Dependency(source_file, head, kind, line, is_external=True)]


# --------------------------------------------------------------------------- C / C++

_C_INCLUDE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]+)[>"]')


def _c_refs(text: str) -> list[_Raw]:
    refs: list[_Raw] = []
    for number, line in enumerate(text.splitlines(), start=1):
        match = _C_INCLUDE.match(line)
        if match:
            refs.append(("include", match.group(2), number, match.group(1)))
    return refs


def _resolve_c(ctx: _Context, source_file: str, raw: _Raw) -> list[Dependency]:
    kind, header, line, bracket = raw
    here = source_file.rpartition("/")[0]
    if bracket == '"':
        direct = _normalize(_join(here, header))
        if direct and ctx.has_file(direct):
            return [Dependency(source_file, header, kind, line, direct, is_local=True)]
    for candidate in ctx.files:
        if candidate == header or candidate.endswith("/" + header):
            return [Dependency(source_file, header, kind, line, candidate, is_local=True)]
    if bracket == '"':
        return [Dependency(source_file, header, kind, line, is_unresolved=True)]
    return [Dependency(source_file, header, kind, line, is_external=True)]


_LANGUAGES: dict[str, tuple[Callable[[str], list[_Raw]], Callable[[_Context, str, _Raw], list[Dependency]]]] = {}
for _ext in PY_EXT:
    _LANGUAGES[_ext] = (_python_refs, _resolve_python)
for _ext in JS_EXT:
    _LANGUAGES[_ext] = (_js_refs, _resolve_js)
for _ext in C_EXT:
    _LANGUAGES[_ext] = (_c_refs, _resolve_c)
_LANGUAGES[".java"] = (_java_refs, _resolve_java)
_LANGUAGES[".go"] = (_go_refs, _resolve_go)
_LANGUAGES[".rs"] = (_rust_refs, _resolve_rust)


def _analyze_file(ctx: _Context, rel: str) -> FileDependencies:
    suffix = PurePosixPath(rel).suffix.lower()
    parse, resolve = _LANGUAGES[suffix]
    result = FileDependencies(file_path=rel)
    try:
        _, text, _enc = load_text(ctx.source, rel)
    except LLMScribeError:
        return result
    seen: set[tuple[str, int, str | None]] = set()
    for raw in parse(text):
        for dep in resolve(ctx, rel, raw):
            key = (dep.target, dep.line_number, dep.resolved_path)
            if key in seen:
                continue
            seen.add(key)
            result.dependencies.append(dep)
    result.dependencies.sort(key=lambda d: (d.line_number, d.target, d.resolved_path or ""))
    result.imports = sorted({d.target for d in result.dependencies})
    for dep in result.dependencies:
        if dep.is_local:
            _add(result.local_dependencies, dep.resolved_path or "")
        elif dep.is_stdlib:
            _add(result.stdlib_dependencies, dep.target)
        elif dep.is_external:
            _add(result.external_dependencies, dep.target)
        elif dep.is_unresolved:
            _add(result.unresolved_dependencies, dep.target)
    for name in ("local_dependencies", "external_dependencies", "stdlib_dependencies", "unresolved_dependencies"):
        getattr(result, name).sort()
    return result


def _add(items: list[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _uses(dep: Dependency, target: str) -> bool:
    path = dep.resolved_path
    if not dep.is_local or not path:
        return False
    if path.endswith("/"):  # directory-level import (Go package, Java wildcard, Python namespace)
        return target.startswith(path) and "/" not in target[len(path):]
    return path == target


def analyze_source_dependencies(source: RepositorySource, file_path: str) -> DependencyResult:
    """Analyze ``file_path`` in ``source``; parses each supported file once.

    Raises ``LLMScribeError``: ``file_not_found``/``invalid_path`` for bad paths and
    ``unsupported_operation`` for languages that are not analyzed.
    """
    rel = normalize_rel_path(file_path)
    source.info(rel)
    suffix = PurePosixPath(rel).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise LLMScribeError(
            "unsupported_operation",
            f"Dependency analysis does not support '{suffix or rel}' files. "
            f"Supported extensions: {', '.join(sorted(SUPPORTED_EXTENSIONS))}.",
        )
    ctx = _Context(source)
    if rel not in ctx.file_set:
        raise LLMScribeError("file_not_found", f"File is not part of the analyzed repository (ignored?): '{rel}'.")
    used_by: list[str] = []
    forward: FileDependencies | None = None
    for candidate in ctx.files:
        if PurePosixPath(candidate).suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        analysis = _analyze_file(ctx, candidate)
        if candidate == rel:
            forward = analysis
        elif any(_uses(d, rel) for d in analysis.dependencies):
            used_by.append(candidate)
    assert forward is not None
    return DependencyResult(
        root_path=source.logical_path,
        target_file=rel,
        file_dependencies=forward,
        used_by=sorted(used_by),
    )


def analyze_dependencies(file_path: str, root: Path | None = None) -> DependencyResult:
    """Analyze a file of a local project. See ``analyze_source_dependencies``."""
    return analyze_source_dependencies(LocalRepository(root), file_path)


# --------------------------------------------------------------------------- impact

@dataclass
class ImpactEntry:
    """One file pulled into scope by a change, plus the chain that links it back."""

    file_path: str
    depth: int  # 1 = imports a changed file directly
    via: list[str] = field(default_factory=list)  # [changed_file, ..., file_path]

    def to_dict(self) -> dict[str, Any]:
        return {"file_path": self.file_path, "depth": self.depth, "via": self.via}


@dataclass
class ImpactResult:
    """Files affected by a change, found through reverse dependencies (transitively)."""

    root_path: str
    changed: list[str] = field(default_factory=list)
    affected: list[ImpactEntry] = field(default_factory=list)
    not_in_graph: list[str] = field(default_factory=list)
    max_depth: int = MAX_IMPACT_DEPTH
    truncated: bool = False
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "changed": self.changed,
            "affected": [entry.to_dict() for entry in self.affected],
            "not_in_graph": self.not_in_graph,
            "max_depth": self.max_depth,
            "truncated": self.truncated,
            "note": self.note,
        }


def _reverse_graph(source: RepositorySource) -> tuple[dict[str, set[str]], set[str]]:
    """Map each local file to the files that import it (direct edges only).

    Built in one pass: every supported file is parsed once, so a closure over many
    seeds costs the same as a single forward analysis.
    """
    ctx = _Context(source)
    reverse: dict[str, set[str]] = {}
    analysable: set[str] = set()
    for candidate in ctx.files:
        if PurePosixPath(candidate).suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        analysable.add(candidate)
        for dep in _analyze_file(ctx, candidate).dependencies:
            if not dep.is_local or not dep.resolved_path:
                continue
            path = dep.resolved_path
            if path.endswith("/"):
                # directory-level import (Go package, Java wildcard, namespace): its direct children
                for member in ctx.files:
                    if member.startswith(path) and "/" not in member[len(path):]:
                        reverse.setdefault(member, set()).add(candidate)
            else:
                reverse.setdefault(path, set()).add(candidate)
    return reverse, analysable


def analyze_source_impact(
    source: RepositorySource,
    changed_paths: list[str],
    max_depth: int = MAX_IMPACT_DEPTH,
    max_files: int = MAX_IMPACT_FILES,
) -> ImpactResult:
    """Return every file that (transitively) imports one of ``changed_paths``.

    This is the reverse-dependency closure: a change to a shared utility pulls in
    callers whose text never changed. Files outside the import graph (config, docs,
    data) are reported in ``not_in_graph`` rather than raising.
    """
    result = ImpactResult(root_path=source.logical_path, max_depth=max_depth)
    seeds: list[str] = []
    for raw in changed_paths or []:
        rel = normalize_rel_path(raw)
        if rel not in seeds:
            seeds.append(rel)
    result.changed = seeds
    if not seeds:
        result.note = "No changed files were supplied."
        return result

    reverse, analysable = _reverse_graph(source)
    result.not_in_graph = sorted(seed for seed in seeds if seed not in analysable)

    seen: set[str] = set(seeds)
    queue: list[tuple[str, int, list[str]]] = [(seed, 0, [seed]) for seed in seeds if seed in analysable]
    head = 0
    while head < len(queue):
        path, depth, via = queue[head]
        head += 1
        if depth >= max_depth:
            if reverse.get(path):
                result.truncated = True
            continue
        for caller in sorted(reverse.get(path, ())):
            if caller in seen:
                continue
            if len(result.affected) >= max_files:
                result.truncated = True
                queue = queue[:head]
                break
            seen.add(caller)
            chain = [*via, caller]
            result.affected.append(ImpactEntry(caller, depth + 1, chain))
            queue.append((caller, depth + 1, chain))

    result.affected.sort(key=lambda entry: (entry.depth, entry.file_path))
    notes: list[str] = []
    if result.truncated:
        notes.append(f"Impact search stopped at depth {max_depth} or {max_files:,} files.")
    if result.not_in_graph:
        notes.append(
            f"{len(result.not_in_graph)} changed file(s) are outside the import graph "
            "(config, docs, data) and cannot be traced to callers."
        )
    result.note = " ".join(notes)
    return result


def analyze_impact(
    changed_paths: list[str],
    root: Path | None = None,
    max_depth: int = MAX_IMPACT_DEPTH,
    max_files: int = MAX_IMPACT_FILES,
) -> ImpactResult:
    """Analyze a local project. See ``analyze_source_impact``."""
    return analyze_source_impact(LocalRepository(root), changed_paths, max_depth, max_files)

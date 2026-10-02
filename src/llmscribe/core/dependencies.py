"""Core dependency analysis functionality for LLMScribe."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .file_reader import is_text_file, TEXT_FILE_EXTENSIONS
from .tree_builder import DEFAULT_IGNORE, IgnoreMatcher, load_gitignore


@dataclass
class Dependency:
    """A single dependency relationship."""
    source_file: str
    target: str
    dependency_type: str  # "import", "require", "include", "unknown"
    line_number: int = 0
    resolved_path: str | None = None
    is_local: bool = False
    is_external: bool = False
    is_unresolved: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        result = {
            "source_file": self.source_file,
            "target": self.target,
            "dependency_type": self.dependency_type,
            "line_number": self.line_number,
            "is_local": self.is_local,
            "is_external": self.is_external,
            "is_unresolved": self.is_unresolved,
        }
        if self.resolved_path:
            result["resolved_path"] = self.resolved_path
        return result


@dataclass
class FileDependencies:
    """Dependencies for a single file."""
    file_path: str
    imports: list[str] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    local_dependencies: list[str] = field(default_factory=list)
    external_dependencies: list[str] = field(default_factory=list)
    unresolved_dependencies: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "imports": self.imports,
            "dependencies": [d.to_dict() for d in self.dependencies],
            "local_dependencies": self.local_dependencies,
            "external_dependencies": self.external_dependencies,
            "unresolved_dependencies": self.unresolved_dependencies,
        }


@dataclass
class DependencyResult:
    """Complete dependency analysis result."""
    root_path: str
    target_file: str
    file_dependencies: FileDependencies
    all_local_files: list[str] = field(default_factory=list)
    all_external_deps: list[str] = field(default_factory=list)
    all_unresolved: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "root_path": self.root_path,
            "target_file": self.target_file,
            "file_dependencies": self.file_dependencies.to_dict(),
            "all_local_files": self.all_local_files,
            "all_external_deps": self.all_external_deps,
            "all_unresolved": self.all_unresolved,
        }


class DependencyProvider:
    """Abstract base class for dependency providers."""
    
    def get_dependencies(self, file_path: str, root: Path) -> FileDependencies:
        """Get dependencies for a specific file."""
        raise NotImplementedError
    
    def get_dependents(self, file_path: str, root: Path) -> list[str]:
        """Get files that depend on the specified file."""
        raise NotImplementedError


class CodeGraphProvider(DependencyProvider):
    """CodeGraph-based dependency provider (placeholder for future integration)."""
    
    def get_dependencies(self, file_path: str, root: Path) -> FileDependencies:
        """Get dependencies using CodeGraph (not yet implemented)."""
        # For now, fall back to basic provider
        basic_provider = BasicDependencyProvider()
        return basic_provider.get_dependencies(file_path, root)
    
    def get_dependents(self, file_path: str, root: Path) -> list[str]:
        """Get dependents using CodeGraph (not yet implemented)."""
        # For now, fall back to basic provider
        basic_provider = BasicDependencyProvider()
        return basic_provider.get_dependents(file_path, root)


class BasicDependencyProvider(DependencyProvider):
    """Basic dependency provider using AST parsing for Python files."""
    
    def __init__(self):
        # Language extensions we can analyze
        self.supported_extensions = {
            '.py': self._analyze_python,
            '.js': self._analyze_javascript,
            '.ts': self._analyze_javascript,
            '.java': self._analyze_java,
            '.go': self._analyze_go,
            '.rs': self._analyze_rust,
            '.cpp': self._analyze_cpp,
            '.c': self._analyze_c,
            '.h': self._analyze_c,
            '.hpp': self._analyze_cpp,
        }
        
        # Patterns for different import styles
        self.python_import_patterns = [
            (r'from\s+([^\s]+)\s+import\s+', 'from_import'),
            (r'import\s+([^\s,]+)', 'import'),
            (r'from\s+\.([^\s]+)\s+import\s+', 'relative_import'),
            (r'import\s+\.([^\s,]+)', 'relative_import'),
        ]
        
        self.javascript_import_patterns = [
            (r'from\s+["\']([^"\']+)["\']\s+import\s+', 'from_import'),
            (r'import\s+["\']([^"\']+)["\']', 'import'),
            (r'require\(["\']([^"\']+)["\']\)', 'require'),
        ]
        
        self.java_import_patterns = [
            (r'import\s+([^;]+);', 'import'),
        ]
        
        self.go_import_patterns = [
            (r'"([^"]+)"', 'import'),
        ]
    
    def get_dependencies(self, file_path: str, root: Path) -> FileDependencies:
        """Get dependencies for a specific file using basic analysis."""
        if not file_path or not file_path.strip():
            return FileDependencies(file_path=file_path)
        
        root = root.resolve()
        target_path = (root / file_path).resolve()
        
        # Check if file exists
        if not target_path.exists():
            return FileDependencies(
                file_path=file_path,
                unresolved_dependencies=[file_path]
            )
        
        if not target_path.is_file():
            return FileDependencies(file_path=file_path)
        
        if not is_text_file(target_path):
            return FileDependencies(file_path=file_path)
        
        # Get file extension
        ext = target_path.suffix.lower()
        analyzer = self.supported_extensions.get(ext)
        
        if analyzer is None:
            # Try to find an analyzer for multi-extension files
            for supported_ext, analyze_func in self.supported_extensions.items():
                if file_path.endswith(supported_ext):
                    analyzer = analyze_func
                    break
        
        if analyzer is None:
            # Unsupported language - return empty dependencies but mark as unresolved
            return FileDependencies(
                file_path=file_path,
                unresolved_dependencies=[f"Unsupported language: {ext}"],
            )
        
        try:
            content = target_path.read_text(encoding="utf-8", errors="ignore")
            return analyzer(content, file_path, root, target_path)
        except OSError:
            return FileDependencies(file_path=file_path)
    
    def get_dependents(self, file_path: str, root: Path) -> list[str]:
        """Find files that depend on the specified file."""
        # This requires scanning all files to find imports of the target file
        # This is expensive but necessary for complete dependency analysis
        
        if not file_path or not file_path.strip():
            return []
        
        root = root.resolve()
        target_path = (root / file_path).resolve()
        
        if not target_path.exists():
            return []
        
        # Get the target file name without extension for matching
        target_stem = target_path.stem
        target_name = target_path.name
        
        # Collect all files in the project
        all_files = []
        ignore_patterns = [*DEFAULT_IGNORE, *load_gitignore(root)]
        matcher = IgnoreMatcher(root, ignore_patterns)
        
        for file_path_obj in root.rglob("*"):
            if file_path_obj.is_dir() or matcher.is_ignored(file_path_obj) or not is_text_file(file_path_obj):
                continue
            try:
                rel_path = file_path_obj.relative_to(root).as_posix()
            except ValueError:
                continue
            all_files.append((rel_path, file_path_obj))
        
        dependents = []
        target_identifiers = [target_name, target_stem, file_path]
        
        for rel_path, file_path_obj in all_files:
            if rel_path == file_path:
                continue  # Skip self
                
            ext = file_path_obj.suffix.lower()
            analyzer = self.supported_extensions.get(ext)
            
            if analyzer is None:
                continue
            
            try:
                content = file_path_obj.read_text(encoding="utf-8", errors="ignore")
                deps = analyzer(content, rel_path, root, file_path_obj)
                
                # Check if any of the dependencies match our target
                for dep in deps.dependencies:
                    if dep.target in target_identifiers:
                        dependents.append(rel_path)
                        break
                    elif dep.resolved_path and dep.resolved_path in target_identifiers:
                        dependents.append(rel_path)
                        break
            except OSError:
                continue
        
        return dependents
    
    def _analyze_python(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze Python file for dependencies."""
        result = FileDependencies(file_path=file_path)
        imports = []
        dependencies = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_name = alias.name
                        imports.append(import_name)
                        
                        dep = self._classify_dependency(import_name, file_path, root, full_path)
                        dependencies.append(dep)
                        self._categorize_dependency(result, dep)
                        
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        import_name = f"{module}.{alias.name}" if module else alias.name
                        imports.append(import_name)
                        
                        dep = self._classify_dependency(import_name, file_path, root, full_path, node.level)
                        dependencies.append(dep)
                        self._categorize_dependency(result, dep)
        except SyntaxError:
            # Fall back to regex-based analysis
            regex_deps = self._analyze_python_regex(content, file_path, root, full_path)
            result.imports.extend(regex_deps.imports)
            result.dependencies.extend(regex_deps.dependencies)
            for dep in regex_deps.dependencies:
                self._categorize_dependency(result, dep)
        
        result.imports = sorted(set(imports))
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        
        return result
    
    def _analyze_python_regex(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Regex-based Python dependency analysis as fallback."""
        result = FileDependencies(file_path=file_path)
        imports = set()
        dependencies = []
        
        for line_idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            
            for pattern, dep_type in self.python_import_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    import_name = match.group(1)
                    if import_name and not import_name.startswith('#'):
                        imports.add(import_name)
                        dep = Dependency(
                            source_file=file_path,
                            target=import_name,
                            dependency_type=dep_type,
                            line_number=line_idx,
                        )
                        
                        # Classify the dependency
                        classified_dep = self._classify_dependency(import_name, file_path, root, full_path)
                        dependencies.append(classified_dep)
                        self._categorize_dependency(result, classified_dep)
        
        result.imports = sorted(imports)
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        return result
    
    def _analyze_javascript(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze JavaScript/TypeScript file for dependencies."""
        result = FileDependencies(file_path=file_path)
        imports = set()
        dependencies = []
        
        for line_idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            
            for pattern, dep_type in self.javascript_import_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    import_name = match.group(1)
                    if import_name and not import_name.startswith('//'):
                        imports.add(import_name)
                        dep = Dependency(
                            source_file=file_path,
                            target=import_name,
                            dependency_type=dep_type,
                            line_number=line_idx,
                        )
                        
                        classified_dep = self._classify_dependency(import_name, file_path, root, full_path)
                        dependencies.append(classified_dep)
                        self._categorize_dependency(result, classified_dep)
        
        result.imports = sorted(imports)
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        return result
    
    def _analyze_java(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze Java file for dependencies."""
        result = FileDependencies(file_path=file_path)
        imports = set()
        dependencies = []
        
        for line_idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            
            for pattern, dep_type in self.java_import_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    import_name = match.group(1).strip()
                    if import_name and not import_name.startswith('//'):
                        imports.add(import_name)
                        dep = Dependency(
                            source_file=file_path,
                            target=import_name,
                            dependency_type=dep_type,
                            line_number=line_idx,
                        )
                        
                        classified_dep = self._classify_dependency(import_name, file_path, root, full_path)
                        dependencies.append(classified_dep)
                        self._categorize_dependency(result, classified_dep)
        
        result.imports = sorted(imports)
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        return result
    
    def _analyze_go(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze Go file for dependencies."""
        result = FileDependencies(file_path=file_path)
        imports = set()
        dependencies = []
        
        for line_idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            
            for pattern, dep_type in self.go_import_patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    import_name = match.group(1)
                    if import_name and not import_name.startswith('//'):
                        imports.add(import_name)
                        dep = Dependency(
                            source_file=file_path,
                            target=import_name,
                            dependency_type=dep_type,
                            line_number=line_idx,
                        )
                        
                        classified_dep = self._classify_dependency(import_name, file_path, root, full_path)
                        dependencies.append(classified_dep)
                        self._categorize_dependency(result, classified_dep)
        
        result.imports = sorted(imports)
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        return result
    
    def _analyze_c(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze C file for dependencies."""
        return self._analyze_cpp_like(content, file_path, root, full_path, r'#include\s+["<]([^">]+)[">]')
    
    def _analyze_cpp(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze C++ file for dependencies."""
        return self._analyze_cpp_like(content, file_path, root, full_path, r'#include\s+["<]([^">]+)[">]')
    
    def _analyze_rust(self, content: str, file_path: str, root: Path, full_path: Path) -> FileDependencies:
        """Analyze Rust file for dependencies."""
        result = FileDependencies(file_path=file_path)
        imports = set()
        dependencies = []
        
        # Look for use and extern crate statements
        patterns = [
            (r'use\s+([^;]+);', 'use'),
            (r'extern\s+crate\s+([^;]+);', 'extern_crate'),
            (r'mod\s+([^;]+);', 'mod'),
        ]
        
        for line_idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            
            for pattern, dep_type in patterns:
                matches = re.finditer(pattern, line)
                for match in matches:
                    import_name = match.group(1).strip()
                    if import_name and not import_name.startswith('//'):
                        imports.add(import_name)
                        dep = Dependency(
                            source_file=file_path,
                            target=import_name,
                            dependency_type=dep_type,
                            line_number=line_idx,
                        )
                        
                        classified_dep = self._classify_dependency(import_name, file_path, root, full_path)
                        dependencies.append(classified_dep)
                        self._categorize_dependency(result, classified_dep)
        
        result.imports = sorted(imports)
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        return result
    
    def _analyze_cpp_like(self, content: str, file_path: str, root: Path, full_path: Path, pattern: str) -> FileDependencies:
        """Generic C/C++-like include analyzer."""
        result = FileDependencies(file_path=file_path)
        imports = set()
        dependencies = []
        
        for line_idx, line in enumerate(content.splitlines(), start=1):
            line = line.strip()
            
            matches = re.finditer(pattern, line)
            for match in matches:
                import_name = match.group(1).strip()
                if import_name and not import_name.startswith('//'):
                    imports.add(import_name)
                    dep = Dependency(
                        source_file=file_path,
                        target=import_name,
                        dependency_type="include",
                        line_number=line_idx,
                    )
                    
                    classified_dep = self._classify_dependency(import_name, file_path, root, full_path)
                    dependencies.append(classified_dep)
                    self._categorize_dependency(result, classified_dep)
        
        result.imports = sorted(imports)
        result.dependencies = sorted(dependencies, key=lambda d: d.target)
        return result
    
    def _classify_dependency(self, import_name: str, source_file: str, root: Path, source_path: Path, relative_level: int = 0) -> Dependency:
        """Classify a dependency as local, external, or unresolved."""
        dep = Dependency(
            source_file=source_file,
            target=import_name,
            dependency_type="import",
            line_number=0,
        )
        
        # Handle relative imports
        if import_name.startswith('.'):
            # This is a relative import
            try:
                # Resolve the relative path
                relative_path = import_name.replace('.', '/')
                if relative_path.startswith('/'):
                    relative_path = relative_path[1:]
                
                # Navigate up based on relative level
                source_dir = source_path.parent
                for _ in range(relative_level):
                    source_dir = source_dir.parent
                
                resolved_path = (source_dir / relative_path).resolve()
                
                # Check if the resolved path exists
                if resolved_path.exists():
                    try:
                        rel_to_root = resolved_path.relative_to(root)
                        dep.resolved_path = rel_to_root.as_posix()
                        dep.is_local = True
                        dep.is_external = False
                        dep.is_unresolved = False
                    except ValueError:
                        # Outside root, still consider it resolved but external
                        dep.resolved_path = str(resolved_path)
                        dep.is_local = False
                        dep.is_external = True
                        dep.is_unresolved = False
                else:
                    # File doesn't exist - unresolved
                    dep.is_unresolved = True
                    dep.is_local = False
                    dep.is_external = False
            except Exception:
                dep.is_unresolved = True
                dep.is_local = False
                dep.is_external = False
            
            return dep
        
        # Handle standard library imports (Python)
        python_builtin_modules = {
            'os', 'sys', 're', 'json', 'math', 'datetime', 'collections', 'itertools',
            'functools', 'pathlib', 'typing', 'abc', 'argparse', 'copy', 'heapq',
            'bisect', 'array', 'enum', 'graphlib', 'pprint', 'random', 'statistics',
            'time', 'calendar', 'dataclasses', 'hashlib', 'hmac', 'base64', 'binascii',
            'struct', 'io', 'builtins', 'gc', 'inspect', 'dis', 'traceback',
            'warnings', 'logging', 'configparser', 'string', 'textwrap', 'unicodedata',
            'stringprep', 'difflib', 'reprlib', 'pickle', 'shelve', 'marshal',
            'contextlib', 'contextvars', 'asyncio', 'concurrent', 'multiprocessing',
            'threading', 'queue', 'sched', 'atexit', 'signal', 'mmap', 'code',
            'codeop', 'ast', 'symtable', 'token', 'keyword', 'tokenize', 'tabnanny',
            'py_compile', 'compile', 'zipimport', 'pkgutil', 'runpy', 'importlib',
            'modulefinder', 'sysconfig', 'platform', 'webbrowser', 'cgi', 'cgitb',
            'wsgiref', 'urllib', 'http', 'ftplib', 'poplib', 'imaplib', 'smtplib',
            'smtpd', 'telnetlib', 'ssl', 'socket', 'socketserver', 'xml', 'xmlrpc',
            'json', 'csv', 'sqlite3', 'dbm', 'shelve'
        }
        
        if import_name in python_builtin_modules:
            dep.is_local = False
            dep.is_external = False  # Built-in, not external
            dep.is_unresolved = False
            return dep
        
        # Check if it's a local file
        candidate_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp', '.h', '.hpp']
        
        for ext in candidate_extensions:
            # Try direct file match
            candidate_path = (source_path.parent / f"{import_name}{ext}").resolve()
            if candidate_path.exists():
                try:
                    rel_to_root = candidate_path.relative_to(root)
                    dep.resolved_path = rel_to_root.as_posix()
                    dep.is_local = True
                    dep.is_external = False
                    dep.is_unresolved = False
                    return dep
                except ValueError:
                    continue
            
            # Try directory with __init__.py
            candidate_dir = (source_path.parent / import_name).resolve()
            if candidate_dir.exists() and candidate_dir.is_dir():
                init_file = candidate_dir / f"__init__.py"
                if init_file.exists():
                    try:
                        rel_to_root = candidate_dir.relative_to(root)
                        dep.resolved_path = rel_to_root.as_posix()
                        dep.is_local = True
                        dep.is_external = False
                        dep.is_unresolved = False
                        return dep
                    except ValueError:
                        continue
        
        # Check for node_modules (JavaScript)
        if '.' not in import_name and import_name not in python_builtin_modules:
            node_modules_path = (root / "node_modules" / import_name).resolve()
            if node_modules_path.exists():
                dep.resolved_path = f"node_modules/{import_name}"
                dep.is_local = True  # Local to project
                dep.is_external = True  # But external dependency
                dep.is_unresolved = False
                return dep
        
        # Check for known external packages (this is a simplified approach)
        # For a real implementation, we'd use a more sophisticated approach
        if '.' in import_name or import_name.startswith('http://') or import_name.startswith('https://'):
            dep.is_local = False
            dep.is_external = True
            dep.is_unresolved = False
            return dep
        
        # If we can't resolve it, mark as unresolved
        dep.is_local = False
        dep.is_external = False
        dep.is_unresolved = True
        
        return dep
    
    def _categorize_dependency(self, result: FileDependencies, dep: Dependency) -> None:
        """Categorize a dependency into the appropriate list."""
        if dep.is_local and not dep.is_unresolved:
            if dep.resolved_path and dep.resolved_path not in result.local_dependencies:
                result.local_dependencies.append(dep.resolved_path)
        elif dep.is_external and not dep.is_unresolved:
            if dep.target not in result.external_dependencies:
                result.external_dependencies.append(dep.target)
        elif dep.is_unresolved:
            if dep.target not in result.unresolved_dependencies:
                result.unresolved_dependencies.append(dep.target)


# Global dependency provider instance
_dependency_provider: DependencyProvider = BasicDependencyProvider()


def set_dependency_provider(provider: DependencyProvider) -> None:
    """Set the global dependency provider."""
    global _dependency_provider
    _dependency_provider = provider


def get_dependency_provider() -> DependencyProvider:
    """Get the current dependency provider."""
    return _dependency_provider


def analyze_dependencies(file_path: str, root: Path | None = None) -> DependencyResult:
    """Analyze dependencies for a specific file.
    
    Args:
        file_path: Relative path to the file from root
        root: Project root directory (defaults to current working directory)
        
    Returns:
        DependencyResult with complete dependency analysis
    """
    if root is None:
        root = Path.cwd().resolve()
    else:
        root = root.resolve()
    
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")
    
    file_deps = _dependency_provider.get_dependencies(file_path, root)
    
    # Get dependents (files that import this file)
    dependents = _dependency_provider.get_dependents(file_path, root)
    
    # Extract all local/external/unresolved from the file dependencies
    all_local = file_deps.local_dependencies.copy()
    all_external = file_deps.external_dependencies.copy()
    all_unresolved = file_deps.unresolved_dependencies.copy()
    
    return DependencyResult(
        root_path=root.as_posix(),
        target_file=file_path,
        file_dependencies=file_deps,
        all_local_files=dependents + all_local,
        all_external_deps=all_external,
        all_unresolved=all_unresolved,
    )
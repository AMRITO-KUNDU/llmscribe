from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from llmscribe.mcp.server import (
    project_get_file,
    project_list_files,
    project_map,
    project_overview,
    project_search,
)


class MCPToolsTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Set up sample directory structure
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('hello world')\n", encoding="utf-8")
        (self.root / "src" / "utils.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
        (self.root / "README.md").write_text("# Test Project\nWelcome to test project.", encoding="utf-8")
        (self.root / "notes.txt").write_text("This is a secret note.", encoding="utf-8")
        (self.root / ".gitignore").write_text("notes.txt\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_project_overview(self) -> None:
        result = project_overview(str(self.root))
        self.assertIn("Selected Files Directory Structure:", result)
        self.assertIn("src", result)
        self.assertIn("main.py", result)
        self.assertIn("hello world", result)
        # notes.txt should be ignored via .gitignore
        self.assertNotIn("secret note", result)

    def test_project_overview_default_cwd(self) -> None:
        old_cwd = os.getcwd()
        try:
            os.chdir(self.root)
            result = project_overview()
            self.assertIn("Selected Files Directory Structure:", result)
            self.assertIn("main.py", result)
        finally:
            os.chdir(old_cwd)

    def test_project_overview_invalid_directory(self) -> None:
        result = project_overview(str(self.root / "nonexistent"))
        self.assertIn("Error building project overview", result)

    def test_project_map(self) -> None:
        result = project_map(str(self.root))
        self.assertIn("Selected Files Directory Structure:", result)
        self.assertIn("main.py", result)
        # Should not include file contents
        self.assertNotIn("hello world", result)

    def test_project_search(self) -> None:
        # Search by content keyword
        res_content = project_search("hello", str(self.root))
        self.assertIn("src/main.py", res_content)
        self.assertIn("hello world", res_content)

        # Search by filename keyword
        res_filename = project_search("utils", str(self.root))
        self.assertIn("src/utils.py", res_filename)

        # Search with no matches
        res_none = project_search("nonexistent_keyword_12345", str(self.root))
        self.assertIn("No matches found", res_none)

        # Search with empty query
        res_empty = project_search("", str(self.root))
        self.assertIn("Error", res_empty)

    def test_project_get_file(self) -> None:
        # Valid file
        result = project_get_file("src/main.py", str(self.root))
        self.assertIn("--- src/main.py ---", result)
        self.assertIn("hello world", result)

        # Nonexistent file
        res_missing = project_get_file("src/missing.py", str(self.root))
        self.assertIn("Error: File does not exist", res_missing)

        # Empty file path
        res_empty = project_get_file("", str(self.root))
        self.assertIn("Error", res_empty)

    def test_project_get_file_path_traversal_prevention(self) -> None:
        outside_file = self.root.parent / "outside.txt"
        outside_file.write_text("outside data", encoding="utf-8")
        try:
            res_traversal = project_get_file("../outside.txt", str(self.root))
            self.assertIn("Path traversal attempt detected", res_traversal)
        finally:
            if outside_file.exists():
                outside_file.unlink()

    def test_project_list_files(self) -> None:
        all_files = project_list_files(str(self.root))
        self.assertIn("README.md", all_files)
        self.assertIn("src/main.py", all_files)
        self.assertIn("src/utils.py", all_files)
        self.assertNotIn("notes.txt", all_files)

        # Filter by extension with leading dot
        py_files = project_list_files(str(self.root), extension=".py")
        self.assertIn("src/main.py", py_files)
        self.assertNotIn("README.md", py_files)

        # Filter by extension without leading dot
        py_files_no_dot = project_list_files(str(self.root), extension="py")
        self.assertIn("src/main.py", py_files_no_dot)
        self.assertNotIn("README.md", py_files_no_dot)

        # Filter with no matching extension
        no_files = project_list_files(str(self.root), extension=".cpp")
        self.assertIn("No text files found", no_files)


if __name__ == "__main__":
    unittest.main()

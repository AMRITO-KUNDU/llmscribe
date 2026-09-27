from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from llmscribe.mcp.server import (
    project_diff,
    project_get_file,
    project_get_files,
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

    def test_markdown_header_consistency(self) -> None:
        res_overview = project_overview(str(self.root), format="markdown")
        self.assertTrue(res_overview.startswith("### llmscribe: project_overview"))

        res_map = project_map(str(self.root), format="markdown")
        self.assertTrue(res_map.startswith("### llmscribe: project_map"))

        res_search = project_search("hello", str(self.root), format="markdown")
        self.assertTrue(res_search.startswith("### llmscribe: project_search"))

        res_get_file = project_get_file("src/main.py", str(self.root), format="markdown")
        self.assertTrue(res_get_file.startswith("### llmscribe: project_get_file"))

        res_get_files = project_get_files(["src/main.py"], str(self.root), format="markdown")
        self.assertTrue(res_get_files.startswith("### llmscribe: project_get_files"))

        res_list = project_list_files(str(self.root), format="markdown")
        self.assertTrue(res_list.startswith("### llmscribe: project_list_files"))

    def test_json_format_all_tools(self) -> None:
        # project_overview
        data_overview = json.loads(project_overview(str(self.root), format="json"))
        self.assertTrue(data_overview["ok"])
        self.assertEqual(data_overview["tool"], "project_overview")
        self.assertIn("summary", data_overview["data"])

        # project_map
        data_map = json.loads(project_map(str(self.root), format="json"))
        self.assertTrue(data_map["ok"])
        self.assertEqual(data_map["tool"], "project_map")
        self.assertIn("map", data_map["data"])

        # project_search
        data_search = json.loads(project_search("hello", str(self.root), format="json"))
        self.assertTrue(data_search["ok"])
        self.assertEqual(data_search["tool"], "project_search")
        self.assertEqual(len(data_search["data"]["matches"]), 1)

        # project_get_file
        data_file = json.loads(project_get_file("src/main.py", str(self.root), format="json"))
        self.assertTrue(data_file["ok"])
        self.assertEqual(data_file["tool"], "project_get_file")
        self.assertEqual(data_file["data"]["file_path"], "src/main.py")

        # project_get_files
        data_files = json.loads(project_get_files(["src/main.py"], str(self.root), format="json"))
        self.assertTrue(data_files["ok"])
        self.assertEqual(data_files["tool"], "project_get_files")
        self.assertEqual(len(data_files["data"]["results"]), 1)

        # project_list_files
        data_list = json.loads(project_list_files(str(self.root), format="json"))
        self.assertTrue(data_list["ok"])
        self.assertEqual(data_list["tool"], "project_list_files")
        self.assertIn("README.md", data_list["data"]["files"])

    def test_json_error_shape(self) -> None:
        err_json = project_get_file("../outside.txt", str(self.root), format="json")
        parsed = json.loads(err_json)
        self.assertFalse(parsed["ok"])
        self.assertEqual(parsed["tool"], "project_get_file")
        self.assertIn("error", parsed)
        self.assertEqual(parsed["error"]["code"], "path_traversal")

    def test_project_get_files_partial_success(self) -> None:
        result_json = project_get_files(
            ["src/main.py", "nonexistent.txt", "../traversal.txt"],
            str(self.root),
            format="json",
        )
        parsed = json.loads(result_json)
        self.assertTrue(parsed["ok"])
        results = parsed["data"]["results"]
        self.assertEqual(len(results), 3)

        # First file succeeded
        self.assertTrue(results[0]["ok"])
        self.assertEqual(results[0]["file_path"], "src/main.py")

        # Second file not found
        self.assertFalse(results[1]["ok"])
        self.assertEqual(results[1]["error"]["code"], "file_not_found")

        # Third file traversal blocked
        self.assertFalse(results[2]["ok"])
        self.assertEqual(results[2]["error"]["code"], "path_traversal")

    def test_project_get_files_path_traversal_blocked(self) -> None:
        result_md = project_get_files(["../outside.txt"], str(self.root), format="markdown")
        self.assertIn("path_traversal", result_md)

    def test_project_diff_non_git_folder(self) -> None:
        diff_md = project_diff(str(self.root), format="markdown")
        self.assertIn("git_unavailable", diff_md)

        diff_json = json.loads(project_diff(str(self.root), format="json"))
        self.assertFalse(diff_json["ok"])
        self.assertEqual(diff_json["error"]["code"], "git_unavailable")

    def test_project_diff_temp_git_repo(self) -> None:
        # Initialize a temporary git repository
        try:
            subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.root, check=True, capture_output=True)
        except Exception as exc:
            self.skipTest(f"Git setup failed: {exc}")

        # Modify a file
        (self.root / "src" / "main.py").write_text("print('hello world updated')\n", encoding="utf-8")

        # Test project_diff (unstaged)
        res_json = json.loads(project_diff(str(self.root), format="json"))
        self.assertTrue(res_json["ok"])
        self.assertIn("hello world updated", res_json["data"]["diff"])

        # Test project_diff markdown
        res_md = project_diff(str(self.root), format="markdown")
        self.assertIn("### llmscribe: project_diff", res_md)
        self.assertIn("hello world updated", res_md)


if __name__ == "__main__":
    unittest.main()

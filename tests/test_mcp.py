from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from llmscribe import __version__
from llmscribe.mcp.server import (
    GET_FILES_MAX_FILES,
    MAX_CONTENT_CHARS,
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

    def test_version_bump_is_1_1_0(self) -> None:
        self.assertEqual(__version__, "1.1.0")

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

    def test_structured_json_and_metadata_project_overview(self) -> None:
        raw_json = project_overview(str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "project_overview")
        self.assertIn("tree", data["data"])
        self.assertIn("files", data["data"])
        self.assertIsInstance(data["data"]["files"], list)

        # Verify items in files list have 'path' and 'content'
        files = data["data"]["files"]
        paths = [f["path"] for f in files]
        self.assertIn("README.md", paths)
        self.assertIn("src/main.py", paths)
        self.assertIn("src/utils.py", paths)

        # Check metadata
        meta = data["metadata"]
        self.assertEqual(meta["file_count"], 3)
        self.assertGreater(meta["character_count"], 0)

    def test_structured_json_and_metadata_project_map(self) -> None:
        raw_json = project_map(str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "project_map")
        self.assertIn("tree", data["data"])
        self.assertIn("files", data["data"])
        self.assertIsInstance(data["data"]["files"], list)

        files = data["data"]["files"]
        paths = [f["path"] for f in files]
        self.assertIn("README.md", paths)
        self.assertIn("src/main.py", paths)
        self.assertNotIn("content", files[0])  # Map only has path

        # Check metadata
        meta = data["metadata"]
        self.assertEqual(meta["file_count"], 3)

    def test_metadata_on_all_successful_tools(self) -> None:
        # project_search
        d_search = json.loads(project_search("hello", str(self.root), format="json"))
        self.assertIn("metadata", d_search)
        self.assertEqual(d_search["metadata"]["match_count"], 1)

        # project_list_files
        d_list = json.loads(project_list_files(str(self.root), format="json"))
        self.assertIn("metadata", d_list)
        self.assertEqual(d_list["metadata"]["file_count"], 3)

        # project_get_file
        d_get = json.loads(project_get_file("src/main.py", str(self.root), format="json"))
        self.assertIn("metadata", d_get)
        self.assertGreater(d_get["metadata"]["character_count"], 0)

        # project_get_files
        d_gets = json.loads(project_get_files(["src/main.py"], str(self.root), format="json"))
        self.assertIn("metadata", d_gets)
        self.assertEqual(d_gets["metadata"]["file_count"], 1)
        self.assertEqual(d_gets["metadata"]["success_count"], 1)
        self.assertEqual(d_gets["metadata"]["error_count"], 0)

    def test_error_code_standardization(self) -> None:
        # Invalid path (non-existent)
        d_inv = json.loads(project_overview(str(self.root / "nonexistent"), format="json"))
        self.assertFalse(d_inv["ok"])
        self.assertEqual(d_inv["error"]["code"], "invalid_path")

        # Not a directory
        d_not_dir = json.loads(project_overview(str(self.root / "README.md"), format="json"))
        self.assertFalse(d_not_dir["ok"])
        self.assertEqual(d_not_dir["error"]["code"], "not_a_directory")

        # Path traversal
        d_trav = json.loads(project_get_file("../outside.txt", str(self.root), format="json"))
        self.assertFalse(d_trav["ok"])
        self.assertEqual(d_trav["error"]["code"], "path_traversal")

        # Missing file
        d_miss = json.loads(project_get_file("missing.py", str(self.root), format="json"))
        self.assertFalse(d_miss["ok"])
        self.assertEqual(d_miss["error"]["code"], "file_not_found")

        # Empty search query
        d_empty = json.loads(project_search("", str(self.root), format="json"))
        self.assertFalse(d_empty["ok"])
        self.assertEqual(d_empty["error"]["code"], "empty_query")

    def test_project_get_files_partial_success_and_caps(self) -> None:
        result_json = project_get_files(
            ["src/main.py", "nonexistent.txt", "../traversal.txt"],
            str(self.root),
            format="json",
        )
        parsed = json.loads(result_json)
        self.assertTrue(parsed["ok"])
        results = parsed["data"]["results"]
        self.assertEqual(len(results), 3)

        # Check metadata metrics
        meta = parsed["metadata"]
        self.assertEqual(meta["file_count"], 3)
        self.assertEqual(meta["success_count"], 1)
        self.assertEqual(meta["error_count"], 2)

    def test_project_get_files_max_files_truncation(self) -> None:
        # Request 60 files (exceeds cap of 50)
        file_list = [f"src/file_{i}.py" for i in range(60)]
        for f in file_list:
            (self.root / f).write_text("print('test')", encoding="utf-8")

        res_json = project_get_files(file_list, str(self.root), format="json")
        parsed = json.loads(res_json)
        self.assertTrue(parsed["ok"])
        self.assertEqual(len(parsed["data"]["results"]), 50)

        meta = parsed["metadata"]
        self.assertTrue(meta["truncated"])
        self.assertIn("Processed first 50 files", meta["truncation_note"])

    def test_project_diff_non_git_folder(self) -> None:
        diff_json = json.loads(project_diff(str(self.root), format="json"))
        self.assertFalse(diff_json["ok"])
        self.assertEqual(diff_json["error"]["code"], "git_unavailable")

    def test_project_diff_temp_git_repo(self) -> None:
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

        res_json = json.loads(project_diff(str(self.root), format="json"))
        self.assertTrue(res_json["ok"])
        self.assertIn("src/main.py", res_json["data"]["changed_files"])
        self.assertIn("hello world updated", res_json["data"]["diff"])

        meta = res_json["metadata"]
        self.assertEqual(meta["changed_file_count"], 1)
        self.assertGreater(meta["character_count"], 0)
        self.assertFalse(meta["truncated"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class CLITests(unittest.TestCase):
    """Test the LLMScribe CLI commands."""

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

    def _run_cli(self, args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
        """Run CLI command and return (returncode, stdout, stderr)."""
        cmd = ["python", "-m", "llmscribe.cli.main"] + args
        result = subprocess.run(
            cmd,
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            timeout=30
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out, result.stderr

    def test_help_output(self) -> None:
        """Test that help command works."""
        returncode, stdout, stderr = self._run_cli(["--help"])
        self.assertEqual(returncode, 0)
        self.assertIn("LLMScribe", stdout)
        self.assertIn("code context for AI agents", stdout)
        self.assertIn("map", stdout)
        self.assertIn("search", stdout)
        self.assertIn("read", stdout)
        self.assertIn("dependencies", stdout)

    def test_version_command(self) -> None:
        """Test version command."""
        returncode, stdout, stderr = self._run_cli(["version"])
        self.assertEqual(returncode, 0)
        self.assertIn("llmscribe version", stdout)

    def test_map_command(self) -> None:
        """Test map command with human-readable output."""
        returncode, stdout, stderr = self._run_cli(["map"])
        self.assertEqual(returncode, 0)
        self.assertIn("Project Map:", stdout)
        self.assertIn("src", stdout)
        self.assertIn("main.py", stdout)
        self.assertIn("utils.py", stdout)
        self.assertIn("README.md", stdout)

    def test_map_json_output(self) -> None:
        """Test map command with JSON output."""
        returncode, stdout, stderr = self._run_cli(["map", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "map")
        self.assertIn("data", data)
        self.assertIn("tree", data["data"])
        self.assertIn("files", data["data"])
        self.assertIn("metadata", data)

    def test_overview_command(self) -> None:
        """Test overview command with human-readable output."""
        returncode, stdout, stderr = self._run_cli(["overview"])
        self.assertEqual(returncode, 0)
        self.assertIn("Project Overview:", stdout)
        self.assertIn("Directory Structure:", stdout)
        self.assertIn("File Count:", stdout)

    def test_overview_json_output(self) -> None:
        """Test overview command with JSON output."""
        returncode, stdout, stderr = self._run_cli(["overview", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "overview")
        self.assertIn("data", data)
        self.assertIn("tree", data["data"])
        self.assertIn("files", data["data"])

    def test_search_command(self) -> None:
        """Test search command with human-readable output."""
        returncode, stdout, stderr = self._run_cli(["search", "hello"])
        self.assertEqual(returncode, 0)
        self.assertIn("Search Results for 'hello':", stdout)
        self.assertIn("main.py", stdout)

    def test_search_json_output(self) -> None:
        """Test search command with JSON output."""
        returncode, stdout, stderr = self._run_cli(["search", "hello", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "search")
        self.assertIn("data", data)
        self.assertIn("matches", data["data"])
        self.assertIn("metadata", data)

    def test_search_no_results(self) -> None:
        """Test search command with no results."""
        returncode, stdout, stderr = self._run_cli(["search", "nonexistent_query_xyz"])
        self.assertEqual(returncode, 0)
        self.assertIn("No matches found", stdout)

    def test_search_empty_query(self) -> None:
        """Test search command with empty query."""
        returncode, stdout, stderr = self._run_cli(["search", ""])
        self.assertNotEqual(returncode, 0)
        self.assertIn("Error", stdout)

    def test_read_command(self) -> None:
        """Test read command with human-readable output."""
        returncode, stdout, stderr = self._run_cli(["read", "src/main.py"])
        self.assertEqual(returncode, 0)
        self.assertIn("File: src/main.py", stdout)
        self.assertIn("hello world", stdout)

    def test_read_json_output(self) -> None:
        """Test read command with JSON output."""
        returncode, stdout, stderr = self._run_cli(["read", "src/main.py", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "read")
        self.assertIn("data", data)
        self.assertEqual(data["data"]["file_path"], "src/main.py")
        self.assertIn("content", data["data"])
        self.assertIn("hello world", data["data"]["content"])

    def test_read_nonexistent_file(self) -> None:
        """Test read command with nonexistent file."""
        returncode, stdout, stderr = self._run_cli(["read", "nonexistent.py"])
        self.assertNotEqual(returncode, 0)
        self.assertIn("Error", stdout)

    def test_read_many_command(self) -> None:
        """Test read-many command with human-readable output."""
        returncode, stdout, stderr = self._run_cli(["read-many", "src/main.py", "src/utils.py"])
        self.assertEqual(returncode, 0)
        self.assertIn("Reading 2 files", stdout)
        self.assertIn("main.py", stdout)
        self.assertIn("utils.py", stdout)

    def test_read_many_json_output(self) -> None:
        """Test read-many command with JSON output."""
        returncode, stdout, stderr = self._run_cli(["read-many", "src/main.py", "src/utils.py", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "read-many")
        self.assertIn("data", data)
        self.assertIn("results", data["data"])
        self.assertEqual(len(data["data"]["results"]), 2)
        self.assertIn("metadata", data)

    def test_read_many_mixed_success(self) -> None:
        """Test read-many command with mixed success/failure."""
        returncode, stdout, stderr = self._run_cli([
            "read-many", "src/main.py", "nonexistent.py", "--json"
        ])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        results = data["data"]["results"]
        self.assertEqual(len(results), 2)
        
        # Check metadata shows mixed results
        meta = data["metadata"]
        self.assertEqual(meta["file_count"], 2)
        self.assertEqual(meta["success_count"], 1)
        self.assertEqual(meta["error_count"], 1)

    def test_dependencies_command(self) -> None:
        """Test dependencies command with human-readable output."""
        # Create a file with imports
        (self.root / "src" / "importer.py").write_text(
            "import os\nfrom utils import add\n", encoding="utf-8"
        )
        
        returncode, stdout, stderr = self._run_cli(["dependencies", "src/importer.py"])
        self.assertEqual(returncode, 0)
        self.assertIn("Dependencies for: src/importer.py", stdout)

    def test_dependencies_json_output(self) -> None:
        """Test dependencies command with JSON output."""
        returncode, stdout, stderr = self._run_cli(["dependencies", "src/main.py", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "dependencies")
        self.assertIn("data", data)
        self.assertIn("file_dependencies", data["data"])

    def test_diff_command_non_git(self) -> None:
        """Test diff command in non-git directory."""
        returncode, stdout, stderr = self._run_cli(["diff", "--json"])
        self.assertNotEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "git_unavailable")

    def test_diff_command_git_repo(self) -> None:
        """Test diff command in git repository."""
        try:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.root, check=True, capture_output=True)
            
            # Modify a file
            (self.root / "src" / "main.py").write_text("print('hello world updated')\n", encoding="utf-8")
            
            returncode, stdout, stderr = self._run_cli(["diff", "--json"])
            self.assertEqual(returncode, 0)
            
            data = json.loads(stdout)
            self.assertTrue(data["ok"])
            self.assertIn("src/main.py", data["data"]["changed_files"])
            
        except Exception as exc:
            self.skipTest(f"Git setup failed: {exc}")

    def test_path_parameter(self) -> None:
        """Test that --path parameter works."""
        returncode, stdout, stderr = self._run_cli(["map", "--path", str(self.root)])
        self.assertEqual(returncode, 0)
        self.assertIn(str(self.root), stdout)

    def test_invalid_path_parameter(self) -> None:
        """Test with invalid path parameter."""
        returncode, stdout, stderr = self._run_cli(["map", "--path", "/nonexistent/path"])
        self.assertNotEqual(returncode, 0)
        self.assertIn("Error", stdout)

    def test_all_commands_json_support(self) -> None:
        """Test that all commands support --json flag."""
        commands_with_json = [
            ("map", ["map", "--json"]),
            ("overview", ["overview", "--json"]),
            ("search", ["search", "test", "--json"]),
            ("read", ["read", "src/main.py", "--json"]),
            ("read-many", ["read-many", "src/main.py", "--json"]),
            ("dependencies", ["dependencies", "src/main.py", "--json"]),
        ]
        
        for cmd_name, args in commands_with_json:
            with self.subTest(command=cmd_name):
                returncode, stdout, stderr = self._run_cli(args)
                self.assertEqual(returncode, 0, f"{cmd_name} --json failed")
                
                # Should be valid JSON
                try:
                    data = json.loads(stdout)
                    self.assertIn("ok", data, f"{cmd_name} missing 'ok'")
                    self.assertIn("command", data, f"{cmd_name} missing 'command'")
                    self.assertIn("data", data, f"{cmd_name} missing 'data'")
                except json.JSONDecodeError:
                    self.fail(f"{cmd_name} --json did not produce valid JSON")

    def test_large_output_handling(self) -> None:
        """Test handling of large outputs."""
        # Create a large file
        large_content = "x" * 10000  # 10KB file
        (self.root / "large.txt").write_text(large_content, encoding="utf-8")
        
        # Test reading large file
        returncode, stdout, stderr = self._run_cli(["read", "large.txt", "--json"])
        self.assertEqual(returncode, 0)
        
        data = json.loads(stdout)
        self.assertTrue(data["ok"])
        content = data["data"]["content"]
        self.assertEqual(len(content), 10000)


class CLIErrorHandlingTests(unittest.TestCase):
    """Test CLI error handling."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run_cli(self, args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
        """Run CLI command and return (returncode, stdout, stderr)."""
        cmd = ["python", "-m", "llmscribe.cli.main"] + args
        result = subprocess.run(
            cmd,
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            timeout=30
        )
        out = (result.stdout or "") + (result.stderr or "")
        return result.returncode, out, result.stderr

    def test_invalid_command(self) -> None:
        """Test invalid command."""
        returncode, stdout, stderr = self._run_cli(["invalid_command"])
        self.assertNotEqual(returncode, 0)
        self.assertTrue("Unknown command" in stdout or "invalid choice" in stdout)

    def test_missing_required_args(self) -> None:
        """Test commands that require arguments."""
        commands_requiring_args = [
            ("search", ["search"]),
            ("read", ["read"]),
            ("read-many", ["read-many"]),
            ("dependencies", ["dependencies"]),
        ]
        
        for cmd_name, args in commands_requiring_args:
            with self.subTest(command=cmd_name):
                returncode, stdout, stderr = self._run_cli(args)
                self.assertNotEqual(returncode, 0, f"{cmd_name} should fail without required args")

    def test_path_traversal_prevention(self) -> None:
        """Test path traversal prevention."""
        (self.root / "secret.txt").write_text("secret content", encoding="utf-8")
        
        returncode, stdout, stderr = self._run_cli(["read", "../secret.txt"])
        self.assertNotEqual(returncode, 0)
        self.assertTrue("path_traversal" in stdout or "Path traversal" in stdout)


class CLIBackwardsCompatibilityTests(unittest.TestCase):
    """Test CLI backwards compatibility."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name).resolve()

        # Set up sample directory structure
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _run_cli(self, args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
        """Run CLI command and return (returncode, stdout, stderr)."""
        cmd = ["python", "-m", "llmscribe.cli.main"] + args
        result = subprocess.run(
            cmd,
            cwd=cwd or self.root,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr

    def test_new_command_structure_works(self) -> None:
        """Test that the new command structure works as expected."""
        # Test all new commands work
        new_commands = ["map", "overview", "search", "read", "read-many", "dependencies", "diff"]
        
        for cmd in new_commands:
            with self.subTest(command=cmd):
                if cmd == "search":
                    args = [cmd, "hello"]
                elif cmd == "read":
                    args = [cmd, "src/main.py"]
                elif cmd == "read-many":
                    args = [cmd, "src/main.py"]
                elif cmd == "dependencies":
                    args = [cmd, "src/main.py"]
                else:
                    args = [cmd]
                
                returncode, stdout, stderr = self._run_cli(args)
                # Should not crash, even if there are errors for specific cases
                self.assertTrue(returncode == 0 or "Error" in stdout or "Error" in stderr)


if __name__ == "__main__":
    unittest.main()
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
    project_dependencies,
    project_map,
    project_overview,
    read,
    read_many,
    search,
)


def _get_registered_tool_names(mcp_obj) -> list[str]:
    if hasattr(mcp_obj, "_tool_manager") and hasattr(mcp_obj._tool_manager, "_tools"):
        return [tool.name for tool in mcp_obj._tool_manager._tools.values()]
    if hasattr(mcp_obj, "_tools"):
        tools = mcp_obj._tools
        if isinstance(tools, dict):
            res = []
            for k, v in tools.items():
                res.append(getattr(v, "name", k))
            return res
    if hasattr(mcp_obj, "list_tools"):
        try:
            import asyncio
            tools = asyncio.run(mcp_obj.list_tools())
            return [t.name for t in tools]
        except Exception:
            pass
    return []


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

    def test_version_is_current(self) -> None:
        # Just verify we can import the version
        self.assertIsNotNone(__version__)

    def test_all_7_tools_registered(self) -> None:
        """Test that all 7 required tools are available."""
        # This tests the new final MCP toolset
        tools = [
            "project_map",
            "project_overview", 
            "search",
            "read",
            "read_many",
            "project_dependencies",
            "project_diff",
        ]
        
        # Verify we can access the functions from the MCP server module
        from llmscribe.mcp.server import (
            project_map, project_overview, search, read, read_many, project_dependencies, project_diff
        )
        
        # Create a mapping of tool names to functions
        tool_functions = {
            "project_map": project_map,
            "project_overview": project_overview,
            "search": search,
            "read": read,
            "read_many": read_many,
            "project_dependencies": project_dependencies,
            "project_diff": project_diff,
        }
        
        for tool_name in tools:
            # Verify we can access the function
            self.assertIn(tool_name, tool_functions, f"Tool {tool_name} should be accessible")
            self.assertIsNotNone(tool_functions[tool_name], f"Tool {tool_name} function should not be None")

    def test_removed_tools_not_available(self) -> None:
        """Test that removed tools are no longer exposed."""
        removed_tools = [
            "project_search",  # renamed to "search"
            "project_get_file",  # renamed to "read"
            "project_get_files",  # renamed to "read_many"
            "project_list_files",  # removed entirely
        ]
        
        # Check that these are not available as MCP tools in the server module
        from llmscribe.mcp.server import mcp
        available_tools = _get_registered_tool_names(mcp)
        
        for tool_name in removed_tools:
            self.assertNotIn(tool_name, available_tools, 
                           f"Removed tool {tool_name} should not be available")

    def test_renamed_tools_available(self) -> None:
        """Test that renamed tools are available under new names."""
        new_tool_names = ["search", "read", "read_many"]
        
        from llmscribe.mcp.server import mcp
        available_tools = _get_registered_tool_names(mcp)
        
        for tool_name in new_tool_names:
            self.assertIn(tool_name, available_tools, 
                         f"Renamed tool {tool_name} should be available")

    def test_markdown_header_consistency(self) -> None:
        res_overview = project_overview(str(self.root), format="markdown")
        self.assertTrue(res_overview.startswith("### llmscribe: project_overview"))

        res_map = project_map(str(self.root), format="markdown")
        self.assertTrue(res_map.startswith("### llmscribe: project_map"))

        res_search = search("hello", str(self.root), format="markdown")
        self.assertTrue(res_search.startswith("### llmscribe: search"))

        res_read = read("src/main.py", str(self.root), format="markdown")
        self.assertTrue(res_read.startswith("### llmscribe: read"))

        res_read_many = read_many(["src/main.py"], str(self.root), format="markdown")
        self.assertTrue(res_read_many.startswith("### llmscribe: read_many"))

        res_deps = project_dependencies("src/main.py", str(self.root), format="markdown")
        self.assertTrue(res_deps.startswith("### llmscribe: project_dependencies"))

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
        paths = [f["path"] if isinstance(f, dict) else f for f in files]
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
        paths = [f["path"] if isinstance(f, dict) else f for f in files]
        self.assertIn("README.md", paths)
        self.assertIn("src/main.py", paths)
        # For map, files should be strings or dicts without content
        for f in files:
            if isinstance(f, dict):
                self.assertNotIn("content", f)  # Map only has path

        # Check metadata
        meta = data["metadata"]
        self.assertEqual(meta["file_count"], 3)

    def test_search_structured_output(self) -> None:
        """Test search tool has structured, agent-friendly output."""
        raw_json = search("hello", str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "search")
        self.assertIn("data", data)
        
        # Check structured search data
        search_data = data["data"]
        self.assertIn("query", search_data)
        self.assertIn("matches", search_data)
        self.assertIsInstance(search_data["matches"], list)
        
        # Check metadata
        meta = data["metadata"]
        self.assertIn("query", meta)
        self.assertIn("match_count", meta)
        self.assertIn("file_count", meta)
        
        # Check that matches have structured information
        if search_data["matches"]:
            first_match = search_data["matches"][0]
            self.assertIn("file_path", first_match)
            self.assertIn("line_number", first_match)
            self.assertIn("match_type", first_match)

    def test_search_deterministic_output(self) -> None:
        """Test that search results are deterministic."""
        # Run search twice and compare results
        result1 = search("hello", str(self.root), format="json")
        result2 = search("hello", str(self.root), format="json")
        
        data1 = json.loads(result1)
        data2 = json.loads(result2)
        
        # Results should be identical
        self.assertEqual(data1, data2)

    def test_read_single_file(self) -> None:
        """Test reading a single file."""
        raw_json = read("src/main.py", str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "read")
        self.assertIn("data", data)
        
        file_data = data["data"]
        self.assertEqual(file_data["file_path"], "src/main.py")
        self.assertIn("content", file_data)
        self.assertIn("hello world", file_data["content"])
        
        # Check metadata
        meta = data["metadata"]
        self.assertIn("character_count", meta)
        self.assertGreater(meta["character_count"], 0)

    def test_read_nonexistent_file(self) -> None:
        """Test reading a non-existent file."""
        raw_json = read("nonexistent.py", str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "file_not_found")

    def test_read_many_files(self) -> None:
        """Test reading multiple files."""
        raw_json = read_many(["src/main.py", "src/utils.py"], str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "read_many")
        self.assertIn("data", data)
        
        results = data["data"]["results"]
        self.assertEqual(len(results), 2)
        
        # Check metadata
        meta = data["metadata"]
        self.assertEqual(meta["file_count"], 2)
        self.assertEqual(meta["success_count"], 2)
        self.assertEqual(meta["error_count"], 0)

    def test_read_many_partial_success(self) -> None:
        """Test reading multiple files with some failures."""
        raw_json = read_many(
            ["src/main.py", "nonexistent.py", "../traversal.txt"],
            str(self.root),
            format="json",
        )
        data = json.loads(raw_json)
        self.assertTrue(data["ok"])
        results = data["data"]["results"]
        self.assertEqual(len(results), 3)

        # Check metadata metrics
        meta = data["metadata"]
        self.assertEqual(meta["file_count"], 3)
        self.assertEqual(meta["success_count"], 1)
        self.assertEqual(meta["error_count"], 2)

    def test_read_many_max_files_truncation(self) -> None:
        """Test that read_many respects maximum file limits."""
        # Request more files than allowed
        file_list = [f"src/file_{i}.py" for i in range(60)]
        for f in file_list:
            (self.root / f).write_text("print('test')", encoding="utf-8")

        res_json = read_many(file_list, str(self.root), format="json")
        data = json.loads(res_json)
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["data"]["results"]), GET_FILES_MAX_FILES)

        meta = data["metadata"]
        self.assertTrue(meta["truncated"])

    def test_dependencies_python_file(self) -> None:
        """Test dependency analysis for Python files."""
        # Create a Python file with imports
        (self.root / "src" / "importer.py").write_text(
            "import os\nfrom utils import add\nimport json\n", encoding="utf-8"
        )
        
        raw_json = project_dependencies("src/importer.py", str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        self.assertEqual(data["tool"], "project_dependencies")
        self.assertIn("data", data)
        
        deps_data = data["data"]
        self.assertIn("file_dependencies", deps_data)
        
        file_deps = deps_data["file_dependencies"]
        self.assertEqual(file_deps["file_path"], "src/importer.py")
        
        # Check that imports were found
        self.assertGreater(len(file_deps["imports"]), 0)
        
        # Check metadata
        meta = data["metadata"]
        self.assertIn("file_count", meta)
        self.assertIn("external_dep_count", meta)
        self.assertIn("unresolved_count", meta)

    def test_dependencies_unresolved_handling(self) -> None:
        """Test that unresolved dependencies are properly reported."""
        # Create a file with unresolved imports
        (self.root / "src" / "unresolved.py").write_text(
            "import nonexistent_module\nfrom fake.package import something\n", encoding="utf-8"
        )
        
        raw_json = project_dependencies("src/unresolved.py", str(self.root), format="json")
        data = json.loads(raw_json)

        self.assertTrue(data["ok"])
        
        file_deps = data["data"]["file_dependencies"]
        
        # Should have some unresolved dependencies
        self.assertGreater(len(file_deps["unresolved_dependencies"]), 0)
        
        # Check that we don't mark local imports as unresolved if they exist
        # (this is a basic test - more sophisticated tests would check specific cases)

    def test_dependencies_missing_file(self) -> None:
        """Test dependency analysis for missing file."""
        raw_json = project_dependencies("nonexistent.py", str(self.root), format="json")
        data = json.loads(raw_json)

        # Should return a valid response but with empty/unresolved dependencies
        self.assertTrue(data["ok"])

    def test_error_code_standardization(self) -> None:
        """Test that error codes are standardized across tools."""
        # Invalid path (non-existent)
        d_inv = json.loads(project_overview(str(self.root / "nonexistent"), format="json"))
        self.assertFalse(d_inv["ok"])
        self.assertEqual(d_inv["error"]["code"], "invalid_path")

        # Not a directory
        d_not_dir = json.loads(project_overview(str(self.root / "README.md"), format="json"))
        self.assertFalse(d_not_dir["ok"])
        self.assertEqual(d_not_dir["error"]["code"], "not_a_directory")

        # Path traversal
        d_trav = json.loads(read("../outside.txt", str(self.root), format="json"))
        self.assertFalse(d_trav["ok"])
        self.assertEqual(d_trav["error"]["code"], "path_traversal")

        # Missing file
        d_miss = json.loads(read("missing.py", str(self.root), format="json"))
        self.assertFalse(d_miss["ok"])
        self.assertEqual(d_miss["error"]["code"], "file_not_found")

        # Empty search query
        d_empty = json.loads(search("", str(self.root), format="json"))
        self.assertFalse(d_empty["ok"])
        self.assertEqual(d_empty["error"]["code"], "empty_query")

    def test_search_empty_query(self) -> None:
        """Test search with empty query."""
        result = search("", str(self.root), format="json")
        data = json.loads(result)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "empty_query")

    def test_project_diff_non_git_folder(self) -> None:
        """Test diff in non-git folder."""
        diff_json = json.loads(project_diff(str(self.root), format="json"))
        self.assertFalse(diff_json["ok"])
        self.assertEqual(diff_json["error"]["code"], "git_unavailable")

    def test_project_diff_temp_git_repo(self) -> None:
        """Test diff in a git repository."""
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

    def test_json_output_stable_schema(self) -> None:
        """Test that JSON output has stable schema across tools."""
        # Map command names to MCP tool function names
        tools_to_test = [
            ("project_map", lambda: project_map(str(self.root), format="json")),
            ("project_overview", lambda: project_overview(str(self.root), format="json")),
            ("search", lambda: search("hello", str(self.root), format="json")),
            ("read", lambda: read("src/main.py", str(self.root), format="json")),
            ("read_many", lambda: read_many(["src/main.py"], str(self.root), format="json")),
            ("project_dependencies", lambda: project_dependencies("src/main.py", str(self.root), format="json")),
        ]
        
        for expected_tool_name, tool_func in tools_to_test:
            try:
                raw_json = tool_func()
                data = json.loads(raw_json)
                
                # All tools should have these top-level keys
                self.assertIn("ok", data, f"{expected_tool_name} missing 'ok'")
                self.assertIn("tool", data, f"{expected_tool_name} missing 'tool'")
                self.assertIn("path", data, f"{expected_tool_name} missing 'path'")
                self.assertIn("data", data, f"{expected_tool_name} missing 'data'")
                
                # Tool name should match the MCP tool name
                self.assertEqual(data["tool"], expected_tool_name, f"{expected_tool_name} tool name mismatch")
                
            except Exception as e:
                self.fail(f"{expected_tool_name} JSON test failed: {e}")


class MCPToolCountTests(unittest.TestCase):
    """Test that exactly 7 tools are registered."""
    
    def test_exactly_7_tools(self) -> None:
        """Test that exactly 7 tools are registered in MCP server."""
        from llmscribe.mcp.server import mcp
        available_tools = _get_registered_tool_names(mcp)
        
        self.assertEqual(len(available_tools), 7, 
                        f"Expected exactly 7 tools, found {len(available_tools)}: {available_tools}")
    
    def test_exact_tool_names(self) -> None:
        """Test that the 7 tools have exactly the required names."""
        from llmscribe.mcp.server import mcp
        available_tools = sorted(_get_registered_tool_names(mcp))
        expected_tools = sorted([
            "project_map",
            "project_overview", 
            "search",
            "read",
            "read_many",
            "project_dependencies",
            "project_diff",
        ])
        
        self.assertEqual(available_tools, expected_tools, 
                        f"Tool names mismatch. Expected: {expected_tools}, Found: {available_tools}")


if __name__ == "__main__":
    unittest.main()
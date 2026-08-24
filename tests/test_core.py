from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from llmscribe import __version__
from llmscribe.core import IgnoreMatcher, build_project_summary, load_gitignore


class CoreTests(unittest.TestCase):
    def test_version_is_exposed(self) -> None:
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")

    def test_gitignore_supports_globs_negation_and_anchoring(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitignore").write_text(
                "*.tmp\n!keep.tmp\n/root-only.txt\nnested/*.txt\n",
                encoding="utf-8",
            )
            (root / "drop.tmp").write_text("drop", encoding="utf-8")
            (root / "keep.tmp").write_text("keep", encoding="utf-8")
            (root / "root-only.txt").write_text("hidden", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "hidden.txt").write_text("hidden", encoding="utf-8")
            (nested / "visible.py").write_text("print(1)", encoding="utf-8")

            matcher = IgnoreMatcher(root, load_gitignore(root))
            self.assertTrue(matcher.is_ignored(root / "drop.tmp"))
            self.assertFalse(matcher.is_ignored(root / "keep.tmp"))
            self.assertTrue(matcher.is_ignored(root / "root-only.txt"))
            self.assertTrue(matcher.is_ignored(nested / "hidden.txt"))
            self.assertFalse(matcher.is_ignored(nested / "visible.py"))

            summary = build_project_summary(root)
            self.assertNotIn("drop.tmp", summary)
            self.assertIn("keep.tmp", summary)
            self.assertNotIn("hidden.txt", summary)
            self.assertIn("visible.py", summary)

    def test_unreadable_directory_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            unreadable = root / "unreadable"
            unreadable.mkdir()

            # Exercise the reporting path without depending on platform ACLs.
            from unittest.mock import patch
            from llmscribe.core.tree_builder import generate_tree

            original_iterdir = Path.iterdir

            def fake_iterdir(path: Path):
                if path == unreadable:
                    raise PermissionError("denied")
                return original_iterdir(path)

            with patch.object(Path, "iterdir", fake_iterdir):
                tree = generate_tree(root, {"unreadable"})
            self.assertIn(root.name, tree)


if __name__ == "__main__":
    unittest.main()

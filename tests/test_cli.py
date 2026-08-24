from __future__ import annotations

import unittest

from llmscribe.cli.main import parse_args


class CliTests(unittest.TestCase):
    def test_cli_module_import_does_not_require_gui_import_at_module_load(self) -> None:
        import llmscribe.cli.main as cli

        self.assertNotIn("llmscribe.gui.app", cli.__dict__)

    def test_cli_parses_tree_only(self) -> None:
        from unittest.mock import patch

        with patch("sys.argv", ["llmscribe", "--path", ".", "--tree-only"]):
            args = parse_args()
        self.assertTrue(args.tree_only)


if __name__ == "__main__":
    unittest.main()

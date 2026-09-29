from __future__ import annotations

import io
import json
import unittest
import urllib.error
import zipfile
from unittest.mock import MagicMock, patch

from llmscribe.github.client import (
    GitHubError,
    GitHubSnapshot,
    _make_request,
    fetch_github_diff,
    fetch_github_snapshot,
    parse_github_repo,
)
from llmscribe.mcp.server import (
    project_get_file,
    project_map,
    project_overview,
    project_search,
)


def create_sample_zipball() -> bytes:
    """Create a sample zipball archive buffer in memory."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("owner-repo-12345/README.md", "# GitHub Test Repo\n")
        zf.writestr("owner-repo-12345/src/main.py", "print('hello from github')\n")
        zf.writestr("owner-repo-12345/.gitignore", "ignored.txt\n")
        zf.writestr("owner-repo-12345/ignored.txt", "secret\n")
    return buf.getvalue()


class GitHubClientTests(unittest.TestCase):

    def test_parse_github_repo_valid_inputs(self) -> None:
        self.assertEqual(parse_github_repo("owner/repo"), ("owner", "repo"))
        self.assertEqual(parse_github_repo("AMRITO-KUNDU/llmscribe"), ("AMRITO-KUNDU", "llmscribe"))
        self.assertEqual(parse_github_repo("https://github.com/owner/repo"), ("owner", "repo"))
        self.assertEqual(parse_github_repo("https://github.com/owner/repo.git"), ("owner", "repo"))
        self.assertEqual(parse_github_repo("git@github.com:owner/repo.git"), ("owner", "repo"))

    def test_parse_github_repo_invalid_inputs(self) -> None:
        with self.assertRaises(GitHubError) as ctx:
            parse_github_repo("invalid")
        self.assertEqual(ctx.exception.code, "invalid_argument")

        with self.assertRaises(GitHubError) as ctx:
            parse_github_repo("https://invalid-domain.com/owner/repo")
        self.assertEqual(ctx.exception.code, "invalid_argument")

    @patch("urllib.request.urlopen")
    def test_fetch_github_snapshot_success(self, mock_urlopen: MagicMock) -> None:
        sample_zip = create_sample_zipball()
        mock_response = MagicMock()
        mock_response.read.return_value = sample_zip
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        snapshot = fetch_github_snapshot("owner", "repo", "main")
        self.assertEqual(snapshot.logical_path, "github.com/owner/repo@main")
        self.assertIn("README.md", snapshot.files)
        self.assertIn("src/main.py", snapshot.files)
        self.assertEqual(snapshot.get_text_content("src/main.py"), "print('hello from github')\n")
        self.assertEqual(snapshot.load_gitignore(), ["ignored.txt"])

    @patch("urllib.request.urlopen")
    def test_error_translation_http_errors(self, mock_urlopen: MagicMock) -> None:
        # HTTP 404
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://api.github.com", code=404, msg="Not Found", hdrs={}, fp=None
        )
        with self.assertRaises(GitHubError) as ctx:
            _make_request("http://api.github.com")
        self.assertEqual(ctx.exception.code, "repo_not_found")

        # HTTP 401
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://api.github.com", code=401, msg="Unauthorized", hdrs={}, fp=None
        )
        with self.assertRaises(GitHubError) as ctx:
            _make_request("http://api.github.com")
        self.assertEqual(ctx.exception.code, "auth_required")

        # HTTP 403 Rate limit
        headers = {"x-ratelimit-remaining": "0"}
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://api.github.com", code=403, msg="Forbidden", hdrs=headers, fp=None
        )
        with self.assertRaises(GitHubError) as ctx:
            _make_request("http://api.github.com")
        self.assertEqual(ctx.exception.code, "rate_limited")

    def test_mutual_exclusion_path_and_repo(self) -> None:
        res_json = project_overview(path="/local/path", repo="owner/repo", format="json")
        data = json.loads(res_json)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "invalid_argument")
        self.assertIn("Cannot specify both", data["error"]["message"])

    @patch("urllib.request.urlopen")
    def test_mcp_github_routing_integration(self, mock_urlopen: MagicMock) -> None:
        sample_zip = create_sample_zipball()
        mock_response = MagicMock()
        mock_response.read.return_value = sample_zip
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # project_overview with repo
        res_json = project_overview(repo="owner/repo", ref="main", format="json")
        data = json.loads(res_json)
        self.assertTrue(data["ok"])
        self.assertEqual(data["path"], "github.com/owner/repo@main")
        self.assertEqual(data["metadata"]["file_count"], 2)  # ignored.txt filtered out

        # project_get_file with repo
        res_file = project_get_file("src/main.py", repo="owner/repo", format="json")
        d_file = json.loads(res_file)
        self.assertTrue(d_file["ok"])
        self.assertEqual(d_file["data"]["content"], "print('hello from github')\n")


if __name__ == "__main__":
    unittest.main()

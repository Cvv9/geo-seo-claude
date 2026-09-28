"""Regression coverage for GitHub Pages star-history generation."""

import importlib.util
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from urllib.error import HTTPError


SCRIPT_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "star_history.py"
SPEC = importlib.util.spec_from_file_location("star_history", SCRIPT_PATH)
star_history = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(star_history)


class TestZeroStarHistory(TestCase):
    """New forks have no stargazers yet, but must still publish a usable chart."""

    def test_empty_stargazer_history_generates_zero_star_svgs(self):
        with TemporaryDirectory() as output_dir:
            with (
                patch.object(star_history, "TOKEN", "test-token"),
                patch.object(star_history, "OUT_DIR", output_dir),
                patch.object(star_history, "fetch_star_dates", return_value=[]),
            ):
                star_history.main()

            for filename in ("star-history.svg", "star-history-dark.svg"):
                svg = (Path(output_dir) / filename).read_text(encoding="utf-8")
                self.assertIn("<svg", svg)
                self.assertIn("★ 0", svg)


class TestStargazerAccess(TestCase):
    def test_403_with_actions_token_retries_public_endpoint(self):
        requests = []

        def urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                raise HTTPError(request.full_url, 403, "Forbidden", None, None)
            return io.BytesIO(b"[]")

        with (
            patch.object(star_history, "TOKEN", "actions-token"),
            patch.object(star_history.urllib.request, "urlopen", side_effect=urlopen),
        ):
            self.assertEqual(star_history.fetch_page(1), [])

        self.assertEqual(requests[0].get_header("Authorization"), "Bearer actions-token")
        self.assertIsNone(requests[1].get_header("Authorization"))

"""Regression coverage for GitHub Pages star-history generation."""

import importlib.util
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


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
    def test_weekly_history_expands_to_chronological_daily_star_points(self):
        history = [
            {"week": 1_704_672_000, "total": 2, "days": [0, 1, 0, 1, 0, 0, 0]},
            {"week": 1_704_067_200, "total": 1, "days": [1, 0, 0, 0, 0, 0, 0]},
        ]
        requests = []

        def urlopen(request, timeout):
            requests.append(request)
            return io.BytesIO(json.dumps(history).encode("utf-8"))

        with (
            patch.object(star_history, "TOKEN", "read-only-token"),
            patch.object(star_history.urllib.request, "urlopen", side_effect=urlopen),
        ):
            dates = star_history.fetch_star_dates()

        self.assertEqual(len(dates), 3)
        self.assertEqual(dates, sorted(dates))
        self.assertIn("/stargazers/history?", requests[0].full_url)
        self.assertEqual(
            requests[0].get_header("X-github-api-version"), "2026-03-10"
        )
        self.assertEqual(
            requests[0].get_header("Accept"), "application/vnd.github+json"
        )

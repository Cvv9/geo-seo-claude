"""Regression coverage for GitHub Pages star-history generation."""

import importlib.util
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

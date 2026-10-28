"""Focused V540 web-choice, layout, and Discord-help regression runner."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.argv = [str(ROOT / "PAFPlayer.py"), "--unit-tests"]

import PAFPlayer as player  # noqa: E402


NAMES = (
    "test_v536_auto_tallest_visualizer_rows_web_contract",
    "test_v540_web_choice_marks_auto_tallest_and_discord_help",
)


if __name__ == "__main__":
    suite = unittest.TestSuite(player.PlayWaveFileTests(name) for name in NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)

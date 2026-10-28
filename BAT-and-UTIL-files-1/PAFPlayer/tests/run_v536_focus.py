"""Focused V536 regression runner; keeps the monolith in unit-test import mode."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.argv = [str(ROOT / "PAFPlayer.py"), "--unit-tests"]

import PAFPlayer as player  # noqa: E402


NAMES = (
    "test_v536_adaptive_progress_uses_current_levels_and_spatial_decay",
    "test_v536_artwork_seaming_accepts_zero_based_favorite_and_default",
    "test_v536_auto_tallest_visualizer_rows_web_contract",
    "test_v242_progress_uses_cached_visualizer_levels_and_adaptive_demo",
)


if __name__ == "__main__":
    suite = unittest.TestSuite(player.PlayWaveFileTests(name) for name in NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)

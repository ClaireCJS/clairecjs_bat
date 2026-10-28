"""Focused V538 progress timing and web-control regression runner."""
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
    "test_v538_beat_timing_control_and_timestamp_contract",
)


if __name__ == "__main__":
    suite = unittest.TestSuite(player.PlayWaveFileTests(name) for name in NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)

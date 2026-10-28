"""Focused V535 regression runner; keeps the monolith in unit-test import mode."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.argv = [str(ROOT / "PAFPlayer.py"), "--unit-tests"]

import PAFPlayer as player  # noqa: E402


NAMES = (
    "test_v535_near_eof_resume_rewinds_fifteen_seconds",
    "test_v535_missing_bookmark_uses_saved_successor",
    "test_v535_legacy_missing_bookmark_uses_first_remaining_track",
    "test_v535_shuffle_lifetime_is_a_persisted_web_playback_setting",
)


if __name__ == "__main__":
    suite = unittest.TestSuite(player.PlayWaveFileTests(name) for name in NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)

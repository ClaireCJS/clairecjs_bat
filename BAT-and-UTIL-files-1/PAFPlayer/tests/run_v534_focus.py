"""Focused V534 regression runner; keeps the monolith in unit-test import mode."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.argv = [str(ROOT / "PAFPlayer.py"), "--unit-tests"]

import PAFPlayer as player  # noqa: E402


NAMES = (
    "test_v534_simulator_uses_live_bounded_selection_core",
    "test_v534_launch_cooldown_covers_artist_song_alias_paths",
    "test_v533_recent_shuffle_revalidates_stale_never_for_album_alias",
    "test_v108_shuffle_visit_ledger_persists_separately_from_earned_history",
)


if __name__ == "__main__":
    suite = unittest.TestSuite(player.PlayWaveFileTests(name) for name in NAMES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)

"""Focused V395 regression tests; no audio, registry writes, or GUI required."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("play_audio_file.py")
SPEC = importlib.util.spec_from_file_location("pafplayer_v395", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class MissingPlaylistEntryWarningTests(unittest.TestCase):
    def test_missing_slot_advances_to_next_existing_slot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "gone.flac"
            playable = root / "still-here.flac"
            playable.touch()
            self.assertEqual(
                playable,
                PAF.playlist_queue_neighbor_distinct(
                    [missing, playable], missing, 1
                ),
            )

    def test_browser_notice_is_expiring_and_preencoded(self) -> None:
        server = PAF.PAFWebServer(enabled=False)
        with mock.patch.object(PAF.time, "time", return_value=1_000.0):
            server.publish_notice("Playlist entry is missing: X", seconds=5.0)
        state = json.loads(server.status_json_snapshot())
        self.assertEqual("Playlist entry is missing: X", state["session_notice"]["message"])
        self.assertEqual("warning", state["session_notice"]["level"])
        self.assertEqual(1_005.0, state["session_notice"]["expires_at_epoch"])

    def test_all_three_warning_surfaces_are_wired(self) -> None:
        source = Path(PAF.__file__).read_text(encoding="utf-8")
        html = PAF._paf_web_html()
        self.assertIn('id="sessionNotice"', html)
        self.assertIn("notice.expires_at_epoch", html)
        self.assertIn('web_server.publish_notice(pending_playlist_warning, seconds=5.0)', source)
        self.assertIn('initial_warning=track_initial_warning', source)
        self.assertIn('if drcs_enabled:', source[source.index("if initial_warning:"):source.index("def change_volume")])


class FloatingLyricsPerformanceTests(unittest.TestCase):
    def test_active_playback_freezes_only_unsafe_decorative_animation(self) -> None:
        limit = PAF.EXTERNAL_FLOATING_LYRICS_ANIMATION_MAX_PIXELS
        self.assertTrue(PAF.floating_lyrics_animation_is_safe(limit, 20.0))
        self.assertFalse(PAF.floating_lyrics_animation_is_safe(limit + 1, 20.0))
        self.assertFalse(
            PAF.floating_lyrics_animation_is_safe(
                100_000,
                PAF.EXTERNAL_FLOATING_LYRICS_ANIMATION_MAX_FRAME_MS,
            )
        )
        self.assertFalse(
            PAF.floating_lyrics_animation_is_safe(
                limit * 4,
                500.0,
                playback_running=False,
            )
        )

    def test_measured_cost_gets_a_real_audio_safe_backoff(self) -> None:
        self.assertGreaterEqual(
            PAF.floating_lyrics_animation_interval_ms(
                600_000, 90.0, playback_running=True
            ),
            4 * 90,  # Current cue responsiveness keeps backoff proportional to paint cost.
        )
        self.assertEqual(40, PAF.floating_lyrics_render_debounce_ms(500_000))
        self.assertEqual(120, PAF.floating_lyrics_render_debounce_ms(1_500_000))
        self.assertEqual(220, PAF.floating_lyrics_render_debounce_ms(4_000_000))

    def test_large_glyph_projection_uses_native_pillow_operation(self) -> None:
        source = Path(PAF.__file__).read_text(encoding="utf-8")
        painter = source[
            source.index("def pattern_rgba_for_mask"):
            source.index("def plasma_rgba_for_mask")
        ]
        self.assertIn("mask.getprojection()", painter)
        self.assertNotIn("mask.crop(column_box).getbbox()", painter)


if __name__ == "__main__":
    unittest.main()

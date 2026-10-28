"""Regression coverage for the V619 console karaoke entry transition."""

import inspect
import unittest

import PAFPlayer as app


class KaraokeEntryTests(unittest.TestCase):
    def test_gap_to_first_cue_prioritizes_karaoke(self):
        kwargs = dict(
            karaoke_enabled=True,
            gap_expansion_enabled=True,
            compositing_mode=0,
            visualizer_uses_lyric_rows=False,
        )
        self.assertTrue(app.prioritize_console_karaoke_entry((None, ""), 4, **kwargs))
        self.assertTrue(app.prioritize_console_karaoke_entry(None, 0, **kwargs))
        self.assertFalse(app.prioritize_console_karaoke_entry((3, "old"), 4, **kwargs))
        self.assertFalse(app.prioritize_console_karaoke_entry((None, ""), None, **kwargs))

    def test_compositing_modes_that_use_lyric_rows_keep_visualizer_first(self):
        base = dict(
            karaoke_enabled=True,
            gap_expansion_enabled=True,
            compositing_mode=0,
            visualizer_uses_lyric_rows=False,
        )
        for override in (
            {"karaoke_enabled": False},
            {"gap_expansion_enabled": False},
            {"compositing_mode": 1},
            {"compositing_mode": 2},
            {"compositing_mode": 3},
            {"visualizer_uses_lyric_rows": True},
        ):
            with self.subTest(override=override):
                self.assertFalse(app.prioritize_console_karaoke_entry(
                    (None, ""), 1, **(base | override),
                ))

    def test_lyric_rows_are_one_synchronized_terminal_payload(self):
        parts = ["\033[3;1H\033#3one", "\033[4;1H\033#4one", "\033[5;1H\033#5\033[2K"]
        payload = app.console_karaoke_frame_payload(parts, synchronized=True)
        self.assertEqual("\033[?2026h" + "".join(parts) + "\033[?2026l", payload)
        self.assertEqual("".join(parts), app.console_karaoke_frame_payload(parts, synchronized=False))
        self.assertEqual("", app.console_karaoke_frame_payload([], synchronized=True))

    def test_entry_is_painted_before_visualizer_geometry_change(self):
        source = inspect.getsource(app.play_audio_file)
        loop = source[source.index("cue_frame = shared_karaoke_frame(displayed_position)"):]
        self.assertLess(loop.index("if karaoke_entry_first:"), loop.index("if visualizer_due and not config_visualizers_paused:"))
        self.assertLess(loop.index("show_status(\n                            displayed_position, indicator,"), loop.index("if visualizer_due and not config_visualizers_paused:"))
        self.assertIn("if not karaoke_entry_first and (cue_changed", loop)


if __name__ == "__main__":
    unittest.main()

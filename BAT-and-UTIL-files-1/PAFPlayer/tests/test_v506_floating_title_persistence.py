"""Regression checks for the Floating Lyrics title duration startup and save paths."""

import inspect
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import PAFPlayer as app


class FloatingTitlePersistence(unittest.TestCase):
    def test_default_is_25_seconds(self):
        self.assertEqual(app.FLOATING_LYRICS_TRACK_INTRO_SECONDS, 25.0)
        self.assertEqual(app.PLAYER_SETTING_DEFAULTS["FloatingLyricsTrackIntroSeconds"], 25.0)

    @unittest.skipUnless(os.name == "nt", "PAFPlayer stores these settings in the Windows registry")
    def test_missing_value_uses_default_and_legacy_value_migrates(self):
        def missing(_name):
            raise OSError("missing")

        with patch.object(app, "paf_registry_query_value", side_effect=missing):
            self.assertEqual(app.load_player_settings()["FloatingLyricsTrackIntroSeconds"], 25.0)

        def legacy(name):
            if name == "FloatingLyricsTrackIntroMs":
                return 12500, 4
            raise OSError("missing")

        with patch.object(app, "paf_registry_query_value", side_effect=legacy):
            self.assertEqual(app.load_player_settings()["FloatingLyricsTrackIntroSeconds"], 12.5)

    @unittest.skipUnless(os.name == "nt", "PAFPlayer stores these settings in the Windows registry")
    def test_saved_seconds_survive_reload_and_take_precedence_over_legacy(self):
        stored = {"FloatingLyricsTrackIntroMs": (2500, 4)}

        def query(name):
            if name not in stored:
                raise OSError("missing")
            return stored[name]

        def save(name, kind, value):
            stored[name] = value, kind
            return True

        with patch.object(app, "paf_registry_query_value", side_effect=query), patch.object(
            app, "paf_registry_set_value", side_effect=save
        ):
            app.save_player_setting_value("FloatingLyricsTrackIntroSeconds", 7.25)
            self.assertEqual(stored["FloatingLyricsTrackIntroSeconds"][0], "7.250000")
            self.assertEqual(app.load_player_settings()["FloatingLyricsTrackIntroSeconds"], 7.25)
            app.save_player_settings({"FloatingLyricsTrackIntroSeconds": 19.75})
            self.assertEqual(app.load_player_settings()["FloatingLyricsTrackIntroSeconds"], 19.75)

    def test_startup_and_track_flush_use_live_duration(self):
        source = inspect.getsource(app.main)
        self.assertIn(
            'FLOATING_LYRICS_TRACK_INTRO_SECONDS = persisted_settings["FloatingLyricsTrackIntroSeconds"]',
            source,
        )
        self.assertIn(
            "'FloatingLyricsTrackIntroSeconds': FLOATING_LYRICS_TRACK_INTRO_SECONDS,",
            source,
        )
        persisted = {"FloatingLyricsTrackIntroSeconds": 25.0}
        app.merge_runtime_player_settings(
            persisted, {"FloatingLyricsTrackIntroSeconds": 7.25}
        )
        self.assertEqual(persisted["FloatingLyricsTrackIntroSeconds"], 7.25)


if __name__ == "__main__":
    unittest.main()

"""Regression checks for V501 fractional Floating Lyrics title duration persistence."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import PAFPlayer as app


class FloatingTitleDurationPersistence(unittest.TestCase):
    def test_setting_remains_fractional_in_defaults_and_schema(self):
        self.assertIsInstance(app.PLAYER_SETTING_DEFAULTS["FloatingLyricsTrackIntroSeconds"], float)
        item = next(x for x in app.paf_web_control_schema()["sliders"] if x["key"] == "floating_track_intro_seconds")
        self.assertEqual(item["step"], 0.01)

    def test_all_settings_save_path_special_cases_fractional_duration(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8-sig")
        self.assertIn('if name == "FloatingLyricsTrackIntroSeconds":', source)
        self.assertIn('paf_registry_set_value(name, winreg.REG_SZ, format(float(value), ".6f"))', source)
        self.assertIn('float(v) if str(k) == "FloatingLyricsTrackIntroSeconds" else int(v)', source)

    def test_legacy_millisecond_key_is_not_the_active_web_save_target(self):
        self.assertTrue(app.paf_web_action_is_allowed("web-set:floating_track_intro_seconds:0.25"))
        self.assertFalse(app.paf_web_action_is_allowed("web-set:floating_track_intro_ms:250"))


if __name__ == "__main__":
    unittest.main()

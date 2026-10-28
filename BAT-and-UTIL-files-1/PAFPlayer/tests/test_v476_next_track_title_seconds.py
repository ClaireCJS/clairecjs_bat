"""Regression checks for V476's fractional next-track title duration control."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import PAFPlayer as app


class NextTrackTitleSeconds(unittest.TestCase):
    def test_schema_uses_fractional_seconds_and_requested_label(self):
        item = next(x for x in app.paf_web_control_schema()["sliders"] if x["key"] == "floating_track_intro_seconds")
        self.assertEqual(item["label"], "Display song title for first")
        self.assertEqual(item["min"], 0)
        self.assertEqual(item["max"], 60)
        self.assertEqual(item["step"], 0.01)
        self.assertEqual(item["suffix"], " seconds")

    def test_decimal_web_values_are_accepted(self):
        self.assertTrue(app.paf_web_action_is_allowed("web-set:floating_track_intro_seconds:0.25"))
        self.assertTrue(app.paf_web_action_is_allowed("web-set:floating_track_intro_seconds:2.5"))
        self.assertFalse(app.paf_web_action_is_allowed("web-set:floating_track_intro_seconds:60.01"))

    def test_ui_formats_selected_value_in_seconds(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8-sig")
        self.assertIn("Display song title for first '+Number(value)+' seconds", source)
        self.assertIn("key == \"floating_track_intro_seconds\"", source)
        self.assertIn('round(FLOATING_LYRICS_TRACK_INTRO_SECONDS * 1000)', source)


if __name__ == "__main__":
    unittest.main()

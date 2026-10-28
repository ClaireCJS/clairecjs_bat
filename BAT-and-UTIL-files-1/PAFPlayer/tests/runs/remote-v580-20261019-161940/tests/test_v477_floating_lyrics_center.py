"""Regression checks for V477 floating-lyrics placement over the console visualizer."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import PAFPlayer as app


class FloatingLyricsConsoleCenter(unittest.TestCase):
    def test_explicit_rectangle_geometry_preserves_signed_coordinates(self):
        self.assertEqual(
            app.centered_geometry_over_rect(400, 200, (-1920, 40, 0, 1040)),
            "400x200-1160+440",
        )
        self.assertIsNone(app.centered_geometry_over_rect(400, 200, None))

    def test_web_control_and_action_are_present(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8-sig")
        self.assertIn('id="floatingLyricsCenterVisualizerButton"', source)
        self.assertIn("Center Over Visualizer", source)
        self.assertIn("external-floating-lyrics-console-center", source)
        self.assertTrue(app.paf_web_action_is_allowed("external-floating-lyrics-console-center"))

    def test_existing_center_action_remains_distinct(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8-sig")
        self.assertIn("action('external-floating-lyrics-center')", source)
        self.assertIn("center_floating_over_console_visualizer", source)
        self.assertIn('center_popup_window(', source)


if __name__ == "__main__":
    unittest.main()

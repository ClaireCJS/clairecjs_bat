"""Focused regression checks for the saved console visualizer FPS ceiling."""
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.argv = [str(ROOT / "PAFPlayer.py"), "--unit-tests"]
import PAFPlayer as player  # noqa: E402


class ConsoleVisualizerFpsTests(unittest.TestCase):
    def test_factory_default_and_saved_registry_value(self):
        self.assertEqual(60, player.PLAYER_SETTING_DEFAULTS["ConsoleVisualizerMaxFps"])

        def registry(name):
            if name == "ConsoleVisualizerMaxFps":
                return 47, 4
            raise OSError(name)

        with mock.patch.object(player, "paf_registry_query_value_read_only", side_effect=registry):
            self.assertEqual(47, player.load_player_settings(read_only=True)["ConsoleVisualizerMaxFps"])
        with mock.patch.object(player, "paf_registry_query_value_read_only", side_effect=OSError):
            self.assertEqual(60, player.load_player_settings(read_only=True)["ConsoleVisualizerMaxFps"])

    def test_ceiling_and_diagnostic_limit(self):
        self.assertEqual(60, player.console_visualizer_target_fps(120, 60))
        self.assertEqual(15, player.console_visualizer_target_fps(120, 15))
        self.assertEqual(1, player.console_visualizer_target_fps(120, 1))
        self.assertEqual(30, player.console_visualizer_target_fps(120, 60, 30))
        self.assertEqual(15, player.console_visualizer_target_fps(120, 15, 30))
        self.assertEqual(45, player.console_visualizer_target_fps(45, 60))
        self.assertEqual(120, player.clamp_console_visualizer_max_fps(999))
        self.assertEqual(1, player.clamp_console_visualizer_max_fps(-5))

    def test_web_control_is_numeric_text_entry_and_validated(self):
        schema = player.paf_web_control_schema(include_saved_marks=False)
        control = next(item for item in schema["sliders"] if item["key"] == "visualizer_max_fps")
        self.assertEqual((1, 120, 60), (control["min"], control["max"], control["default"]))
        self.assertTrue(control["text_only"])
        self.assertEqual("visualizer", control["theme"])
        self.assertTrue(player.paf_web_action_is_allowed("web-set:visualizer_max_fps:15"))
        for value in ("0", "121", "15.5", "garbage"):
            self.assertFalse(player.paf_web_action_is_allowed("web-set:visualizer_max_fps:" + value))
        html = player._paf_web_html()
        self.assertIn("if(item.text_only)", html)
        self.assertIn("entry.type='number'", html)

    def test_runtime_and_shutdown_use_same_saved_cap(self):
        source = inspect.getsource(player.play_audio_file)
        self.assertIn("set_console_visualizer_max_fps(value)", source)
        self.assertIn('save_player_setting_value("ConsoleVisualizerMaxFps", visualizer_max_fps)', source)
        self.assertIn("requested = min(visualizer_target_fps, max(min(VISUALIZER_MIN_ADAPTIVE_FPS, visualizer_target_fps), requested))", source)
        main = inspect.getsource(player.main)
        self.assertIn("visualizer_max_fps_state=visualizer_max_fps_state", main)
        self.assertIn("'ConsoleVisualizerMaxFps': int(visualizer_max_fps_state[0])", main)


if __name__ == "__main__":
    unittest.main(argv=[__file__])

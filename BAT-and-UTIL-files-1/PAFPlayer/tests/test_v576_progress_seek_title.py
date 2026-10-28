"""Focused regressions for V576 progress, instance seek, and console title."""
import unittest
import http.client
import json
import queue
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import PAFPlayer as player
import PAFPlayer_instance as instance_module


class ProgressSeekTitleTests(unittest.TestCase):
    def test_timestamp_forms_and_boundaries(self):
        expected = {"0:00": 0, "0:30": 30, "1:30": 90,
                    "60s": 60, "120s": 120, "125s": 125,
                    "-5s": -5, "-1:30": -90}
        for token, seconds in expected.items():
            with self.subTest(token=token):
                self.assertEqual(player.parse_seek_timestamp_token(token), seconds)
        for token in ("-5", "1:99", "1:30junk", "nan", "5m"):
            self.assertIsNone(player.parse_seek_timestamp_token(token))
        resolve = player.resolve_seek_timestamp_position
        self.assertEqual(resolve(-5, 0, 125), 120)
        self.assertEqual(resolve(-90, 0, 125), 35)
        self.assertEqual(resolve(-999, 0, 125), 0)
        self.assertEqual(resolve(999, 0, 125), 125)
        self.assertIsNone(resolve(-5, 0, None))

    def test_progress_modes_keep_ids_and_layer_independently(self):
        self.assertEqual(player.PLAYER_SETTING_DEFAULTS["ProgressColorMode"], 1)
        self.assertEqual(player.PLAYER_SETTING_DEFAULTS["ProgressBeatOverlayMode"], 0)
        self.assertEqual(player.progress_layer_rgb(2, .5, .2, True),
                         player.progress_color_rgb(2, .5, .8))
        color = player.progress_layer_rgb(3, .5, .25)
        self.assertEqual(player.progress_layer_rgb(3, .5, .25, False, True),
                         tuple(255 - component for component in color))
        args = (50.0, 100.0, "▶", 100, "", False, 20)
        plain = player.render_status(*args, repaint=False, progress_color_mode=1,
                                     beat_reactive_illumination=True, pulse_energy=1)
        overlay = player.render_status(*args, repaint=False, progress_color_mode=1,
                                       beat_reactive_illumination=True, pulse_energy=1,
                                       progress_beat_overlay_mode=3)
        quiet = player.render_status(*args, repaint=False, progress_color_mode=1,
                                     beat_reactive_illumination=True, pulse_energy=0,
                                     progress_beat_overlay_mode=3)
        quiet_base = player.render_status(*args, repaint=False, progress_color_mode=1,
                                          beat_reactive_illumination=True, pulse_energy=0)
        self.assertNotEqual(plain, overlay)
        self.assertEqual(quiet, quiet_base)

    def test_web_controls_and_title_styles(self):
        schema = player.paf_web_control_schema()
        selects = {item["key"] for item in schema["selects"]}
        toggles = {item["key"] for item in schema["toggles"]}
        self.assertIn("progress_beat_overlay_mode", selects)
        self.assertTrue({"progress_invert_order", "progress_invert_palette"} <= toggles)
        self.assertEqual(len(schema["title_styles"]), 25)
        for command in ("web-set:progress_invert_order:1",
                        "web-set:progress_invert_palette:1",
                        "web-set:progress_beat_overlay_mode:3",
                        "web-set:console_title_style:25",
                        "web-set:console_title_preview_seconds:5"):
            self.assertTrue(player.paf_web_action_is_allowed(command), command)
        for command in ("web-set:progress_beat_overlay_mode:17",
                        "web-set:console_title_style:26"):
            self.assertFalse(player.paf_web_action_is_allowed(command), command)
        html = player._paf_web_html()
        self.assertIn("consoleTitleDropdown", html)
        self.assertIn("Test title for 5 seconds", html)
        self.assertIn("preview(10)", html)
        for style in range(1, 26):
            self.assertIn("\033P0;1;1;10;0;2;20;0{ @", player.console_title_splash(style, 50, 20))

    def test_authenticated_instance_seek_reaches_only_its_owner(self):
        owner_actions = queue.Queue()
        background_actions = queue.Queue()
        owner = SimpleNamespace(root=Path("never-created-owner"),
                                seek_bridge=lambda seconds: (owner_actions.put(seconds) or True))
        background = SimpleNamespace(root=Path("never-created-background"),
                                     seek_bridge=lambda seconds: (background_actions.put(seconds) or True))
        official = instance_module.Instance(owner)
        other = instance_module.Instance(background)
        metadata = []
        with patch.object(instance_module, "write_json", side_effect=lambda path, value: metadata.append(value)):
            official.start()
        try:
            self.assertIsNone(other.httpd)
            def send(value, token):
                connection = http.client.HTTPConnection("127.0.0.1", official.httpd.server_port, timeout=2)
                body = json.dumps(value)
                connection.request("POST", "/handoff", body,
                                   {"X-PAF-Instance": token, "Content-Type": "application/json"})
                reply = connection.getresponse()
                result = reply.status, json.loads(reply.read())
                connection.close()
                return result
            self.assertEqual(send({"seek_seconds": -5}, metadata[0]["token"])[0], 200)
            self.assertEqual(owner_actions.get_nowait(), -5)
            self.assertTrue(background_actions.empty())
            self.assertEqual(send({"seek_seconds": 30}, "incorrect")[0], 400)
            self.assertEqual(send({"seek_seconds": "30"}, metadata[0]["token"])[0], 400)
            self.assertTrue(owner_actions.empty())
        finally:
            official.close()


if __name__ == "__main__":
    unittest.main()

import inspect
import unittest

import PAFPlayer as app


class CoordinatedFixRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = app._paf_web_html()

    def test_hud_bubbles_keep_requested_order(self):
        chips = self.html[self.html.index("const chips=[") : self.html.index("];", self.html.index("const chips=["))]
        positions = [
            chips.index("'Status: '+playState"),
            chips.index("'Last play: '+((m['Last play'])??'Never')"),
            chips.index("volIcon+' Vol: '+vol+'%'"),
            chips.index("'Balance: '+balanceText"),
        ]
        self.assertEqual(positions, sorted(positions))

    def test_popup_and_floating_controls_have_shared_order(self):
        for prefix in ("artworkPopup", "floatingLyrics"):
            ids = [
                f'id="{prefix}ConfigButton"',
                f'id="{prefix}TopmostButton"',
                f'id="{prefix}BringTopButton"',
                f'id="{prefix}BringCenterButton"',
                f'id="{prefix}EmojiMaxxButton"',
                f'id="{prefix}DecensorButton"',
            ]
            positions = [self.html.index(value) for value in ids]
            self.assertEqual(positions, sorted(positions), prefix)

    def test_topmost_can_disable_visual_button_without_removing_action(self):
        self.assertIn("popupBringTop.onclick=()=>action('external-album-art-foreground')", self.html)
        self.assertIn("floatingBringTop.onclick=()=>action('external-floating-lyrics-foreground')", self.html)
        self.assertIn("[popupBringTop,popupBringCenter,popupTopmost", self.html)
        self.assertTrue(app.paf_web_action_is_allowed("external-album-art-foreground"))
        self.assertTrue(app.paf_web_action_is_allowed("external-floating-lyrics-foreground"))

    def test_floating_pentagram_uses_console_compatible_rendering_contract(self):
        source = inspect.getsource(app.ExternalAlbumArtWindow)
        self.assertIn('"seguisym.ttf"', source)
        self.assertIn('if ch == "⛤":', source)
        self.assertIn("draw_emoji=not colored", source)
        self.assertIn("expand_lyric_outline(mask", source)
        self.assertIn("popup_emojimax_enabled", source)

    def test_rapid_seek_requests_are_cumulative_and_not_dropped(self):
        capture = app.GlobalSeekCapture()
        capture.sample(1, 0.0)
        capture.sample(0, 0.01)
        capture.sample(1, 0.02)
        capture.sample(0, 0.03)
        self.assertEqual(capture.drain(), 10.0)

        server = app.PAFWebServer(enabled=False)
        accepted = [server.enqueue_action(app.SEEK_FORWARD_5) for _ in range(100)]
        self.assertTrue(all(accepted))
        self.assertEqual(sum(server.pop_action() == app.SEEK_FORWARD_5 for _ in range(100)), 100)
        self.assertIsNone(server.pop_action())

    def test_playback_sliders_and_visualizer_height_presets(self):
        schema = app.paf_web_control_schema()
        sliders = {item["key"]: item for item in schema["sliders"]}
        for key in ("volume", "locked_bass_reduction_percent", "bass_boost_percent"):
            self.assertEqual(sliders[key].get("theme"), "playback")
        self.assertIn("visualizer-height-default", self.html)
        self.assertIn("visualizer-height-tallest", self.html)
        self.assertIn("textContent='Default'", self.html)
        self.assertIn("textContent='Tallest'", self.html)
        self.assertIn("action('web-set:visualizer_rows:16')", self.html)
        self.assertIn("action('visualizer-rows-tallest')", self.html)
        self.assertEqual(app.tallest_visualizer_rows(30, 12), 18)
        self.assertEqual(app.tallest_visualizer_rows(50, 12), 38)
        self.assertEqual(app.tallest_visualizer_rows(120, 12), 48)


if __name__ == "__main__":
    unittest.main()

import inspect
import unittest

import PAFPlayer as app


class TodoBatchV461Tests(unittest.TestCase):
    def test_seek_burst_accumulates_only_adjacent_seek_actions(self):
        batch = app.PendingSeekAccumulator(app.SEEK_FORWARD_10)
        self.assertTrue(batch.add(app.SEEK_FORWARD_10))
        self.assertTrue(batch.add(app.SEEK_FORWARD_5))
        self.assertEqual(25.0, batch.total_seconds)
        self.assertFalse(batch.add(app.PAUSE_TOGGLE))
        self.assertEqual(app.SEEK_FORWARD_5, batch.last_action)

    def test_non_default_speed_reminder_schedule(self):
        reminder = app.NonDefaultSpeedReminder()
        self.assertIsNone(reminder.observe(1.5, True, 0.0))
        self.assertIsNone(reminder.observe(1.5, True, 1799.9))
        self.assertEqual("show", reminder.observe(1.5, True, 1800.0))
        self.assertIsNone(reminder.observe(1.5, True, 2099.9))
        self.assertIsNone(reminder.observe(1.5, True, 2100.0))
        self.assertEqual("show", reminder.observe(1.5, True, 3600.0))
        self.assertTrue(reminder.answer(3600.1))
        self.assertIsNone(reminder.observe(1.0, True, 3600.2))

    def test_style_modifiers_keep_legacy_ids_and_hide_old_variants(self):
        self.assertEqual((2, True, False), app.migrate_karaoke_style_selection(3))
        labels = [item["label"] for item in app.KARAOKE_STYLE_VISIBLE_OPTIONS]
        self.assertIn("Monospace", labels)
        self.assertFalse(any("Clean" in label or "Framed" in label for label in labels))
        self.assertIn("Spaced", app.karaoke_style_label(2, spaced=True))
        self.assertIn("Framed:", app.karaoke_style_label(2, framed=True))
        self.assertTrue(" " in app.stylize_karaoke_text("AB", 2, spaced=True))

    def test_global_config_developer_gate_and_new_controls(self):
        for machine in ("demona", "wyvern", "thailog", "goliath"):
            self.assertTrue(app.global_config_developer_choice_available({"USERNAME": "claire", "COMPUTERNAME": machine}))
        self.assertFalse(app.global_config_developer_choice_available({"USERNAME": "other", "COMPUTERNAME": "demona"}))
        self.assertEqual("PAFPlayer.dcc", app.GLOBAL_CONFIG_DCC_FILENAME)

        html = app._paf_web_html()
        for control_id in (
            "artworkPopupKaraokeToggle",
            "artworkPopupEmojiMaxxConfigButton",
            "floatingLyricsEmojiMaxxConfigButton",
            "artworkPopupEmojiMaxxButton",
            "floatingLyricsEmojiMaxxButton",
        ):
            self.assertIn(f'id="{control_id}"', html)
        self.assertIn("openExtendedEmojiMaxxConfiguration", html)

        schema = app.paf_web_control_schema()
        toggle_keys = {item["key"] for item in schema["toggles"]}
        self.assertIn("alert_non_default_speed", toggle_keys)
        self.assertIn("karaoke_style_spaced", toggle_keys)
        self.assertIn("karaoke_style_framed", toggle_keys)
        self.assertIn("karaoke_style_frame", {item["key"] for item in schema["selects"]})

    def test_pause_overlay_names_action_available_after_toggle(self):
        self.assertEqual("Pause", app.pause_visualizer_feedback_label(False))
        self.assertEqual("Unpause", app.pause_visualizer_feedback_label(True))
        self.assertIn("ART_COLOR_VISUALIZER_KARAOKE_SIDES", inspect.getsource(app.play_audio_file))


if __name__ == "__main__":
    unittest.main()

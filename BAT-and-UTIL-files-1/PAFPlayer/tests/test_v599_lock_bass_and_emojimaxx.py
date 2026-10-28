"""V599: new locked-bass default and literal Emojimaxx wording."""

import unittest
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as app


class LockedBassDefaultTests(unittest.TestCase):
    def test_missing_saved_choice_defaults_on_without_writing(self):
        with mock.patch.dict(app._BASS_SESSION_OVERRIDES, {}, clear=True), \
             mock.patch.object(app, "paf_registry_query_value", side_effect=OSError("missing")), \
             mock.patch.object(app, "save_player_setting_value") as save:
            values = app.load_bass_settings()
            self.assertEqual(1, values["ReduceBassWhenLocked"])
            self.assertEqual(50, values["LockedBassReductionPercent"])
            self.assertEqual(-10, app.bass_settings_effective_db(values, locked=True))
            self.assertEqual(0, app.bass_settings_effective_db(values, locked=False))
            save.assert_not_called()

    def test_saved_off_and_session_override_remain_authoritative(self):
        def read(name):
            if name == "ReduceBassWhenLocked":
                return 0, None
            raise OSError("missing")

        with mock.patch.dict(app._BASS_SESSION_OVERRIDES, {}, clear=True), \
             mock.patch.object(app, "paf_registry_query_value", side_effect=read):
            self.assertEqual(0, app.load_bass_settings()["ReduceBassWhenLocked"])
            app._BASS_SESSION_OVERRIDES["ReduceBassWhenLocked"] = 1
            self.assertEqual(1, app.load_bass_settings()["ReduceBassWhenLocked"])

    def test_web_initial_state_reflects_saved_choice(self):
        for stored in (None, 0, 1):
            def read(name):
                if name == "ReduceBassWhenLocked" and stored is not None:
                    return stored, None
                raise OSError("missing")

            with self.subTest(stored=stored), \
                 mock.patch.dict(app._BASS_SESSION_OVERRIDES, {}, clear=True), \
                 mock.patch.object(app, "paf_registry_query_value", side_effect=read), \
                 mock.patch.object(app, "paf_workflows", return_value=SimpleNamespace()):
                server = app.PAFWebServer(enabled=False)
                self.assertEqual(stored != 0, server.snapshot()["reduce_bass_when_locked"])

    def test_web_control_is_independent_from_lockscreen_status(self):
        with mock.patch.object(app, "waveout_output_devices", return_value=[]):
            schema = app.paf_web_control_schema(include_saved_marks=False)
        control = next(item for item in schema["toggles"] if item["key"] == "reduce_bass_when_locked")
        self.assertEqual("Reduce bass while computer is locked", control["label"])
        self.assertEqual("reduce_bass_when_locked", control["web_key"])
        self.assertIn("keeping Windows lock-screen song status enabled", control["tooltip"])


class EmojimaxxWordingTests(unittest.TestCase):
    def test_heavy_is_literal_in_lookup_and_rendered_lyrics(self):
        self.assertNotIn("heavy", app.semantic)
        self.assertIsNone(app.emojimax_replacement_for_key("heavy"))
        for word in ("heavy", "Heavy", "HEAVY"):
            with self.subTest(word=word):
                rendered, solutions = app.emojimax_plain_with_solutions(word)
                self.assertEqual(word, rendered)
                self.assertEqual([], solutions)


if __name__ == "__main__":
    unittest.main()

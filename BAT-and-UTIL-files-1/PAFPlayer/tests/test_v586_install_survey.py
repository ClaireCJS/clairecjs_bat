"""Focused, noninteractive checks for the V586 first-install rehearsal."""
from __future__ import annotations

import io
from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as app


class Tty:
    def isatty(self):
        return True


VOLUME = {"key": "volume", "setting": "Volume", "kind": "slider", "label": "Volume", "tooltip": "Playback level", "min": 0, "max": 400}
BALANCE = {"key": "balance", "setting": "Balance", "kind": "slider", "label": "Balance", "tooltip": "Stereo position", "min": -100, "max": 100}
COLOR = {"key": "color_style", "setting": "ColorStyle", "kind": "select", "label": "Palette", "tooltip": "Visualizer colors", "options": [{"value": 1, "label": "Red"}, {"value": 2, "label": "Blue"}]}


class InstallSurveyTests(unittest.TestCase):
    def run_script(self, sections, answers, *, current=None, defaults=None, favorites=None):
        output = []
        iterator = iter(answers)
        def read(_prompt):
            value = next(iterator)
            if isinstance(value, BaseException):
                raise value
            return value
        current = current or {"Volume": 30, "Balance": 25, "ColorStyle": 2}
        defaults = defaults or {"Volume": 100, "Balance": 0, "ColorStyle": 1}
        with mock.patch.object(app, "_install_survey_sections", return_value=sections), \
             mock.patch.object(app, "load_player_settings", return_value=current), \
             mock.patch.object(app, "_install_survey_defaults", return_value=defaults), \
             mock.patch.object(app, "_install_survey_web_preferences", return_value={}), \
             mock.patch.object(app, "_install_survey_favorites", return_value=favorites or []), \
             mock.patch.object(app, "save_player_settings", side_effect=AssertionError("active save")), \
             mock.patch.object(app, "paf_registry_set_value", side_effect=AssertionError("registry write")), \
             mock.patch.object(app, "global_config_load_profile", side_effect=AssertionError("profile load")), \
             mock.patch.object(app, "_global_config_write_json", side_effect=AssertionError("profile write")):
            code = app.run_install_survey_dry_run(input_fn=read, output_fn=output.append, stdin=Tty())
        return code, "\n".join(output)

    def test_dry_run_never_changes_active_settings(self):
        code, output = self.run_script([("Playback / output", [VOLUME])], ["c", "d", "d"])
        self.assertEqual(0, code)
        self.assertIn("Volume: 30 → 100", output)
        self.assertIn("Survey discarded", output)

    def test_skip_section_and_finish_early_assume_only_remaining_defaults(self):
        sections = [("First", [VOLUME]), ("Second", [BALANCE])]
        code, output = self.run_script(sections, ["s", "f", "d"])
        self.assertEqual(0, code)
        self.assertIn("Balance: 25 → 0", output)
        self.assertNotIn("Volume: 30 → 100", output)
        self.assertIn("1 unanswered choices assumed", output)

    def test_abort_and_ctrl_c_or_eof_leave_no_changes(self):
        for answers in (["a", "w"], ["c", KeyboardInterrupt()], ["c", EOFError()]):
            with self.subTest(answers=answers):
                code, output = self.run_script([("First", [VOLUME])], answers)
                self.assertEqual(130, code)
                self.assertIn("Survey aborted", output)

    def test_defaults_and_favorites_are_displayed_and_selectable(self):
        code, output = self.run_script([("Visualizer", [COLOR])], ["c", "f", "d"], favorites=[2])
        self.assertEqual(0, code)
        self.assertIn("Default: Red", output)
        self.assertIn("Current saved: Blue", output)
        self.assertIn("F1=Blue", output)

    def test_invalid_and_conflicting_answers_do_not_escape_validation(self):
        code, output = self.run_script([("Visualizer", [COLOR])], ["c", "f", "999", "NaN", "2", "d"])
        self.assertEqual(0, code)
        self.assertGreaterEqual(output.count("Invalid answer"), 3)
        self.assertRaises(ValueError, app._install_survey_parse_answer, "1.5", COLOR, 1, [])
        self.assertRaises(ValueError, app._install_survey_parse_answer, "401", VOLUME, 100, [])

    def test_save_requires_exact_confirmation_and_uses_existing_profile_format(self):
        sections = [("Playback", [VOLUME])]
        output = []
        answers = iter(["c", "d", "s", "House", "SAVE House", ""])
        written = []
        with mock.patch.object(app, "_install_survey_sections", return_value=sections), \
             mock.patch.object(app, "load_player_settings", return_value={"Volume": 30}), \
             mock.patch.object(app, "_install_survey_defaults", return_value={"Volume": 100}), \
             mock.patch.object(app, "_install_survey_web_preferences", return_value={}), \
             mock.patch.object(app, "_install_survey_favorites", return_value=[]), \
             mock.patch.object(app, "_global_config_profile_store", return_value={}), \
             mock.patch.object(app, "_global_config_profile_list", return_value=[]), \
             mock.patch.object(app, "_global_config_write_json", side_effect=lambda path, value: written.append((path, value))), \
             mock.patch.object(app, "save_player_settings", side_effect=AssertionError("active save")), \
             mock.patch.object(app, "global_config_load_profile", side_effect=AssertionError("automatic load")):
            code = app.run_install_survey_dry_run(input_fn=lambda _: next(answers), output_fn=output.append, stdin=Tty())
        self.assertEqual(0, code)
        self.assertEqual(1, len(written))
        self.assertEqual(app.global_config_profiles_path(), written[0][0])
        self.assertEqual(app.GLOBAL_CONFIG_FORMAT, written[0][1]["House"]["format"])
        self.assertEqual(100, written[0][1]["House"]["player_settings"]["Volume"])
        self.assertIn("not active", "\n".join(output))

    def test_failed_save_confirmation_and_duplicate_name_write_nothing(self):
        sections = [("Playback", [VOLUME])]
        code, output = self.run_script(sections, ["c", "d", "s", "House", "no"])
        self.assertEqual(0, code)
        self.assertIn("save cancelled", output)
        with mock.patch.object(app, "_global_config_profile_list", return_value=["HOUSE"]):
            code, output = self.run_script(sections, ["c", "d", "s", "House", ""])
        self.assertEqual(0, code)
        self.assertIn("already exists", output)

    def test_loading_needs_two_confirmations_after_save(self):
        sections = [("Playback", [VOLUME])]
        for second, expected in (("no", 0), ("APPLY House", 1)):
            with self.subTest(second=second):
                answers = iter(["c", "d", "s", "House", "SAVE House", "l", "LOAD House", second])
                loaded = []
                with mock.patch.object(app, "_install_survey_sections", return_value=sections), \
                     mock.patch.object(app, "load_player_settings", return_value={"Volume": 30}), \
                     mock.patch.object(app, "_install_survey_defaults", return_value={"Volume": 100}), \
                     mock.patch.object(app, "_install_survey_web_preferences", return_value={}), \
                     mock.patch.object(app, "_install_survey_favorites", return_value=[]), \
                     mock.patch.object(app, "_global_config_profile_store", return_value={}), \
                     mock.patch.object(app, "_global_config_profile_list", return_value=[]), \
                     mock.patch.object(app, "_global_config_write_json"), \
                     mock.patch.object(app, "global_config_load_profile", side_effect=lambda name: loaded.append(name)):
                    code = app.run_install_survey_dry_run(input_fn=lambda _: next(answers), output_fn=lambda _: None, stdin=Tty())
                self.assertEqual(0, code)
                self.assertEqual(["House"] if expected else [], loaded)

    def test_missing_tty_and_conflicting_cli_never_enter_player_startup(self):
        with mock.patch.object(app, "_install_survey_sections", side_effect=AssertionError("questions")):
            output = []
            self.assertEqual(2, app.run_install_survey_dry_run(output_fn=output.append, stdin=io.StringIO()))
            self.assertIn("Interactive stdin/TTY is required", "\n".join(output))
        with mock.patch.object(app, "paf_workflows", side_effect=AssertionError("player startup")):
            self.assertEqual(2, app.main(["--install-survey-dry-run", "--playlist", "sample.m3u"]))
            self.assertEqual(2, app.main(["--install-survey-dry-run=unexpected"]))

    def test_catalog_uses_existing_ids_and_ten_skippable_sections(self):
        sections = app._install_survey_sections()
        self.assertEqual(10, len(sections))
        self.assertTrue(all(questions for _, questions in sections))
        for _title, questions in sections:
            for question in questions:
                if question["kind"] != "integration":
                    self.assertIn(question["setting"], app.PLAYER_SETTING_DEFAULTS)
        self.assertFalse(any(q["key"] == "paf-web-background-config-v238.enabled" for _, items in sections for q in items))

    def test_read_only_settings_and_schema_do_not_call_migrating_reader(self):
        with mock.patch.object(app, "paf_registry_query_value", side_effect=AssertionError("migrating read")), \
             mock.patch.object(app, "paf_registry_query_value_read_only", side_effect=OSError("missing")), \
             mock.patch.object(app, "registry_favorites", side_effect=AssertionError("mark lookup")):
            self.assertEqual(app.PLAYER_SETTING_DEFAULTS["Volume"], app.load_player_settings(read_only=True)["Volume"])
            self.assertIsInstance(app.load_user_defaults(read_only=True), dict)
            self.assertIn("selects", app.paf_web_control_schema(include_saved_marks=False))

    def test_survey_profile_load_omits_registry_marks_and_matrix_changes(self):
        with mock.patch.object(app, "save_player_settings") as saved, \
             mock.patch.object(app, "_global_config_restore_registry_values", side_effect=AssertionError("registry")), \
             mock.patch.object(app, "save_active_matrixmixer_matrices", side_effect=AssertionError("matrix")):
            app._global_config_persist_snapshot({"player_settings": {"Volume": 50}, "registry_values": {}, "matrix": {}})
        self.assertEqual(50, saved.call_args.args[0]["Volume"])

    def test_full_catalog_finish_early_is_read_only(self):
        output = []
        answers = iter(["f", "d"])
        with mock.patch.object(app, "save_player_settings", side_effect=AssertionError("settings write")), \
             mock.patch.object(app, "paf_registry_set_value", side_effect=AssertionError("registry write")), \
             mock.patch.object(app, "_global_config_write_json", side_effect=AssertionError("profile write")):
            code = app.run_install_survey_dry_run(input_fn=lambda _: next(answers), output_fn=output.append, stdin=Tty())
        self.assertEqual(0, code)
        self.assertIn("unanswered choices assumed", "\n".join(output))


if __name__ == "__main__":
    unittest.main()

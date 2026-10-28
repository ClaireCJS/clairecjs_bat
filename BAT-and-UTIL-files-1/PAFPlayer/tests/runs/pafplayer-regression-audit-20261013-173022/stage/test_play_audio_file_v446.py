"""V446 Global Config profiles and state-aware pause feedback."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import PAFPlayer as p


class V446GlobalConfigTests(unittest.TestCase):
    def test_pause_feedback_names_the_result(self):
        self.assertEqual("Pause", p.pause_visualizer_feedback_label(False))
        self.assertEqual("Unpause", p.pause_visualizer_feedback_label(True))

    def test_developer_choice_gate_uses_username_and_machine_environment(self):
        self.assertTrue(p.global_config_developer_choice_available({"USERNAME": "claire", "COMPUTERNAME": "demona"}))
        self.assertTrue(p.global_config_developer_choice_available({"USERNAME": "CLAIRE", "COMPUTERNAME": "GOLIATH"}))
        self.assertFalse(p.global_config_developer_choice_available({"USERNAME": "claire", "COMPUTERNAME": "desktop"}))
        self.assertFalse(p.global_config_developer_choice_available({"USERNAME": "other", "COMPUTERNAME": "demona"}))

    def test_snapshot_covers_every_player_setting_and_named_matrix_profiles(self):
        snapshot = p.global_config_snapshot({})
        self.assertEqual(p.GLOBAL_CONFIG_FORMAT, snapshot["format"])
        self.assertEqual(set(p.PLAYER_SETTING_DEFAULTS), set(snapshot["player_settings"]))
        self.assertIn("web_preferences", snapshot)
        self.assertIn("registry_values", snapshot)
        self.assertIn("named_profiles", snapshot["matrix"])

    def test_named_profile_round_trip_uses_persistent_store(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "profiles.json"
            payload = {"format": p.GLOBAL_CONFIG_FORMAT, "player_settings": dict(p.PLAYER_SETTING_DEFAULTS)}
            with mock.patch.object(p, "global_config_profiles_path", return_value=target), mock.patch.object(p, "global_config_snapshot", return_value=dict(payload)):
                saved = p.global_config_save_profile("test profile")
                self.assertEqual("test profile", saved["profile_name"])
                store = json.loads(target.read_text(encoding="utf-8"))
                self.assertEqual("test profile", store["test profile"]["profile_name"])
                with mock.patch.object(p, "_global_config_persist_snapshot") as persist:
                    loaded = p.global_config_load_profile("test profile")
                self.assertEqual("test profile", loaded["profile_name"])
                persist.assert_called_once()
                backups = list(Path(directory).glob("profiles.json.bak.*.replaced-by-chatgpt.bak"))
                self.assertEqual([], backups)

    def test_developer_choice_is_a_separate_pafplayer_dcc_sidecar(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / p.GLOBAL_CONFIG_DCC_FILENAME
            payload = {"format": p.GLOBAL_CONFIG_FORMAT, "player_settings": dict(p.PLAYER_SETTING_DEFAULTS)}
            with mock.patch.object(p, "global_config_dcc_path", return_value=target), mock.patch.object(p, "global_config_developer_choice_available", return_value=True), mock.patch.object(p, "global_config_snapshot", return_value=dict(payload)):
                saved = p.global_config_save_profile("ignored", developer_choice=True)
            self.assertEqual(p.GLOBAL_CONFIG_DEVELOPER_CHOICE_NAME, saved["profile_name"])
            on_disk = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(p.GLOBAL_CONFIG_DEVELOPER_CHOICE_NAME, on_disk["profile_name"])

    def test_web_interface_puts_global_config_at_the_bottom(self):
        html = p._paf_web_html()
        section = html.index('id="globalConfigSection"')
        closing = html.index("</section>", section)
        self.assertLess(section, closing)
        self.assertIn("Global Config", html[section:closing])
        self.assertIn("PAFPlayer.dcc", html[section:closing])

    def test_web_interface_javascript_still_parses(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node required for web JavaScript syntax validation")
        scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", p._paf_web_html(), re.S)
        result = subprocess.run([node, "--check"], input="\n".join(scripts), text=True, encoding="utf-8", capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()

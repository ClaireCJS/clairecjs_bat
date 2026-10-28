import inspect
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PAFPlayer as paf


class V584WebPlaylistTitleTrayTests(unittest.TestCase):
    def test_playlist_config_explains_repair_and_opens_list_separately(self):
        html = paf._paf_web_html()
        self.assertIn("When F2 renames the currently playing audio file", html)
        self.assertIn('id="webPlaylistOpen"', html)
        self.assertIn("window.open('/?view=playlist'", html)
        self.assertIn(".playlist-only .playlist-queue-exp{display:block}", html)

    def test_title_test_uses_three_dropdowns_with_choice_marks(self):
        selects = {item["key"]: item for item in paf.paf_web_control_schema()["selects"]}
        for key in ("console_title_shape", "console_title_coloring", "console_title_content"):
            self.assertTrue(selects[key]["choice_marks"])
            self.assertTrue(selects[key]["experimental"])
        html = paf._paf_web_html()
        self.assertNotIn('id="consoleTitleDropdown"', html)
        self.assertIn("Test selected title for 5 seconds", html)

    def test_large_audio_device_default_uses_fallback_after_dword_overflow(self):
        source = inspect.getsource(paf.save_user_default)
        self.assertIn("OverflowError", source)
        self.assertIn("_save_choice_marks_fallback", source)

    def test_tray_hover_art_size_is_live_and_persistent(self):
        tray_source = paf._PAF_BUNDLED_SOURCES["PAFPlayer_tray"]
        hover_source = paf._PAF_BUNDLED_SOURCES["PAFPlayer_tray_hover"]
        options_source = paf._PAF_BUNDLED_SOURCES["PAFPlayer_tray_options"]
        self.assertIn("TrayHoverArtSize", tray_source)
        self.assertIn("def set_art_size", hover_source)
        self.assertIn("Hover artwork size:", options_source)
        self.assertIn("art_preview.configure(width=size, height=size)", options_source)

    def test_lock_screen_status_install_and_confirmed_test_controls(self):
        source = paf._PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"]
        self.assertIn("Test Lock Screen Now", source)
        self.assertIn("Install / repair integration", source)
        self.assertIn("def uac_enabled", source)
        self.assertIn("turn UAC on, reboot Windows", source)
        self.assertIn("confirm('Lock this Windows workstation now", source)

    def test_folder_monitor_results_start_collapsed_with_explanation(self):
        source = paf._PAF_BUNDLED_SOURCES["PAFPlayer_workflows_ui"]
        self.assertIn('<details id="monitorResults">', source)
        self.assertNotIn('<details id="monitorResults" open', source)
        self.assertIn("Dry-run preview reports what would be found", source)
        self.assertIn("does not rename, retag, move, or delete audio files", source)

    def test_v585_web_tray_icon_uses_separate_type_and_color_buttons(self):
        source = paf._PAF_BUNDLED_SOURCES["PAFPlayer_tray"]
        self.assertIn('id="trayIconTypes"', source)
        self.assertIn('id="trayIconColors"', source)
        self.assertIn("function applySelection()", source)
        self.assertIn("selectedMotif", source)
        self.assertIn("selectedBackground", source)
        self.assertNotIn('id="trayIconGallery"', source)


if __name__ == "__main__":
    unittest.main()

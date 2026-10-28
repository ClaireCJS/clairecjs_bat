import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v543", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class V543Tests(unittest.TestCase):
    def test_f2_mapping_has_no_duplicate(self):
        self.assertEqual(PAF.RENAME_CURRENT_FILE, PAF.interpret_console_key("\0", extended="<"))
        self.assertEqual(PAF.KARAOKE_PREVIOUS, PAF.interpret_console_key("\0", extended="<", ctrl=True))
        self.assertEqual(PAF.KARAOKE_TREATMENT_PREVIOUS,
                         PAF.interpret_console_key("\0", extended="<", ctrl=True, shift=True))
        self.assertEqual(PAF.KARAOKE_TREATMENT_PREVIOUS,
                         PAF.interpret_console_key("\0", extended="<", shift=True))

    def test_rename_repairs_current_and_neighboring_playlists(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            track = root / "old song.mp3"
            track.write_bytes(b"audio")
            current = root / "current.m3u8"
            other = root / "other.pls"
            current.write_text("#EXTM3U\nold song.mp3\n", encoding="utf-8")
            other.write_text("[playlist]\nFile1=old song.mp3\nNumberOfEntries=1\n", encoding="utf-8")
            renamed, repaired = PAF.rename_current_audio_file(
                track, "new song", current, repair_current=True, repair_others=True)
            self.assertEqual(root / "new song.mp3", renamed)
            self.assertFalse(track.exists())
            self.assertTrue(renamed.exists())
            self.assertIn("new song.mp3", current.read_text(encoding="utf-8"))
            self.assertIn("new song.mp3", other.read_text(encoding="utf-8"))
            self.assertEqual({current, other}, {path for path, count in repaired if count == 1})
            self.assertTrue(list(root.glob("current.m3u8.bak.*.replaced-by-chatgpt*.bak")))
            self.assertTrue(list(root.glob("other.pls.bak.*.replaced-by-chatgpt*.bak")))

    def test_web_cleanup_contract(self):
        page = PAF._paf_web_html()
        self.assertIn(">Show tags</button>", page)
        self.assertIn("button.textContent='Hide tags'", page)
        self.assertIn("[...logs].reverse().map", page)
        self.assertNotIn("Icon visible</", page)
        self.assertNotIn("Official instance owns the tray", page)
        self.assertIn("Turn off PAFPlayer global hotkeys?", page)
        self.assertNotIn("Off by default until verified on your Windows installation", page)
        self.assertNotIn("r'''\\n<script>(()=>", (ROOT / "src" / "PAFPlayer_tray.py").read_text(encoding="utf-8"))

    def test_v544_profile_help_and_tray_contract(self):
        page = PAF._paf_web_html()
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8")
        tray = (ROOT / "src" / "PAFPlayer_tray.py").read_text(encoding="utf-8")
        discord = (ROOT / "src" / "PAFPlayer_discord.py").read_text(encoding="utf-8")
        self.assertIn("Demo: Style 1 + Spectral Flux + Beat illumination + Flash Full", page)

    def test_v545_help_sort_and_tray_refresh_contract(self):
        page = PAF._paf_web_html()
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8")
        tray = (ROOT / "src" / "PAFPlayer_tray.py").read_text(encoding="utf-8")
        discord = (ROOT / "src" / "PAFPlayer_discord.py").read_text(encoding="utf-8")
        self.assertLess(source.index('return (0, ord(upper), upper)'),
                        source.index('return (2, int(match.group(1)), upper)'))
        self.assertIn('return (1, single_named.get(upper, 1000 + ord(upper[0])), upper)', source)
        self.assertIn("self._requested_icon_style = value", tray)
        self.assertIn("self._icon_applied.wait(1.5)", tray)
        self.assertIn("self.NIM_DELETE", tray)
        self.assertIn("help_key_order_mode", source)
        self.assertIn('return (0, ord(upper), upper)', source)
        self.assertIn('values = ", ".join(key + "=" + description', source)
        self.assertIn("Discord Application ID", page)
        self.assertNotIn("discordWebhookInput", page)
        self.assertIn("SET_ACTIVITY", discord)
        self.assertIn("discord-ipc-", discord)
        spec = importlib.util.spec_from_file_location("pafplayer_tray_v544", ROOT / "src" / "PAFPlayer_tray.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.assertEqual(200, len(module.TRAY_ICON_STYLES))
        self.assertIn("SetMenuItemInfoW", tray)
        self.assertIn("for type_index, (_type_key, type_label) in enumerate(TRAY_ICON_TYPES)", tray)
        self.assertIn("for color_index, (_color_key, color_label", tray)


if __name__ == "__main__":
    unittest.main()

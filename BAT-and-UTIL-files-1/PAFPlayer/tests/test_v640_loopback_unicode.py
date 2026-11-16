"""V640 RAM loopback retry and floating lyric glyph coverage regressions."""

from __future__ import annotations

import os
from pathlib import Path
import unittest

import PAFPlayer as app


class LoopbackReconnectTests(unittest.TestCase):
    def _command(self, builder, input_url):
        options = dict(
            bass_boost_enabled=False, bass_boost_percent=0,
            reduce_bass_when_locked=False, locked_bass_reduction_percent=0,
            session_locked=False, input_url=input_url,
        )
        return builder(Path("ffmpeg.exe"), Path("song.mp3"), 0.94, 0, 1.0, 2, 0,
                       **options)

    def test_ram_input_reconnects_in_both_audio_paths(self):
        for builder in (app.ffplay_command, app.matrixmixer_inspired_ffmpeg_command):
            with self.subTest(builder=builder.__name__):
                command = self._command(builder, "http://127.0.0.1:12345/track.mp3")
                index = command.index("-reconnect")
                self.assertEqual(["-reconnect", "1", "-reconnect_delay_max", "2"],
                                 command[index:index + 4])
                self.assertLess(index, command.index("http://127.0.0.1:12345/track.mp3"))

    def test_file_input_does_not_use_http_reconnect(self):
        for builder in (app.ffplay_command, app.matrixmixer_inspired_ffmpeg_command):
            with self.subTest(builder=builder.__name__):
                command = self._command(builder, None)
                self.assertNotIn("-reconnect", command)


class FloatingLyricGlyphTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows fonts are required")
    def test_japanese_lyric_uses_installed_covered_font(self):
        try:
            from PIL import ImageFont
            from fontTools.ttLib import TTFont  # noqa: F401
        except ImportError:
            self.skipTest("WARNING: Pillow or fontTools unavailable")
        fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        primary_path = fonts / "segoeuib.ttf"
        if not primary_path.is_file():
            self.skipTest("WARNING: Segoe UI font unavailable")
        primary = ImageFont.truetype(str(primary_path), 48)
        lyric = "手を伸ばせば巡り巡るめくるめく夢見て"
        primary_coverage = app._paf_pillow_font_codepoints(str(primary_path))
        self.assertNotIn(ord("手"), primary_coverage)
        for character in lyric:
            selected = app._paf_pillow_lyric_font_for_run(
                character, False, primary, None, fonts)
            self.assertIn(ord(character),
                          app._paf_pillow_font_codepoints(str(selected.path)),
                          f"No floating lyric glyph for {character}")

    @unittest.skipUnless(os.name == "nt", "Windows fonts are required")
    def test_font_collection_coverage_is_read(self):
        path = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "meiryob.ttc"
        if not path.is_file():
            self.skipTest("WARNING: Meiryo TTC unavailable")
        try:
            from fontTools.ttLib import TTFont  # noqa: F401
        except ImportError:
            self.skipTest("WARNING: fontTools unavailable")
        self.assertIn(ord("手"), app._paf_pillow_font_codepoints(str(path)))


if __name__ == "__main__":
    unittest.main()

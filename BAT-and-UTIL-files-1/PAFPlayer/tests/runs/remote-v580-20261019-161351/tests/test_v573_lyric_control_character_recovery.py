"""Recover Windows-1252 punctuation that arrived as C1 lyric controls."""

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v573_lyrics", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class LyricControlCharacterTests(unittest.TestCase):
    def test_c1_control_becomes_the_printable_per_mille_sign(self):
        self.assertEqual("The odds are 5‰ tonight", PAF.renderable_lyric_text("The odds are 5\x89 tonight"))
        self.assertEqual("“Sing” — loud", PAF.renderable_lyric_text("\x93Sing\x94 \x97 loud"))
        self.assertEqual("A\x81B", PAF.renderable_lyric_text("A\x81B"))
        self.assertEqual("Déjà vu 🎵 ‰", PAF.renderable_lyric_text("Déjà vu 🎵 ‰"))

    def test_sidecar_recovers_raw_cp1252_and_utf8_encoded_control(self):
        path = Path("lyric.srt")
        raw = b"1\n00:00:01,000 --> 00:00:03,000\n5\x89 chance\n"
        with mock.patch.object(Path, "read_bytes", return_value=raw):
            self.assertIn("5‰ chance", PAF._read_lyrics_sidecar_text(path))
        encoded_control = "1\n00:00:01,000 --> 00:00:03,000\n5\x89 chance\n".encode("utf-8")
        with mock.patch.object(Path, "read_bytes", return_value=encoded_control):
            self.assertIn("5‰ chance", PAF._read_lyrics_sidecar_text(path))

    def test_timed_and_plain_lyrics_reach_playback_as_printable_text(self):
        audio = Path("song.mp3")
        with mock.patch.object(PAF, "_find_timed_lyric_sidecar", return_value=audio.with_suffix(".srt")), \
             mock.patch.object(Path, "read_bytes", return_value=b"1\n00:00:01,000 --> 00:00:03,000\n5\x89 chance\n"):
            self.assertEqual("5‰ chance", PAF.load_lyrics(audio)[0][2])
        with mock.patch.object(PAF, "_find_timed_lyric_sidecar", return_value=None), \
             mock.patch.object(Path, "is_file", autospec=True, side_effect=lambda path: path.suffix == ".txt"), \
             mock.patch.object(Path, "read_bytes", return_value=b"5\x89 chance\n"):
            self.assertEqual("5‰ chance", PAF.load_lyrics(audio)[0][2])
        self.assertEqual("5‰ chance", PAF.parse_timed_lyrics_text("[00:01.00]5\x89 chance", "lrc")[0][2])

    def test_floating_renderer_repairs_direct_runtime_text(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8")
        self.assertIn('raw_source = renderable_lyric_text(lyric).strip()', source)
        self.assertIn('lyric = renderable_lyric_text(state.get("lyric_floating", state.get("lyric", ""))).strip()', source)


if __name__ == "__main__":
    unittest.main()

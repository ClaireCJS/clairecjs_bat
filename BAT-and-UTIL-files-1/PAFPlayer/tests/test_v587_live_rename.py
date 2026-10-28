"""Focused Windows F2 live-rename regressions without audible playback."""

import importlib.util
import inspect
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import wave

from send2trash import send2trash


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v587", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class LiveRenameTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp(prefix="paf-v587-rename-"))

    def tearDown(self):
        if self.folder.exists():
            send2trash(str(self.folder))

    def test_live_rename_preserves_identity_and_repairs_playlist(self):
        old = self.folder / "old.wav"
        old.write_bytes(b"audio")
        playlist = self.folder / "queue.m3u8"
        playlist.write_text("old.wav\n", encoding="utf-8")
        new, repaired = PAF.rename_current_audio_file(
            old, "new", playlist, repair_current=True, live_playback=True,
        )
        self.assertTrue(old.samefile(new))
        self.assertEqual([(playlist, 1)], repaired)
        self.assertIn("new.wav", playlist.read_text(encoding="utf-8"))
        self.assertEqual([], PAF.retire_live_audio_names([old], new))
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())

    def test_f2_editor_does_not_block_running_playback(self):
        source = inspect.getsource(PAF.play_audio_file)
        handler = source.split("if action_value == RENAME_CURRENT_FILE:", 1)[1].split(
            "if action_value == TEST_TONE_LOAD:", 1
        )[0]
        self.assertIn("rename_editor.start(audio_path)", handler)
        self.assertNotIn("input(", handler)
        self.assertIn("live_rename_callback", handler)
        self.assertIn("continue", handler)
        self.assertNotIn("stop_process(", handler)
        self.assertNotIn("set_paused(", handler)

    def test_multiple_renames_retire_each_old_name(self):
        old = self.folder / "first.flac"
        old.write_bytes(b"audio")
        middle, _ = PAF.rename_current_audio_file(old, "second", live_playback=True)
        final, _ = PAF.rename_current_audio_file(middle, "third", live_playback=True)
        self.assertEqual([], PAF.retire_live_audio_names([old, middle], final))
        self.assertFalse(old.exists())
        self.assertFalse(middle.exists())
        self.assertTrue(final.exists())

    def test_collision_and_changed_identity_are_safe(self):
        old = self.folder / "old.mp3"
        other = self.folder / "other.mp3"
        old.write_bytes(b"old")
        other.write_bytes(b"other")
        with self.assertRaises(FileExistsError):
            PAF.rename_current_audio_file(old, "other", live_playback=True)
        recycled = []
        failures = PAF.retire_live_audio_names([old], other, recycle=recycled.append)
        self.assertEqual([], recycled)
        self.assertEqual(1, len(failures))
        self.assertTrue(old.exists())

    @unittest.skipUnless(os.name == "nt" and shutil.which("ffmpeg"), "Windows FFmpeg required")
    def test_ffmpeg_keeps_reading_during_live_rename(self):
        old = self.folder / "playing.wav"
        with wave.open(str(old), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(8000)
            output.writeframes(b"\0\0" * 8000 * 20)
        process = subprocess.Popen(
            [shutil.which("ffmpeg"), "-nostdin", "-re", "-i", str(old), "-f", "null", "NUL"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(0.4)
            self.assertIsNone(process.poll())
            new, _ = PAF.rename_current_audio_file(old, "renamed", live_playback=True)
            self.assertIsNone(process.poll())
            self.assertTrue(old.samefile(new))
        finally:
            process.terminate()
            process.wait(timeout=5)
        self.assertEqual([], PAF.retire_live_audio_names([old], new))
        self.assertFalse(old.exists())
        self.assertTrue(new.exists())


if __name__ == "__main__":
    unittest.main()

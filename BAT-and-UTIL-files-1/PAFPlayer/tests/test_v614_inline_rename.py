"""Regression tests for the nonblocking F2 filename editor."""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from send2trash import send2trash


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v614", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class InlineEditorTests(unittest.TestCase):
    def test_prefilled_name_edits_in_place_and_caret_is_visible(self):
        editor = PAF.InlineRenameEditor()
        editor.start(Path("original.flac"))
        self.assertEqual("original.flac", editor.text)
        self.assertEqual(len("original"), editor.cursor)
        editor.feed_key("X")
        self.assertEqual("originalX.flac", editor.text)
        editor.feed_key("\0", "K")
        editor.feed_key("\b")
        self.assertEqual("originaX.flac", editor.text)
        prompt, column = editor.display(80)
        self.assertIn("originaX.flac", prompt)
        self.assertGreater(column, len("✏ Rename: "))
        self.assertIn("Enter: save", prompt)
        self.assertEqual(PAF.RENAME_EDITOR_COMMIT, editor.feed_key("\r"))
        self.assertTrue(editor.active)
        self.assertEqual(PAF.RENAME_EDITOR_CANCEL, editor.feed_key("\x1b"))
        editor.close()
        self.assertFalse(editor.active)

    def test_long_filename_scrolls_to_keep_caret_in_view(self):
        editor = PAF.InlineRenameEditor()
        editor.start(Path("a" * 100 + ".mp3"))
        prompt, column = editor.display(32)
        self.assertLess(PAF.terminal_cell_width(prompt), 32)
        self.assertGreaterEqual(column, 1)
        self.assertLess(column, 32)

    def test_arrow_home_end_delete_and_modifier_guard(self):
        editor = PAF.InlineRenameEditor()
        editor.start(Path("abc.wav"))
        editor.feed_key("\0", "G")
        editor.feed_key("Z")
        editor.feed_key("\0", "M")
        editor.feed_key("\0", "S")
        editor.feed_key("\0", "O")
        editor.feed_key("!", ctrl=True)
        self.assertEqual("Zac.wav", editor.text)


class PlaybackHandoffTests(unittest.TestCase):
    class FakeProcess:
        def __init__(self, end_after=None):
            self.polls = 0
            self.end_after = end_after
            self.ended = False

        def poll(self):
            self.polls += 1
            return 0 if self.ended or (self.end_after is not None and self.polls >= self.end_after) else None

        def terminate(self):
            self.ended = True

        def wait(self, timeout=None):
            self.ended = True
            return 0

        def kill(self):
            self.ended = True

    def test_editor_survives_automatic_track_completion_and_renames_old_track(self):
        folder = Path(tempfile.mkdtemp(prefix="paf-v614-rename-"))
        first = folder / "first.mp3"
        second = folder / "second.mp3"
        first.write_bytes(b"audio")
        second.write_bytes(b"audio")
        editor = PAF.InlineRenameEditor()
        callbacks = []
        processes = []

        def run(track, actions, end_after=None):
            actions = iter(actions)
            def read():
                return next(actions, None)
            def factory(*_args, **_kwargs):
                process = self.FakeProcess(end_after)
                processes.append(process)
                return process
            def rename(old, requested, *, live_playback=True):
                callbacks.append((Path(old), requested, live_playback))
                return PAF.rename_current_audio_file(old, requested, live_playback=live_playback)
            with mock.patch.object(PAF, "_RUNTIME_SETTINGS_UNDO_STACK", []), \
                 contextlib.redirect_stdout(io.StringIO()):
                return PAF.play_audio_file(
                    track, ffplay=Path("ffplay.exe"), duration_probe=lambda _path: 0.2,
                    replaygain_probe=lambda _path, _mode: PAF.calculate_replaygain_info({}, "off"),
                    key_action_reader=read, process_factory=factory,
                    live_rename_callback=rename, rename_editor_state=editor,
                    install_signal_handlers=False, drcs_visualizer=False,
                    sixel_visualizer=False, lyrics_display=False, looping=False,
                )

        try:
            self.assertEqual("completed", run(first, [PAF.RENAME_CURRENT_FILE], end_after=5))
            self.assertTrue(editor.active)
            self.assertEqual(first, editor.target)
            editor.text = "renamed.mp3"
            self.assertEqual("stopped", run(second, [PAF.RENAME_EDITOR_COMMIT, PAF.STOP]))
            self.assertEqual([(first, "renamed.mp3", False)], callbacks)
            self.assertTrue((folder / "renamed.mp3").exists())
            self.assertTrue(second.exists())
            self.assertFalse(editor.active)
            self.assertTrue(all(process.poll() is not None for process in processes))
        finally:
            send2trash(str(folder))

    def test_commit_during_playback_stages_name_without_restarting_audio(self):
        folder = Path(tempfile.mkdtemp(prefix="paf-v614-live-"))
        original = folder / "original.mp3"
        original.write_bytes(b"audio")
        editor = PAF.InlineRenameEditor()
        actions = iter((PAF.RENAME_CURRENT_FILE, PAF.RENAME_EDITOR_COMMIT, PAF.STOP))
        processes = []
        caret_seen = []

        def read():
            action = next(actions, None)
            if action == PAF.RENAME_EDITOR_COMMIT:
                caret_seen.append("\033[?25h" in PAF._INLINE_RENAME_CURSOR_SUFFIX)
                editor.text = "updated.mp3"
            return action

        def factory(*_args, **_kwargs):
            process = self.FakeProcess()
            processes.append(process)
            return process

        try:
            with mock.patch.object(PAF, "_RUNTIME_SETTINGS_UNDO_STACK", []), \
                 contextlib.redirect_stdout(io.StringIO()):
                result = PAF.play_audio_file(
                    original, ffplay=Path("ffplay.exe"), duration_probe=lambda _path: 60.0,
                    replaygain_probe=lambda _path, _mode: PAF.calculate_replaygain_info({}, "off"),
                    key_action_reader=read, process_factory=factory,
                    rename_editor_state=editor,
                    install_signal_handlers=False, drcs_visualizer=False,
                    sixel_visualizer=False, lyrics_display=False, looping=False,
                )
            self.assertEqual("stopped", result)
            self.assertEqual([True], caret_seen)
            self.assertEqual(1, len(processes))
            self.assertFalse(original.exists())
            self.assertTrue((folder / "updated.mp3").exists())
            self.assertFalse(editor.active)
            self.assertEqual("", PAF._INLINE_RENAME_CURSOR_SUFFIX)
        finally:
            send2trash(str(folder))


if __name__ == "__main__":
    unittest.main()

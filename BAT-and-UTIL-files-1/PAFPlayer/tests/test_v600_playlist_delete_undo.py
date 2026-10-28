"""V600 Delete-key playlist save, undo, and navigation regressions."""

import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from send2trash import send2trash

import PAFPlayer as app


class PlaylistFileDeletionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="paf-v600-delete-"))
        self.first = self.root / "A.mp3"
        self.second = self.root / "B.mp3"
        self.first.write_bytes(b"first audio")
        self.second.write_bytes(b"second audio")
        self.playlist = self.root / "songs.m3u"
        self.original = b"#EXTM3U\r\nA.mp3\r\nB.mp3\r\n"
        self.playlist.write_bytes(self.original)

    def tearDown(self):
        send2trash(str(self.root))

    def test_stage_is_memory_only_and_saved_delete_has_verified_backup(self):
        self.assertEqual(1, app.remove_track_from_playlist_file(self.playlist, self.first, write=False))
        self.assertEqual(self.original, self.playlist.read_bytes())
        self.assertFalse(list(self.root.glob("songs.m3u.bak.*.replaced-by-chatgpt*.bak")))
        self.assertEqual(1, app.remove_track_from_playlist_file(self.playlist, self.first))
        after = self.playlist.read_bytes()
        self.assertNotIn(b"A.mp3", after)
        self.assertTrue(self.first.is_file())
        backups = list(self.root.glob("songs.m3u.bak.*.replaced-by-chatgpt*.bak"))
        self.assertEqual(1, len(backups))
        self.assertEqual(self.original, backups[0].read_bytes())
        self.assertTrue(app.restore_playlist_file_snapshot(self.playlist, after, self.original))
        self.assertEqual(self.original, self.playlist.read_bytes())
        self.assertEqual(2, len(list(self.root.glob("songs.m3u.bak.*.replaced-by-chatgpt*.bak"))))

    def test_undo_refuses_to_overwrite_a_later_playlist_edit(self):
        app.remove_track_from_playlist_file(self.playlist, self.first)
        after = self.playlist.read_bytes()
        app._global_config_backup_before_replacement(self.playlist)
        self.playlist.write_bytes(after + b"# later edit\n")
        self.assertFalse(app.restore_playlist_file_snapshot(self.playlist, after, self.original))
        self.assertIn(b"later edit", self.playlist.read_bytes())


class DeleteSavePromptTests(unittest.TestCase):
    def choice(self, key=None):
        tick = [0.0]
        shown = []

        def now():
            return tick[0]

        def sleep(seconds):
            tick[0] += seconds

        def read_key():
            return key if tick[0] == 0 else None

        result = app.playlist_delete_save_choice(read_key, lambda: True, now, sleep, shown.append)
        return result, tick[0], shown

    def test_timeout_defaults_yes_after_eight_seconds(self):
        result, elapsed, shown = self.choice()
        self.assertEqual("save", result)
        self.assertGreaterEqual(elapsed, 8.0)
        self.assertEqual(8, shown[0])
        self.assertEqual(0, shown[-1])

    def test_explicit_no_enter_and_undo(self):
        for key, expected in (("n", "session"), ("N", "session"), ("\r", "save"),
                              ("y", "save"), ("\x1a", "undo"), ("\x1b", "undo"),
                              ("\x03", "abort")):
            with self.subTest(key=key):
                result, elapsed, _shown = self.choice(key)
                self.assertEqual(expected, result)
                self.assertEqual(0.0, elapsed)


class PlaybackDeleteTests(unittest.TestCase):
    class FakeProcess:
        def __init__(self):
            self.ended = False
        def poll(self):
            return 0 if self.ended else None
        def terminate(self):
            self.ended = True
        def wait(self, timeout=None):
            self.ended = True
            return 0
        def kill(self):
            self.ended = True

    def run_actions(self, actions, *, choice="save"):
        root = Path(tempfile.mkdtemp(prefix="paf-v600-playback-"))
        audio = root / "A.mp3"
        audio.write_bytes(b"test audio")
        calls = []
        created = []
        kind = [None]

        def stage(path):
            calls.append(("stage", Path(path)))
            kind[0] = "playlist"
            return 1

        def save():
            calls.append(("save", None))
            return True

        def undo():
            calls.append(("undo", None))
            return True

        def factory(*_args, **_kwargs):
            process = self.FakeProcess()
            created.append(process)
            return process

        try:
            with mock.patch.object(app, "playlist_delete_save_choice", return_value=choice), \
                 mock.patch.object(app, "_RUNTIME_SETTINGS_UNDO_STACK", []), \
                 contextlib.redirect_stdout(io.StringIO()):
                result = app.play_audio_file(
                    audio, ffplay=Path("ffplay.exe"),
                    duration_probe=lambda _path: 60.0,
                    replaygain_probe=lambda _path, _mode: app.calculate_replaygain_info({}, "off"),
                    key_action_reader=iter(actions).__next__, process_factory=factory,
                    playlist_remove_callback=lambda _path: self.fail("Delete should stage first"),
                    playlist_stage_delete_callback=stage,
                    playlist_save_delete_callback=save,
                    playlist_undo_callback=undo,
                    playlist_has_undo_callback=lambda: True,
                    playlist_undo_kind_state=kind,
                    playlist_display=str(root / "songs.m3u"),
                    install_signal_handlers=False, drcs_visualizer=False,
                    sixel_visualizer=False, lyrics_display=False,
                )
            return result, calls, created
        finally:
            send2trash(str(root))

    def test_delete_saves_without_restarting_current_song(self):
        result, calls, created = self.run_actions((app.PLAYLIST_DELETE_CURRENT, app.STOP))
        self.assertEqual("stopped", result)
        self.assertEqual(["stage", "save"], [name for name, _value in calls])
        self.assertEqual(1, len(created))

    def test_ctrl_z_uses_playlist_undo_after_delete(self):
        result, calls, created = self.run_actions((app.PLAYLIST_DELETE_CURRENT, app.UNDO_LAST_CHANGE, app.STOP))
        self.assertEqual("stopped", result)
        self.assertEqual(["stage", "save", "undo"], [name for name, _value in calls])
        self.assertEqual(1, len(created))

    def test_no_keeps_session_removal_and_ctrl_z_restores_it(self):
        result, calls, created = self.run_actions(
            (app.PLAYLIST_DELETE_CURRENT, app.UNDO_LAST_CHANGE, app.STOP), choice="session"
        )
        self.assertEqual("stopped", result)
        self.assertEqual(["stage", "undo"], [name for name, _value in calls])
        self.assertEqual(1, len(created))

    def test_next_then_previous_cannot_visit_removed_song(self):
        root = Path(tempfile.mkdtemp(prefix="paf-v600-nav-"))
        try:
            first, second, third = (root / name for name in ("A.mp3", "B.mp3", "C.mp3"))
            for path in (first, second, third):
                path.write_bytes(b"audio")
            remaining = [second, third]
            history, cursor = app.prune_playlist_visit_history(
                [first], 0, {str(first).casefold()}, lambda path: str(path).casefold()
            )
            self.assertEqual(([], -1), (history, cursor))
            next_track, cursor = app.advance_playlist_visit_history(
                history, cursor, app.NEXT_FILE,
                lambda direction: remaining[0] if direction >= 0 else remaining[-1],
            )
            previous, cursor = app.advance_playlist_visit_history(
                history, cursor, app.PREVIOUS_FILE,
                lambda direction: app.playlist_queue_neighbor_distinct(remaining, next_track, direction),
            )
            self.assertEqual(second, next_track)
            self.assertEqual(third, previous)
            self.assertNotIn(first, history)
        finally:
            send2trash(str(root))


if __name__ == "__main__":
    unittest.main()

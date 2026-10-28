"""Queued-only removal, live browser reconciliation, and remote Pause controls."""

from pathlib import Path
import contextlib
import io
import msvcrt
import os
import unittest
from unittest import mock

import PAFPlayer as app
from PAFPlayer_remote_tray import RemoteHotkeys


class QueuedOnlyDeletionTests(unittest.TestCase):
    def test_live_queue_membership_is_enough_without_a_disk_playlist_row(self):
        song = Path("C:/music/queued-only.mp3")
        self.assertEqual(1, app.active_playlist_removal_count(0, [(4, song)], [], []))
        self.assertEqual(1, app.active_playlist_removal_count(0, [], [], [(0, song)]))
        self.assertEqual(0, app.active_playlist_removal_count(0, [], [], []))


class LiveBrowserTests(unittest.TestCase):
    def test_external_insert_preserves_focus_and_selection(self):
        a, b, c, incoming = [Path(f"C:/music/{name}.mp3") for name in "abci"]
        cursor, selected = app.rebase_playlist_browser_selection(
            [a, b, c], [a, incoming, b, c], 1, {1, 2}
        )
        self.assertEqual(2, cursor)
        self.assertEqual({2, 3}, selected)

    def test_duplicate_occurrences_stay_distinct(self):
        a, b, incoming = [Path(f"C:/music/{name}.mp3") for name in "abi"]
        cursor, selected = app.rebase_playlist_browser_selection(
            [a, b, a], [incoming, a, b, a], 2, {2}
        )
        self.assertEqual(3, cursor)
        self.assertEqual({3}, selected)

    def test_multiple_selected_rows_move_together_without_reordering_them(self):
        paths = [Path(f"C:/music/{name}.mp3") for name in "abcd"]
        moved, focused, selected = app.move_playlist_browser_selection(paths, {1, 2}, 1)
        self.assertEqual([paths[0], paths[3], paths[1], paths[2]], moved)
        self.assertEqual((2, {2, 3}), (focused, selected))
        original, _, selected = app.move_playlist_browser_selection(moved, selected, -1)
        self.assertEqual(paths, original)
        self.assertEqual({1, 2}, selected)

    def test_browser_delete_copy_and_undo_route_selected_paths(self):
        paths = [Path(f"C:/music/{name}.mp3") for name in "abc"]
        keys = list(" \x03\x00S\x1a\x1b")
        deleted, copied, undone = [], [], []
        with mock.patch.object(app, "windows_console_ctrl_c_as_key", return_value=contextlib.nullcontext()), \
             mock.patch.object(app, "_windows_key_down", return_value=False), \
             mock.patch.object(msvcrt, "kbhit", side_effect=lambda: bool(keys)), \
             mock.patch.object(msvcrt, "getwch", side_effect=lambda: keys.pop(0)), \
             mock.patch.object(app, "write_console"), contextlib.redirect_stdout(io.StringIO()):
            app.interactive_playlist_browser(
                paths, 0, initial_direction=1,
                delete_callback=lambda selected: deleted.append(selected) or len(selected),
                copy_callback=lambda selected: copied.append(selected),
                undo_callback=lambda: undone.append(True) or True,
            )
        self.assertEqual([[paths[1]]], deleted)
        self.assertEqual([[paths[1]]], copied)
        self.assertEqual([True], undone)


class RemotePauseTests(unittest.TestCase):
    @staticmethod
    def press(hotkeys, *names, now=1.0):
        down = {hotkeys.VK[name] for name in names}
        return hotkeys.sample(lambda code: code in down, now=now, epoch=100.0)

    def test_pause_and_media_play_pause_relay_once_per_press(self):
        hotkeys = RemoteHotkeys()
        self.assertEqual([("server", "pause", 100.0)], self.press(hotkeys, "pause_key"))
        self.assertEqual([], self.press(hotkeys, "pause_key", now=1.1))
        self.assertEqual([], self.press(hotkeys, now=1.2))
        self.assertEqual([("server", "pause", 100.0)], self.press(hotkeys, "media_pause", now=1.3))
        self.assertEqual([], self.press(hotkeys, now=1.4))
        self.assertEqual([("server", "pause", 100.0)], self.press(hotkeys, "pause_key", "media_pause", now=1.5))


if __name__ == "__main__":
    unittest.main()

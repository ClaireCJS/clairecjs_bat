"""Tray icon drop routing and available-memory buffering regression checks."""

import io
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import PAFPlayer  # Install the single-file feature-module finder.
from PAFPlayer_memory_audio import MemoryAudioSource
from PAFPlayer_tray import TrayController, tray_drop_target_rect


class TrayDropTests(unittest.TestCase):
    def test_overlay_arms_only_for_a_held_drag_near_this_icon(self):
        rect = (100, 200, 132, 232)
        self.assertEqual((100, 200, 32, 32),
                         tray_drop_target_rect(rect, (95, 215), True))
        self.assertIsNone(tray_drop_target_rect(rect, (95, 215), False))
        self.assertIsNone(tray_drop_target_rect(rect, (300, 215), True))
        self.assertIsNone(tray_drop_target_rect((100, 200, 100, 232), (100, 210), True))

    def test_drop_queues_on_owner_and_releases_shell_handle_once(self):
        runtime = SimpleNamespace(app=SimpleNamespace(windows_dropped_paths=mock.Mock(
            return_value=[Path('C:/music/song.mp3'), Path('C:/music/album')])), log=mock.Mock())
        instance = SimpleNamespace(owns=mock.Mock(return_value=True))
        queue = mock.Mock(return_value=2)
        tray = TrayController(runtime, instance, True, click_window=.6, drop_callback=queue)

        class ImmediateThread:
            def __init__(self, target, **_kwargs):
                self.target = target

            def start(self):
                self.target()

        with mock.patch('PAFPlayer_tray.threading.Thread', ImmediateThread):
            tray._accept_drop(123)
        runtime.app.windows_dropped_paths.assert_called_once_with(123)
        queue.assert_called_once_with([Path('C:/music/song.mp3'), Path('C:/music/album')])

    def test_non_owner_cannot_queue_a_drop(self):
        runtime = SimpleNamespace(app=SimpleNamespace(windows_dropped_paths=mock.Mock(
            return_value=[Path('C:/music/song.mp3')])), log=mock.Mock())
        tray = TrayController(runtime, SimpleNamespace(owns=lambda: False), True,
                              click_window=.6, drop_callback=mock.Mock())
        tray._accept_drop(99)
        tray.drop_callback.assert_not_called()
        runtime.app.windows_dropped_paths.assert_called_once_with(99)

    def test_remote_settings_object_uses_the_supplied_shell_drop_reader(self):
        reader = mock.Mock(return_value=[])
        runtime = SimpleNamespace(app=SimpleNamespace(), log=mock.Mock())
        tray = TrayController(runtime, SimpleNamespace(owns=lambda: True), True,
                              click_window=.6, drop_callback=mock.Mock(), drop_reader=reader)
        tray._accept_drop(77)
        reader.assert_called_once_with(77)
        tray.drop_callback.assert_not_called()


class MemoryBufferTests(unittest.TestCase):
    def test_track_larger_than_old_64_mib_cap_can_be_buffered(self):
        payload = bytes(65 * 1024 * 1024)
        with mock.patch('PAFPlayer_memory_audio.available_buffer_bytes', return_value=128 * 1024 * 1024), \
             mock.patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=len(payload))), \
             mock.patch.object(Path, 'open', return_value=io.BytesIO(payload)):
            source = MemoryAudioSource.try_open(Path('C:/music/large.flac'))
        self.assertIsNotNone(source)
        try:
            self.assertEqual(len(payload), len(source.data))
        finally:
            source.close()

    def test_insufficient_available_memory_uses_disk_source(self):
        with mock.patch('PAFPlayer_memory_audio.available_buffer_bytes', return_value=32), \
             mock.patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=33)), \
             mock.patch.object(Path, 'open') as opened:
            self.assertIsNone(MemoryAudioSource.try_open(Path('C:/music/song.flac')))
        opened.assert_not_called()


if __name__ == '__main__':
    unittest.main()

import threading
import unittest
from pathlib import Path
from unittest import mock

import play_audio_file as p


class PickerTests(unittest.TestCase):
    def picker(self, events, *, file_selection=None):
        class Console:
            modifiers = (False, False)
            def kbhit(self): return True
            def getwch(self):
                key, ctrl, shift = events.pop(0)
                self.modifiers = (ctrl, shift)
                return key
        console = Console()
        paths = [Path('one.mp3'), Path('two.mp3')]
        catalog = mock.Mock()
        catalog.search.return_value = paths
        catalog.snapshot.return_value = (paths, 'test catalog')
        def key_down(key):
            return console.modifiers[0] if key == 0x11 else console.modifiers[1] if key == 0x10 else False
        jump = [False]
        with mock.patch.dict('sys.modules', {'msvcrt': console}), \
             mock.patch.object(p, '_windows_key_down', side_effect=key_down), \
             mock.patch.object(p, 'traditional_windows_audio_file_picker', return_value=file_selection):
            chosen = p.interactive_audio_catalog_picker(catalog, render_callback=lambda rows: None, jump_state=jump)
        return chosen, jump[0]

    def test_enter_queues_and_shift_enter_jumps(self):
        self.assertEqual((Path('one.mp3'), False), self.picker([('\r', False, False)]))
        self.assertEqual((Path('one.mp3'), True), self.picker([('\r', False, True)]))

    def test_multiselect_retains_both_rows_for_enter(self):
        events = [(' ', True, False), ('\xe0', False, False), ('P', False, False),
                  (' ', True, False), ('\r', False, False)]
        self.assertEqual(((Path('one.mp3'), Path('two.mp3')), False), self.picker(events))

    def test_shift_insert_keeps_all_dialog_selections(self):
        selected = (Path('first.mp3'), Path('second.mp3'))
        self.assertEqual((selected, False), self.picker([('\xe0', False, True), ('R', False, True)], file_selection=selected))

    def test_ctrl_arrow_prefix_is_not_mistaken_for_ctrl_space(self):
        # Ctrl+Down arrives with the null prefix on some Windows consoles.
        events = [('\x00', True, False), ('P', True, False), ('\r', False, False)]
        self.assertEqual((Path('two.mp3'), False), self.picker(events))


class PopupTimelineTests(unittest.TestCase):
    def test_full_future_timeline_advances_without_owner_repainting(self):
        window = object.__new__(p.ExternalAlbumArtWindow)
        window._lock = threading.RLock()
        window._playback_running = True
        window._playback_position = 4.0
        window.update_karaoke_frame = mock.Mock()
        process = mock.Mock(playback_clock={'seconds': 4.0, 'at': 100.0, 'queued_seconds': .5})
        cues = [(0, 3, 'intro'), (3, 6, 'chorus'), (6, 10, 'outro')]
        window.set_playback_clock(process, 0, 1, 90, 10)
        window.set_karaoke_timeline(cues, emojimax=True)
        with mock.patch.object(p.time, 'monotonic', return_value=100), \
             mock.patch.object(p, 'KARAOKE_DISPLAY_OFFSET_SECONDS', 0):
            window.advance_karaoke_timeline()
            self.assertEqual('chorus', window.update_karaoke_frame.call_args.args[0].active_text)
            # Only the audio worker updates; console is still busy in a menu.
            process.playback_clock = {'seconds': 7.0, 'at': 100.0, 'queued_seconds': .5}
            window.advance_karaoke_timeline()
            self.assertEqual('outro', window.update_karaoke_frame.call_args.args[0].active_text)
            window.set_playback_running(False)
            self.assertEqual(4, window.playback_position())


if __name__ == '__main__':
    unittest.main()

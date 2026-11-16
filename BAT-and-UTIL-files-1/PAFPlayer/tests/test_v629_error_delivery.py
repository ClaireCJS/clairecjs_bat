"""V629 unplayable-track recovery and per-file error delivery."""
from pathlib import Path
import base64
import unittest
import uuid
from unittest import mock

import PAFPlayer as player
import PAFPlayer_error_delivery as delivery
from PAFPlayer_workflows import recycle


class ErrorDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / 'runs' / ('v629-' + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(lambda: recycle(self.root))
        self.good = self.root / 'good.flac'
        self.good.write_bytes(b'valid bytes for selection')
        self.empty = self.root / 'empty.flac'
        self.empty.write_bytes(b'')
        self.missing = self.root / 'missing.flac'

    def test_empty_and_missing_entries_skip_to_next_playable(self):
        order = [self.good, self.empty, self.missing]
        self.assertEqual('empty', delivery.file_problem(self.empty))
        self.assertEqual('missing', delivery.file_problem(self.missing))
        self.assertEqual(self.good, delivery.next_playable_entry(order, self.empty))
        self.assertEqual(self.good, delivery.next_playable_entry(order, self.missing))
        self.assertIsNone(delivery.next_playable_entry([self.empty, self.missing], self.empty))

    def test_one_alert_per_error_and_file_revision(self):
        notices = []
        class Tray:
            def notify_error(self, title, message):
                notices.append((title, message))
                return True
        class ImmediateThread:
            def __init__(self, target, args=(), **kwargs):
                self.target, self.args = target, args
            def start(self):
                self.target(*self.args)
        alerts = delivery.ErrorAlerts()
        settings = {'ErrorPopupEnabled': 1, 'ErrorWindowsNotificationEnabled': 1,
                    'ErrorSoundEnabled': 1}
        with mock.patch.object(delivery.threading, 'Thread', ImmediateThread), \
             mock.patch.object(delivery, '_popup') as popup, \
             mock.patch.object(delivery, '_sound') as sound:
            self.assertTrue(alerts.emit(path=self.empty, reason='empty', settings=settings,
                                        tray=Tray(), ffplay_path='ffplay.exe'))
            self.assertFalse(alerts.emit(path=self.empty, reason='empty', settings=settings,
                                         tray=Tray(), ffplay_path='ffplay.exe'))
            self.assertEqual(1, len(notices))
            popup.assert_called_once()
            sound.assert_called_once_with('ffplay.exe')
            self.empty.write_bytes(b'now repaired')
            self.assertTrue(alerts.emit(path=self.empty, reason='empty', settings=settings,
                                        tray=Tray(), ffplay_path='ffplay.exe'))
            self.assertEqual(2, len(notices))

    def test_disabled_delivery_still_marks_error_seen(self):
        class Tray:
            def notify_error(self, *_args):
                raise AssertionError('notification should be disabled')
        alerts = delivery.ErrorAlerts()
        settings = {'ErrorPopupEnabled': 0, 'ErrorWindowsNotificationEnabled': 0,
                    'ErrorSoundEnabled': 0}
        with mock.patch.object(delivery.threading, 'Thread') as thread:
            self.assertTrue(alerts.emit(path=self.empty, reason='empty', settings=settings, tray=Tray()))
            self.assertFalse(alerts.emit(path=self.empty, reason='empty', settings=settings, tray=Tray()))
            thread.assert_not_called()

    def test_bundled_sound_uses_one_percent_ffplay_volume(self):
        data = base64.b64decode(delivery.WILHELM_OGG_B64)
        self.assertEqual(b'OggS', data[:4])
        played = []
        class Process:
            def communicate(self, payload, timeout):
                played.append((payload, timeout))
        with mock.patch.object(delivery.subprocess, 'Popen', return_value=Process()) as popen:
            delivery._sound('ffplay.exe')
        command = popen.call_args.args[0]
        self.assertEqual('1', command[command.index('-volume') + 1])
        self.assertEqual(data, played[0][0])

    def test_popup_uses_independent_process_so_final_error_survives_shutdown(self):
        with mock.patch.object(delivery.os, 'name', 'nt'), \
             mock.patch.object(delivery.subprocess, 'Popen') as popen:
            delivery._popup('PAFPlayer error', 'empty.flac is empty')
        args = popen.call_args.args[0]
        self.assertEqual('PAFPlayer error', args[-2])
        self.assertEqual('empty.flac is empty', args[-1])
        self.assertIn('MessageBoxW', args[2])

    def test_web_schema_and_saved_defaults(self):
        settings = player.load_player_settings(read_only=True)
        for name in ('ErrorPopupEnabled', 'ErrorWindowsNotificationEnabled', 'ErrorSoundEnabled'):
            self.assertEqual(1, player.PLAYER_SETTING_DEFAULTS[name])
            self.assertIn(settings[name], (0, 1))
        keys = {item['key'] for item in player.paf_web_control_schema(include_saved_marks=False)['toggles']}
        for key in ('error_popup_enabled', 'error_windows_notification_enabled', 'error_sound_enabled'):
            self.assertIn(key, keys)
            self.assertTrue(player.paf_web_action_is_allowed('web-set:' + key + ':0'))
            self.assertFalse(player.paf_web_action_is_allowed('web-set:' + key + ':2'))


if __name__ == '__main__':
    unittest.main()

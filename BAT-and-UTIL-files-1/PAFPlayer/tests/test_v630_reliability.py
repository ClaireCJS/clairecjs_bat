"""V630 regressions for randomize handoff and error alert recovery."""
from pathlib import Path
import types
import unittest
import uuid
from unittest import mock

import PAFPlayer as player
from PAFPlayer_error_delivery import ErrorAlerts
from PAFPlayer_instance import Instance, resolve_request
from PAFPlayer_workflows import recycle


class RandomizeReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent / 'runs' / ('v630-' + uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(lambda: recycle(self.root))
        self.song = self.root / 'song.mp3'
        self.song.write_bytes(b'audio')
        self.playlist = self.root / 'list.m3u'
        self.playlist.write_text(str(self.song), encoding='utf-8')

    def instance(self, *, bridge):
        runtime = types.SimpleNamespace(
            root=self.root,
            app=types.SimpleNamespace(AUDIO_EXTENSIONS={'.mp3'}),
            queue_bridge=lambda *_: None,
            randomize_bridge=bridge,
        )
        instance = Instance(runtime)
        instance.start()
        self.addCleanup(instance.close)
        return instance

    def request(self):
        return {'paths': [str(self.song)], 'playlist': str(self.playlist), 'randomize': True}

    def test_bridge_unavailable_rejects_before_queue_mutation(self):
        instance = self.instance(bridge=None)
        with mock.patch('PAFPlayer_web_workflows.edit_queue') as edit:
            with self.assertRaisesRegex(ValueError, 'request was not accepted'):
                instance.forward(self.request())
            edit.assert_not_called()

    def test_randomize_failure_after_load_reports_partial_success(self):
        def failed():
            raise ValueError('action queue is full')
        instance = self.instance(bridge=failed)
        with mock.patch('PAFPlayer_web_workflows.queue_snapshot', return_value={'entries': [], 'revision': 0}), \
             mock.patch('PAFPlayer_web_workflows.edit_queue', return_value={'revision': 1}) as edit:
            result = instance.forward(self.request())
        edit.assert_called_once()
        self.assertTrue(result['ok'])
        self.assertTrue(result['warning'])
        self.assertEqual(1, result['queued'])
        self.assertIn('loaded, but not randomized', result['message'])
        self.assertIn('action queue is full', result['message'])

    def test_malformed_combined_request_never_loads(self):
        instance = self.instance(bridge=lambda: {'message': 'randomized'})
        bad = self.request()
        bad['unexpected'] = 1
        with mock.patch('PAFPlayer_web_workflows.edit_queue') as edit:
            with self.assertRaisesRegex(ValueError, 'Invalid playlist randomize request'):
                instance.forward(bad)
            edit.assert_not_called()

    def test_history_worker_keeps_live_order_and_duplicate_slots(self):
        a, b, c = (Path(name) for name in ('a.mp3', 'b.mp3', 'c.mp3'))
        live = [a, c, b, b]
        self.assertEqual(live, player.preserve_session_randomized_order(live, [a, b, b, c], a))
        self.assertEqual(live, player.preserve_session_randomized_order(live, [c, b, a, b], a))
        changed = player.preserve_session_randomized_order(live, [a, b, c], a)
        self.assertEqual(3, len(changed))
        self.assertCountEqual([a, b, c], changed)

    def test_playlist_request_preserves_repeated_file_slots(self):
        app = types.SimpleNamespace(
            PLAYLIST_EXTENSIONS={'.m3u'},
            AUDIO_EXTENSIONS={'.mp3'},
            load_playlist=lambda *_args, **_kwargs: [self.song, self.song],
        )
        result = resolve_request(types.SimpleNamespace(app=app), [str(self.playlist)])
        self.assertEqual([str(self.song), str(self.song)], result['paths'])
        self.assertEqual(str(self.playlist), result['playlist'])


class ErrorReliabilityTests(unittest.TestCase):
    def test_healthy_transition_rearms_identical_file_error(self):
        alerts = ErrorAlerts()
        path = Path('unavailable-v630.flac')
        disabled = {'ErrorPopupEnabled': 0, 'ErrorSoundEnabled': 0,
                    'ErrorWindowsNotificationEnabled': 0}
        self.assertTrue(alerts.emit(path=path, reason='missing', settings=disabled))
        self.assertFalse(alerts.emit(path=path, reason='missing', settings=disabled))
        alerts.mark_healthy(path)
        self.assertTrue(alerts.emit(path=path, reason='missing', settings=disabled))

    def test_alert_delivery_failure_does_not_interrupt_recovery(self):
        class BrokenTray:
            def notify_error(self, *_args):
                raise RuntimeError('shell is restarting')
        alerts = ErrorAlerts()
        settings = {'ErrorPopupEnabled': 1, 'ErrorSoundEnabled': 1,
                    'ErrorWindowsNotificationEnabled': 1}
        with mock.patch('PAFPlayer_error_delivery.threading.Thread') as thread:
            thread.return_value.start.side_effect = RuntimeError('cannot start thread')
            self.assertTrue(alerts.emit(path='bad-v630.flac', reason='empty',
                                        settings=settings, tray=BrokenTray()))
        self.assertFalse(alerts.emit(path='bad-v630.flac', reason='empty',
                                     settings=settings, tray=BrokenTray()))


if __name__ == '__main__':
    unittest.main()

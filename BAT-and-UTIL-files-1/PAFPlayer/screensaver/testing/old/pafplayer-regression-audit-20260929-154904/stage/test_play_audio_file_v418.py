"""Browser detection, failed-helper fallback, stale data and pause ownership."""
import io
import json
import re
import subprocess
import threading
import time
import unittest
from unittest import mock

import play_audio_file as p


class BrowserDetectionTests(unittest.TestCase):
    def payload(self, browser='chrome', peak=.1):
        return {'known': True, 'winamp': 0, 'smtc_available': True,
                'media': [{'app': browser + '.exe', 'state': 'Paused'}],
                'audio': [{'name': browser, 'state': 1, 'peak': peak}]}

    def test_audio_from_another_tab_overrides_paused_media_session(self):
        for browser in ('chrome', 'opera', 'msedge'):
            self.assertEqual((browser,), p.resolve_external_media_snapshot(self.payload(browser), 1)['active'])

    def test_paused_stream_without_audio_does_not_interrupt(self):
        self.assertEqual((), p.resolve_external_media_snapshot(self.payload(peak=0), 1)['active'])

    def test_playing_transport_holds_through_silence(self):
        payload = self.payload(peak=0)
        payload['media'][0]['state'] = 'Playing'
        self.assertEqual(('chrome',), p.resolve_external_media_snapshot(payload, 1)['active'])

    def test_edge_appid_and_opera_gx(self):
        self.assertEqual('msedge', p.external_media_family('Microsoft.MicrosoftEdge.Stable_8wekyb3d8bbwe!App'))
        self.assertEqual('opera', p.external_media_family('Opera GX Stable'))

    def test_inactive_stream_never_counts_as_playing(self):
        payload = self.payload()
        payload['audio'][0]['state'] = 0
        self.assertEqual((), p.resolve_external_media_snapshot(payload, 1)['active'])

    def test_partial_failure_cannot_hide_positive_playback(self):
        controller = p.PAFExternalPlaybackCoordinator(None)
        controller.last_snapshot = {"known": True, "active": ()}
        controller.filter_action(None, False, 0)
        payload = self.payload()
        payload.update(known=False, error='One other audio endpoint disconnected')
        controller.last_snapshot = p.resolve_external_media_snapshot(payload, 1)
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, controller.filter_action(None, False, 1))
        controller.last_snapshot = {'known': False, 'active': ()}
        self.assertIsNone(controller.filter_action(None, True, 10))

    def test_fallback_resumes_with_fifteen_second_fade_after_quiet(self):
        monitor = p.PAFExternalMediaMonitor()
        monitor._audio_sample = {**self.payload(), 'at': 1}
        monitor._media_sample = {'smtc_available': False, 'error': 'helper cannot start', 'at': 1}
        controller = p.PAFExternalPlaybackCoordinator(None)
        controller.last_snapshot = {"known": True, "active": ()}
        controller.filter_action(None, False, 0)
        controller.last_snapshot = monitor.snapshot(1)
        self.assertTrue(controller.last_snapshot['degraded'])
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, controller.filter_action(None, False, 1))
        monitor._audio_sample = {'audio': [], 'winamp': 0, 'known': True, 'at': 2}
        controller.last_snapshot = monitor.snapshot(2)
        self.assertIsNone(controller.filter_action(None, True, 2))
        self.assertEqual(p.EXTERNAL_MEDIA_RESUME, controller.filter_action(None, True, 4))
        self.assertEqual((15, 0), controller.fade_arguments())

    def test_stale_native_data_is_never_positive_or_quiet_confirmation(self):
        monitor = p.PAFExternalMediaMonitor()
        monitor._audio_sample = {**self.payload(), 'at': 1}
        state = monitor.snapshot(12)
        self.assertFalse(state['known'])
        self.assertEqual((), state['active'])

    def test_lost_working_media_feed_prevents_unsafe_resume(self):
        monitor = p.PAFExternalMediaMonitor()
        monitor._media_was_available = True
        monitor._audio_sample = {'audio': [], 'winamp': 0, 'known': True, 'at': 10}
        monitor._media_sample = {'media': [{'app': 'chrome.exe', 'state': 'Playing'}],
                                 'smtc_available': True, 'at': 1}
        state = monitor.snapshot(10)
        self.assertEqual((), state['active'])
        self.assertFalse(state['known'])
        self.assertIn('not updated', state['error'])

    def test_media_failure_does_not_erase_fresh_native_playback(self):
        monitor = p.PAFExternalMediaMonitor()
        monitor._media_was_available = True
        monitor._audio_sample = {**self.payload(), 'at': 10}
        state = monitor.snapshot(10)
        self.assertFalse(state['known'])
        self.assertEqual(('chrome',), state['active'])

    def test_all_browser_javascript_still_parses(self):
        scripts = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', p._paf_web_html(), re.S))
        result = subprocess.run(['node', '--check'], input=scripts, text=True, encoding='utf-8', capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)


class MonitorThreadTests(unittest.TestCase):
    def test_failed_helper_has_diagnostics_while_native_thread_keeps_working(self):
        sample = {'audio': [{'name': 'chrome', 'state': 1, 'peak': .2}], 'winamp': 0, 'known': True}
        with mock.patch.object(p, 'probe_external_audio_sessions', return_value=sample), \
             mock.patch.object(p.subprocess, 'Popen', side_effect=OSError('test helper failure')):
            monitor = p.PAFExternalMediaMonitor().start()
            try:
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    state = monitor.snapshot()
                    if 'test helper failure' in state.get('smtc_error', ''): break
                    time.sleep(.01)
                self.assertTrue(state['known'])
                self.assertEqual(('chrome',), state['active'])
                self.assertIn('test helper failure', state['smtc_error'])
            finally:
                monitor.close()
            self.assertFalse(monitor._thread.is_alive())
            self.assertFalse(monitor._audio_thread.is_alive())

    def test_exit_code_and_plain_stderr_are_preserved(self):
        monitor = p.PAFExternalMediaMonitor()
        process = mock.Mock(stdout=io.StringIO('Unable to load Windows media API\n'))
        process.wait.return_value = 17
        process.poll.return_value = 17
        # End after one iteration, after recording its exit diagnostics.
        monitor._stop.wait = lambda _: monitor._stop.set()
        with mock.patch.object(p.subprocess, 'Popen', return_value=process) as launch:
            monitor._run()
        self.assertIn('exited 17', monitor._media_sample['error'])
        self.assertIn('Unable to load', monitor._media_sample['error'])
        self.assertEqual(p.subprocess.STDOUT, launch.call_args.kwargs["stderr"])

    def test_hung_helper_is_restarted_independently_of_native_detection(self):
        monitor = p.PAFExternalMediaMonitor()
        process = mock.Mock()
        monitor._process = process
        monitor._helper_started = time.monotonic() - 20
        monitor._stop.wait = lambda _: monitor._stop.set()
        with mock.patch.object(p, 'probe_external_audio_sessions', return_value={'audio': [], 'winamp': 0, 'known': True}):
            monitor._run_audio()
        process.terminate.assert_called_once()


if __name__ == '__main__':
    unittest.main()

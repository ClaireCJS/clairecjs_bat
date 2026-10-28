import array
import math
from pathlib import Path
import subprocess
import unittest

import play_audio_file as p


class Monitor:
    def __init__(self): self.value = {'known': True, 'active': ()}
    def snapshot(self, _now): return self.value


class ExternalMediaTests(unittest.TestCase):
    def make(self):
        monitor = Monitor()
        controller = p.PAFExternalPlaybackCoordinator(monitor)
        controller.filter_action(None, False, 0)
        return controller, monitor

    def test_detect_transport_state_and_active_audio_not_merely_open_processes(self):
        payload = {'known': True, 'winamp': 3, 'media': [{'app': 'chrome.exe', 'state': 'Paused'}],
                   'audio': [{'name': 'chrome', 'state': 1}, {'name': 'vlc', 'state': 0}]}
        self.assertEqual((), p.resolve_external_media_snapshot(payload, 0)['active'])
        payload['media'][0]['state'] = 'Playing'
        payload['winamp'] = 1
        payload['audio'][1]['state'] = 1
        payload['audio'][1]['peak'] = .1
        self.assertEqual(('VLC', 'Winamp', 'chrome'), p.resolve_external_media_snapshot(payload, 0)['active'])
        # Core-Audio-only fallback requires an audible stream, not a stale session.
        payload['media'] = []
        payload['audio'][0]['peak'] = .1
        payload['winamp'] = 0
        self.assertEqual(('VLC', 'chrome'), p.resolve_external_media_snapshot(payload, 0)['active'])

    def test_multiple_players_hold_until_all_stop_and_quiet_period_elapses(self):
        controller, monitor = self.make()
        monitor.value['active'] = ('VLC', 'chrome')
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, controller.filter_action(None, False, 1))
        monitor.value['active'] = ('chrome',)
        self.assertIsNone(controller.filter_action(None, True, 2))
        monitor.value['active'] = ()
        self.assertIsNone(controller.filter_action(None, True, 3))
        self.assertIsNone(controller.filter_action(None, True, 4))
        self.assertEqual(p.EXTERNAL_MEDIA_RESUME, controller.filter_action(None, True, 5))
        self.assertEqual((15, 0), controller.fade_arguments())

    def test_manual_pause_is_never_automatically_resumed(self):
        controller, monitor = self.make()
        controller.filter_action(p.WEB_PAUSE, False, 1)
        monitor.value['active'] = ('Winamp',)
        self.assertIsNone(controller.filter_action(None, True, 2))
        monitor.value['active'] = ()
        controller.filter_action(None, True, 3)
        self.assertIsNone(controller.filter_action(None, True, 10))
        self.assertIsNone(controller.fade_arguments())

    def test_pause_during_automatic_hold_cancels_automatic_resume(self):
        controller, monitor = self.make()
        monitor.value['active'] = ('VLC',)
        controller.filter_action(None, False, 1)
        self.assertEqual(p.WEB_PAUSE, controller.filter_action(p.WEB_PAUSE, True, 2))
        monitor.value['active'] = ()
        controller.filter_action(None, True, 3)
        self.assertIsNone(controller.filter_action(None, True, 10))

    def test_explicit_play_overrides_current_media(self):
        controller, monitor = self.make()
        monitor.value['active'] = ('VLC',)
        controller.filter_action(None, False, 1)
        self.assertEqual(p.WEB_PLAY, controller.filter_action(p.WEB_PLAY, True, 2))
        self.assertIsNone(controller.filter_action(None, False, 3))
        monitor.value['active'] = ()
        controller.filter_action(None, False, 4)
        controller.filter_action(None, False, 6)
        monitor.value['active'] = ('Winamp',)
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, controller.filter_action(None, False, 7))

    def test_unknown_monitor_state_does_not_release_automatic_hold(self):
        controller, monitor = self.make()
        monitor.value['active'] = ('VLC',)
        controller.filter_action(None, False, 1)
        monitor.value = {'known': False, 'active': ()}
        for now in (2, 10, 100):
            self.assertIsNone(controller.filter_action(None, True, now))
        self.assertEqual(p.EXTERNAL_MEDIA_RESUME, controller.filter_action(None, True, 101, enabled=False, fade_seconds=25))
        self.assertEqual((25, 0), controller.fade_arguments())

    def test_short_gap_repeated_interruption_and_fade_restart(self):
        controller, monitor = self.make()
        monitor.value['active'] = ('chrome',)
        controller.filter_action(None, False, 1)
        monitor.value['active'] = ()
        controller.filter_action(None, True, 2)
        monitor.value['active'] = ('chrome',)
        self.assertIsNone(controller.filter_action(None, True, 3))
        monitor.value['active'] = ()
        controller.filter_action(None, True, 4)
        controller.filter_action(None, True, 6)
        controller.advance_fade(0, 4)
        self.assertEqual((15, 4), controller.fade_arguments())
        controller.advance_fade(4, 3)
        self.assertEqual((15, 7), controller.fade_arguments())
        controller.advance_fade(7, 20)
        self.assertIsNone(controller.fade_arguments())

    def test_playback_web_settings_and_ranges(self):
        schema = p.paf_web_control_schema()
        slider = next(x for x in schema['sliders'] if x['key'] == 'external_media_resume_fade_seconds')
        toggle = next(x for x in schema['toggles'] if x['key'] == 'external_media_auto_pause')
        self.assertEqual('playback', slider['theme'])
        self.assertEqual('playback', toggle['theme'])
        self.assertEqual(15, p.PLAYER_SETTING_DEFAULTS['ExternalMediaResumeFadeSeconds'])
        for value in (0, 15, 120):
            self.assertTrue(p.paf_web_action_is_allowed(f'web-set:external_media_resume_fade_seconds:{value}'))
        for value in (-1, 121):
            self.assertFalse(p.paf_web_action_is_allowed(f'web-set:external_media_resume_fade_seconds:{value}'))

    def test_real_ffmpeg_fade_has_fifteen_seconds_and_preserves_selected_gain(self):
        ffmpeg = p.direct_ffmpeg_executable()
        self.assertIsNotNone(ffmpeg)
        base = [str(ffmpeg), '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=1000:sample_rate=48000:duration=16',
                '-af', 'volume=0.5', '-f', 's16le', '-ac', '1', '-']
        faded = p.apply_external_resume_fade(base, (15, 0))
        result = subprocess.run(faded, capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr.decode(errors='replace'))
        samples = array.array('h', result.stdout)
        def rms(at):
            values = samples[int(at * 48000):int((at + .1) * 48000)]
            return math.sqrt(sum(x*x for x in values) / len(values))
        final = rms(15.5)
        self.assertLess(rms(0), final * .01)
        self.assertAlmostEqual(.5, rms(7.5) / final, delta=.015)
        self.assertAlmostEqual(1, rms(14.95) / final, delta=.015)
        self.assertTrue(1400 < final < 1500, final)  # Half of the source's 0.125 full-scale sine.
        self.assertIn('(t+4.000000)/15.000000', p.apply_external_resume_fade(base, (15, 4))[base.index('-af') + 1])
        self.assertIs(base, p.apply_external_resume_fade(base, (0, 0)))


if __name__ == '__main__':
    unittest.main()

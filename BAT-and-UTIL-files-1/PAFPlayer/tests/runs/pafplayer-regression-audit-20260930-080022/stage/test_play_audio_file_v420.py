import contextlib
import io
from pathlib import Path
import unittest
from unittest import mock

import play_audio_file as p


class Monitor:
    def __init__(self): self.value = {'known': True, 'active': ()}
    def snapshot(self, now): return dict(self.value, at=now)


class PriorityTests(unittest.TestCase):
    def setUp(self):
        self.monitor = Monitor()
        self.player = p.PAFExternalPlaybackCoordinator(self.monitor)
        self.player.filter_action(None, False, 0)

    def test_play_during_monitor_startup_does_not_disable_first_detection(self):
        self.monitor.value = {'known': False, 'active': ()}
        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, True, 1))
        self.monitor.value = {'known': True, 'active': ('chrome',)}
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.player.filter_action(None, False, 2))

    def test_redundant_play_acknowledges_current_media(self):
        self.monitor.value['active'] = ('chrome',)
        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, False, 1))

    def test_resume_overrides_chrome_but_new_vlc_cannot_be_ignored(self):
        self.monitor.value['active'] = ('chrome',)
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.player.filter_action(None, False, 1))
        for action in (p.WEB_PLAY, p.PAUSE_TOGGLE):
            self.assertEqual(action, self.player.filter_action(action, True, 2))
            self.assertFalse(self.player.auto_paused)
        self.monitor.value['active'] = ('chrome', 'VLC')
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.player.filter_action(None, False, 3))

    def test_disabling_setting_allows_new_media_until_reenabled(self):
        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, True, 1, enabled=False))
        self.monitor.value['active'] = ('VLC',)
        self.assertIsNone(self.player.filter_action(None, False, 2, enabled=False))
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.player.filter_action(None, False, 3, enabled=True))

    def test_play_after_manual_pause_immediately_resumes(self):
        self.monitor.value['active'] = ('msedge',)
        self.player.filter_action(p.WEB_PAUSE, True, 1)
        self.assertFalse(self.player.auto_paused)
        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, True, 2))
        self.monitor.value['active'] = ()
        self.assertIsNone(self.player.filter_action(None, True, 3))
        self.assertIsNone(self.player.filter_action(None, False, 5))
        self.assertIsNone(self.player.fade_arguments())

    def test_manual_stop_stays_stopped_when_media_finishes(self):
        self.monitor.value['active'] = ('opera',)
        self.player.filter_action(None, False, 1)
        self.player.filter_action(p.WEB_STOP, True, 2)
        self.monitor.value['active'] = ()
        self.player.filter_action(None, True, 3)
        self.assertIsNone(self.player.filter_action(None, True, 6))
        self.assertEqual('manual-hold', self.player.status()['external_media_decision'])


class FullPlayerLoopTests(unittest.TestCase):
    def test_chrome_play_attempt_vlc_quiet_fade_and_manual_hold(self):
        class Process:
            def __init__(self): self.running = True
            def poll(self): return None if self.running else 0
            def terminate(self): self.running = False
            kill = terminate
            def wait(self, timeout=None): self.running = False; return 0
        monitor = Monitor()
        coordinator = p.PAFExternalPlaybackCoordinator(monitor)
        coordinator.filter_action(None, False, 0)
        monitor.value['active'] = ('chrome',)
        commands, processes = [], []
        paused, clock, phase = [False], [100.], [0]
        def factory(command, **kwargs):
            commands.append(command)
            process = Process(); processes.append(process)
            return process
        def action():
            clock[0] += 1
            if clock[0] > 120: raise AssertionError('Player-loop scenario did not complete')
            if phase[0] == 0 and paused[0]:
                self.assertIsNotNone(processes[0].poll())
                phase[0] = 1
                return p.WEB_PLAY
            if phase[0] == 1:
                self.assertFalse(paused[0], 'Play must release the automatic hold')
                self.assertEqual(2, len(commands))
                monitor.value['active'] = ('chrome', 'VLC')
                phase[0] = 2
                return None
            if phase[0] == 2:
                self.assertTrue(paused[0], 'New VLC playback must interrupt after Chrome override')
                monitor.value['active'] = ('chrome',)
                phase[0] = 3
            elif phase[0] == 3 and len(commands) == 3:
                self.assertFalse(paused[0])
                self.assertIn('/15.000000', ' '.join(commands[2]))
                monitor.value['active'] = ('VLC',)
                phase[0] = 4
            elif phase[0] == 4 and paused[0]:
                self.assertIsNotNone(processes[2].poll())
                monitor.value['active'] = ()
                phase[0] = 5
                return p.WEB_PAUSE
            elif phase[0] == 5 and clock[0] >= 112:
                self.assertTrue(paused[0])
                return p.STOP
            return None
        fixture = Path(__file__).with_name('pafplayer_v416_timing_fixture.wav')
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            for name in ('update_lastfm_now_playing_async', 'append_pafplayer_trace',
                         'write_now_playing_files', 'start_background_audio_health_check'):
                if hasattr(p, name): stack.enter_context(mock.patch.object(p, name))
            result = p.play_audio_file(fixture, ffplay=Path('ffplay.exe'), duration_probe=lambda _: 60,
                key_action_reader=action, process_factory=factory, monotonic=lambda: clock[0], sleeper=lambda _: None,
                install_signal_handlers=False, drcs_visualizer=False, sixel_visualizer=False, lyrics_display=False,
                looping=False, now_playing_targets=[], paused_state=paused, manage_winamp=False,
                visualizer_input_source_state=[0], external_media_controller=coordinator,
                attribute_management_enabled=False, theory_modes={13})
        self.assertEqual('stopped', result)
        self.assertEqual(3, len(commands))
        self.assertEqual(5, phase[0])


if __name__ == '__main__': unittest.main()

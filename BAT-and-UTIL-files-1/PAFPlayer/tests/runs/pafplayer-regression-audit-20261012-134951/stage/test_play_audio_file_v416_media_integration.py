import contextlib
import io
from pathlib import Path
import unittest
from unittest import mock

import play_audio_file as p


class PlayerIntegrationTests(unittest.TestCase):
    def test_automatic_pause_resumes_same_position_with_fade_on_both_backends(self):
        class Monitor:
            active = False
            def snapshot(self, now): return {'known': True, 'active': ('VLC',) if self.active else (), 'at': now}
        class Process:
            def __init__(self): self.running = True
            def poll(self): return None if self.running else 0
            def terminate(self): self.running = False
            kill = terminate
            def wait(self, timeout=None): self.running = False; return 0
        monitor = Monitor()
        controller = p.PAFExternalPlaybackCoordinator(monitor)
        controller.filter_action(None, False, 0)
        monitor.active = True
        commands = []
        clock = [100.]
        paused = [False]
        def factory(command, **kwargs):
            commands.append(command)
            return Process()
        def action():
            if paused[0]:
                monitor.active = False
            if len(commands) == 2:
                return p.STOP
            clock[0] += 1
            if clock[0] > 120: raise AssertionError('Automatic resume did not arrive')
            return None
        fixture = Path(__file__).with_name('pafplayer_v416_timing_fixture.wav')
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            for name in ('update_lastfm_now_playing_async', 'append_pafplayer_trace', 'record_local_play_history',
                         'write_now_playing_files', 'start_background_audio_health_check'):
                if hasattr(p, name): stack.enter_context(mock.patch.object(p, name))
            stack.enter_context(mock.patch.object(p, 'LASTFM_SCROBBLING', False, create=True))
            result = p.play_audio_file(fixture, ffplay=Path('ffplay.exe'), duration_probe=lambda _: 60,
                key_action_reader=action, process_factory=factory, monotonic=lambda: clock[0], sleeper=lambda _: None,
                install_signal_handlers=False, drcs_visualizer=False, sixel_visualizer=False, lyrics_display=False,
                looping=False, now_playing_targets=[], paused_state=paused, manage_winamp=False,
                external_media_controller=controller, attribute_management_enabled=False, theory_modes={13})
        self.assertEqual('stopped', result)
        self.assertEqual(2, len(commands))
        self.assertEqual(commands[0][commands[0].index('-ss') + 1], commands[1][commands[1].index('-ss') + 1])
        self.assertNotIn('eval=frame', commands[0][commands[0].index('-af') + 1])
        self.assertIn('/15.000000', commands[1][commands[1].index('-af') + 1])
        self.assertFalse(paused[0])
        # Native worker uses the same sample-time envelope before output fan-out.
        with mock.patch.object(p, 'direct_ffmpeg_executable', return_value=Path('ffmpeg.exe')), \
             mock.patch.object(p, 'waveout_output_devices', return_value=[{'value': -1}]), \
             mock.patch.object(p, 'load_multi_output_latencies_ms', return_value={}), \
             mock.patch.object(p, 'IsolatedWaveOutProcess') as worker:
            p.launch_matrixmixer_inspired_renderer(fixture, 5, 100, 1, 2, 0, 48000,
                end_seconds=60, replaygain_info=None, resume_fade=(15, 4))
            self.assertIn('(t+4.000000)/15.000000', ' '.join(worker.call_args.args[0]['command']))


if __name__ == '__main__': unittest.main()

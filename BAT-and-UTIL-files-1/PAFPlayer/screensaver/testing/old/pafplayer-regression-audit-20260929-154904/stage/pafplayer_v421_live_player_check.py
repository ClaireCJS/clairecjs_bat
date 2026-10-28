"""Use live Windows detection and real muted audio; never control other apps."""
import contextlib
import io
import json
from pathlib import Path
import time
import sys
from unittest import mock
import play_audio_file as p
from pafplayer_v416_edit import unique

monitor = p.PAFExternalMediaMonitor().start()
class SelectedMedia:
    def snapshot(self, now):
        sample = monitor.snapshot(now)
        if '--vlc-only' in sys.argv:
            sample = dict(sample, active=tuple(x for x in sample['active'] if x == 'VLC'))
        return sample
controller = p.PAFExternalPlaybackCoordinator(SelectedMedia())
# Establish a known idle baseline before attaching the live native sample, to
# exercise an interruption and real worker restart without controlling apps.
controller.baseline_observed = True
paused, phase, stopped = [False], [0], []
resumed_at = [None]
deadline = time.monotonic() + 25
original_stop = p.stop_process
original_launch = p.launch_matrixmixer_inspired_renderer
workers = []
def launch(*args, **kwargs):
    process, command = original_launch(*args, **kwargs)
    workers.append(process)
    return process, command

def stop_audio(process, *args, **kwargs):
    before = process.poll()
    result = original_stop(process, *args, **kwargs)
    stopped.append({'pid': getattr(process, 'pid', None), 'before': before,
                    'after': process.poll(), 'type': type(process).__name__})
    return result

def action():
    if time.monotonic() > deadline:
        raise AssertionError('Live player did not automatically pause within 25 seconds')
    if phase[0] == 0 and paused[0] and controller.auto_paused:
        assert controller.last_snapshot['active'], controller.last_snapshot
        assert stopped and stopped[-1]['before'] is None and stopped[-1]['after'] is not None, stopped
        phase[0] = 1
        return p.WEB_PLAY
    if phase[0] == 1:
        assert not paused[0] and not controller.auto_paused, 'Manual Play did not resume playback'
        phase[0] = 2
        resumed_at[0] = time.monotonic()
        return None
    if phase[0] == 2 and time.monotonic() - resumed_at[0] >= 0.75:
        assert not paused[0] and not controller.auto_paused, 'Playback was immediately paused again'
        assert len(workers) >= 2 and workers[-1].poll() is None, 'Resumed audio worker is not running'
        phase[0] = 3
        return p.STOP
    return None

try:
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        stack.enter_context(mock.patch.object(p, 'stop_process', side_effect=stop_audio))
        stack.enter_context(mock.patch.object(p, 'launch_matrixmixer_inspired_renderer', side_effect=launch))
        for name in ('update_lastfm_now_playing_async', 'append_pafplayer_trace',
                     'start_background_audio_health_check', 'set_console_title'):
            if hasattr(p, name): stack.enter_context(mock.patch.object(p, name))
        result = p.play_audio_file(Path(__file__).with_name('pafplayer_v420_silent_vlc_fixture.wav'),
            key_action_reader=action, install_signal_handlers=False,
            drcs_visualizer=False, sixel_visualizer=False, lyrics_display=False,
            looping=False, now_playing_targets=[], volume_state=[0], paused_state=paused,
            visualizer_input_source_state=[0], external_media_controller=controller,
            manage_winamp=False, attribute_management_enabled=False, theory_modes={13})
    assert result == 'stopped' and phase[0] == 3, (result, phase)
    report = {'result': result, 'phase': phase[0], 'external': controller.last_snapshot,
              'real_audio_processes_stopped': stopped, 'vlc_isolated_from_other_apps': '--vlc-only' in sys.argv, 'baseline': 'idle baseline injected before live monitor', 'manual_play_resumed': True}
    output = unique(Path(__file__).with_name('pafplayer_v421_live_player_check.json'))
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
finally:
    monitor.close()

"""Pause-reason behavior and artwork-detail applicability, with playback mocked."""
import ast
import contextlib
import io
import json
import re
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest import mock

import play_audio_file as p


class Monitor:
    def __init__(self):
        self.value = {'known': True, 'active': ()}

    def snapshot(self, now):
        return dict(self.value, at=now)


class PauseReasons(unittest.TestCase):
    def setUp(self):
        self.monitor = Monitor()
        self.player = p.PAFExternalPlaybackCoordinator(self.monitor)
        self.player.filter_action(None, False, 0)

    def test_keyboard_and_web_reasons_survive_idle_and_clear_on_play(self):
        for action, reason in ((p.PAUSE_TOGGLE, 'hit pause key'), (p.WEB_PAUSE, 'web pause'), (p.WEB_STOP, 'web stop')):
            self.player.filter_action(action, False, 1)
            self.player.filter_action(None, True, 2)
            self.assertEqual(reason, self.player.status()['pause_reason'])
            self.assertEqual('Paused (' + reason + ')', p.paused_status_text(self.player.pause_reason))
            self.player.filter_action(p.WEB_PLAY, True, 3)
            self.assertEqual('', self.player.pause_reason)

    def test_detected_source_reason_survives_monitor_loss_and_quiet_period(self):
        self.monitor.value['active'] = ('VLC',)
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.player.filter_action(None, False, 1))
        self.assertEqual('VLC playback detected', self.player.pause_reason)
        self.monitor.value = {'known': False, 'active': ()}
        self.player.filter_action(None, True, 2)
        self.assertEqual('VLC playback detected', self.player.pause_reason)
        self.monitor.value['known'] = True
        self.player.filter_action(None, True, 3)
        self.assertEqual('VLC playback detected', self.player.pause_reason)
        self.assertEqual(p.EXTERNAL_MEDIA_RESUME, self.player.filter_action(None, True, 5))
        self.assertEqual('', self.player.pause_reason)

    def test_manual_pause_replaces_auto_reason_and_keeps_hold(self):
        self.monitor.value['active'] = ('youtube',)
        self.player.filter_action(None, False, 1)
        self.assertEqual('YouTube playback detected', self.player.pause_reason)
        self.player.filter_action(p.WEB_PAUSE, True, 2)
        self.monitor.value['active'] = ()
        self.player.filter_action(None, True, 3)
        self.assertIsNone(self.player.filter_action(None, True, 9))
        self.assertEqual('web pause', self.player.pause_reason)

    def test_reason_names_only_new_sources_and_does_not_guess_browser_site(self):
        self.player.filter_action(p.WEB_PLAY, False, 1)
        self.monitor.value['active'] = ('chrome',)
        self.player.filter_action(p.WEB_PLAY, False, 2)
        self.monitor.value['active'] = ('chrome', 'VLC')
        self.player.filter_action(None, False, 3)
        self.assertEqual('VLC playback detected', self.player.pause_reason)
        self.assertEqual('Chrome playback detected', p.external_media_pause_reason({'active': ('chrome',)}))
        snapshot = p.resolve_external_media_snapshot({'known': True, 'media': [{'app': 'youtube', 'state': 'Playing'}]}, 0)
        self.assertEqual('YouTube playback detected', p.external_media_pause_reason(snapshot))

    def test_real_player_help_shows_restored_keyboard_and_web_pause_reasons(self):
        class Process:
            def __init__(self): self.running = True
            def poll(self): return None if self.running else 0
            def terminate(self): self.running = False
            kill = terminate
            def wait(self, timeout=None): self.running = False; return 0
        fixture = Path(__file__).with_name('pafplayer_v416_timing_fixture.wav')
        for initial, request, expected, source in (
            (True, None, 'restored previous pause state', None),
            (False, p.PAUSE_TOGGLE, 'hit pause key', None),
            (False, p.WEB_PAUSE, 'web pause', None),
            (False, None, 'VLC playback detected', 'VLC'),
            (False, None, 'YouTube playback detected', 'youtube'),
        ):
            clock, paused = [100.], [initial]
            actions = iter(([request] if request or source else []) + [p.HELP_OVERLAY, p.STOP])
            monitor = Monitor()
            coordinator = p.PAFExternalPlaybackCoordinator(monitor)
            coordinator.filter_action(None, False, 0)
            if source:
                monitor.value['active'] = (source,)
            def action():
                clock[0] += 1
                if clock[0] > 115:
                    raise AssertionError('Mock playback scenario did not terminate')
                return next(actions, p.STOP)
            output = io.StringIO()
            with self.subTest(reason=expected), contextlib.ExitStack() as stack:
                stack.enter_context(contextlib.redirect_stdout(output))
                for name in ('update_lastfm_now_playing_async', 'append_pafplayer_trace', 'record_local_play_history',
                             'write_now_playing_files', 'start_background_audio_health_check', 'save_player_setting_value',
                             'set_console_title', 'scrobble_track_async', 'playlist_history_mark_played',
                             'save_spectrum_timeline_cache'):
                    if hasattr(p, name): stack.enter_context(mock.patch.object(p, name))
                stack.enter_context(mock.patch.object(p, 'LASTFM_SCROBBLING', False, create=True))
                result = p.play_audio_file(
                    fixture, ffplay=Path('ffplay.exe'), duration_probe=lambda _: 60,
                    key_action_reader=action, process_factory=lambda *a, **k: Process(),
                    monotonic=lambda: clock[0], sleeper=lambda _: None,
                    install_signal_handlers=False, drcs_visualizer=False, sixel_visualizer=False,
                    lyrics_display=False, looping=False, now_playing_targets=[],
                    initially_paused=initial, paused_state=paused, manage_winamp=False,
                    external_media_controller=coordinator, visualizer_input_source_state=[0],
                    attribute_management_enabled=False, theory_modes={13, 36},
                )
                self.assertEqual('stopped', result)
                self.assertIn('Paused (' + expected + ')', output.getvalue())


class ArtworkApplicability(unittest.TestCase):
    def test_disabled_controls_explanation_and_reenable_in_actual_javascript(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node required for actual web-control behavior')
        html = p._paf_web_html()
        scripts = re.findall(r'<script\b[^>]*>(.*?)</script>', html, re.S)
        syntax = subprocess.run([node, '--check'], input='\n'.join(scripts), capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(0, syntax.returncode, syntax.stderr)
        start = html.index('function setControlApplicability(')
        end = html.index('function applyConsoleAlertsEnablement()', start)
        script = r'''
const assert=require('assert');
const elements={},wraps={};
function element(){return {checked:true,value:'3',hidden:false,textContent:'',disabled:false,dataset:{},classList:{toggle(){}}};}
for(const id of ['visualizerSection','visualizerMasterToggle','ctl-visualizer_bars_enabled','ctl-art_color_bars','ctl-visualizer_background_artwork_enabled','ctl-visualizer_granularity','microtileBarsReason','microtileBlacknessReason'])elements[id]=element();
for(const key of ['art_color_bars','drcs_art_bar_microtile_mode','drcs_art_microtile_mode']){
 const controls=[element(),element(),element(),element()];
 wraps[key]={classList:{toggle(){}},querySelectorAll(){return controls},controls};
}
global.document={getElementById(id){return elements[id]||null},querySelector(selector){const match=selector.match(/data-control-key="([^"]+)"/);return match?wraps[match[1]]||null:null}};
''' + html[start:end] + r'''
const check=(key,disabled)=>assert(wraps[key].controls.every(control=>control.disabled===disabled));
for(const value of ['1','2']){
 elements['ctl-visualizer_granularity'].value=value;applyVisualizerLayerEnablement();
 check('drcs_art_microtile_mode',true);check('drcs_art_bar_microtile_mode',true);
 assert.equal(elements.microtileBlacknessReason.hidden,false);
 assert.equal(elements.microtileBlacknessReason.textContent,'Requires Granularity: 2× Twin DRCS.');
 assert.equal(elements['ctl-visualizer_granularity'].value,value);
}
elements['ctl-visualizer_granularity'].value='3';applyVisualizerLayerEnablement();
check('drcs_art_microtile_mode',false);check('drcs_art_bar_microtile_mode',false);
assert.equal(elements.microtileBlacknessReason.hidden,true);
elements['ctl-visualizer_background_artwork_enabled'].checked=false;applyVisualizerLayerEnablement();
check('drcs_art_microtile_mode',true);check('drcs_art_bar_microtile_mode',false);
elements.visualizerSection.dataset.unicodeHalfcellForced='true';applyVisualizerLayerEnablement();
check('drcs_art_bar_microtile_mode',true);
assert(elements.microtileBarsReason.textContent.includes('forced Unicode'));
console.log('Artwork controls: passed');
'''
        result = subprocess.run([node, '-e', script], capture_output=True, text=True, encoding='utf-8', timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_rendering_and_row_fix_are_identical_to_v444(self):
        baseline = Path(__file__).with_name('play_audio_file_v444_v427_console_row_fix_only.py')
        old = ast.parse(baseline.read_text(encoding='utf-8'))
        new = ast.parse(Path(p.__file__).read_text(encoding='utf-8'))
        names = {'render_drcs_visualizer', '_windows_console_text_api', '_write_large_windows_console_text', 'write_console', 'write_console_bytes', 'main'}
        def selected(tree):
            return {node.name: ast.dump(node) for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names}
        self.assertEqual(selected(old), selected(new))


if __name__ == '__main__':
    unittest.main()

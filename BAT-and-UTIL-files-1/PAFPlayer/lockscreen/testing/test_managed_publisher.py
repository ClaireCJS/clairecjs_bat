"""Lifecycle and authorization regressions; no real package launches."""
import ast
import contextlib
import hashlib
import importlib.util
import io
import http.client
import json
import os
from pathlib import Path
import sys
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('managed_bridge', ROOT / 'lockscreen/src/PAFPlayer_lockscreen.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class ManagedPublisherTests(unittest.TestCase):
    def test_large_shell_environment_is_not_inherited_or_modified(self):
        original = {'windir': 'C:/Windows', 'USERPROFILE': 'C:/Users/Test',
                    'TEMP': 'C:/Users/Test/Temp', 'LOCALAPPDATA': 'C:/Users/Test/AppData/Local',
                    'PATH': 'X' * 50000, 'MUSIC_SHELL_STATE': 'Y' * 95000,
                    'COMSPEC': 'C:/tcmd/TCC.EXE', 'PAF_PRIVATE_VALUE': 'do not inherit'}
        saved = dict(original)
        child = bridge.activation_environment(original)
        self.assertEqual(original, saved)
        self.assertLess(sum(len(k) + len(v) + 2 for k, v in child.items()), 8192)
        self.assertEqual(child['USERPROFILE'], original['USERPROFILE'])
        self.assertEqual(child['TEMP'], original['TEMP'])
        self.assertEqual(child['LOCALAPPDATA'], original['LOCALAPPDATA'])
        self.assertNotIn('MUSIC_SHELL_STATE', child)
        self.assertNotIn('PAF_PRIVATE_VALUE', child)
        self.assertEqual(Path(child['COMSPEC']).name, 'cmd.exe')

    def test_real_launcher_receives_bounded_environment(self):
        process = Mock()
        process.lease = '0' * 32
        process.attach.return_value = process
        completed = SimpleNamespace(returncode=0, stdout='1234\n', stderr='')
        huge = dict(os.environ, **{'MUSIC_SHELL_STATE_%s' % n: 'X' * 20000 for n in range(8)})
        with patch.object(bridge.os, 'environ', huge), \
             patch.object(bridge, 'ManagedProcess', return_value=process), \
             patch.object(bridge.subprocess, 'run', return_value=completed) as run:
            self.assertIs(bridge.launch('http://127.0.0.1:666', 'session'), process)
        self.assertFalse(any(key.startswith('MUSIC_SHELL_STATE') for key in run.call_args.kwargs['env']))
        self.assertEqual(run.call_args.kwargs['encoding'], 'utf-8-sig')
        process.attach.assert_called_once_with(1234)

    def test_actual_activation_error_is_preserved_and_handles_closed(self):
        process = Mock()
        process.lease = '0' * 32
        completed = SimpleNamespace(returncode=1, stdout='', stderr='COM activation failed: 0x80070005\n')
        with patch.object(bridge, 'ManagedProcess', return_value=process), \
             patch.object(bridge.subprocess, 'run', return_value=completed):
            with self.assertRaisesRegex(OSError, 'COM activation failed: 0x80070005'):
                bridge.launch('http://127.0.0.1:666', 'session')
        process.close.assert_called_once()

    def make(self, enabled=True, official=True):
        runtime = SimpleNamespace(settings={bridge.KEY: enabled}, lock=threading.RLock(),
                                  save_settings=Mock(), instance=SimpleNamespace(owns=lambda: official, identity='session-1'))
        owner = SimpleNamespace(workflows=runtime, port=1777)
        child = SimpleNamespace(close=Mock(), poll=Mock(return_value=None))
        launcher = Mock(return_value=child)
        return bridge.Controller(owner, launcher), launcher, child

    def test_off_by_default(self):
        with patch.dict(os.environ, {'LOCALAPPDATA': ''}):
            self.assertFalse(bridge.previous_setting())

    def test_migration_only_boolean_true(self):
        for raw, expected in ((True, True), (False, False), ('true', False)):
            with patch.object(Path, 'stat', return_value=SimpleNamespace(st_size=40)), patch.object(Path, 'read_text', return_value=json.dumps({bridge.KEY: raw})), patch.dict(os.environ, {'LOCALAPPDATA': 'C:/example'}):
                self.assertEqual(expected, bridge.previous_setting())

    def test_official_launch_pins_identity_and_actual_port(self):
        control, launch, child = self.make()
        control._step()
        launch.assert_called_once_with('http://127.0.0.1:1777', 'session-1')

    def test_secondary_instance_never_launches(self):
        control, launch, child = self.make(official=False)
        control._step()
        launch.assert_not_called()

    def test_disabled_never_launches(self):
        control, launch, child = self.make(enabled=False)
        control._step()
        launch.assert_not_called()

    def test_no_duplicate_launch_when_running(self):
        control, launch, child = self.make()
        for unused in range(10): control._step()
        launch.assert_called_once()

    def test_disable_closes_pipe_without_killing_player(self):
        control, launch, child = self.make()
        control._step()
        control.configure({'enabled': False})
        control._step()
        child.close.assert_called_once()
        self.assertIsNone(control.process)

    def test_ownership_loss_closes_pipe(self):
        control, launch, child = self.make()
        control._step()
        control.runtime.instance.owns = lambda: False
        control._step()
        child.close.assert_called_once()

    def test_failed_settings_write_preserves_previous_choice(self):
        control, launch, child = self.make()
        control.runtime.save_settings.side_effect = OSError('disk full')
        with self.assertRaises(OSError): control.configure({'enabled': False})
        self.assertTrue(control.enabled())

    def test_bad_types_rejected(self):
        control, launch, child = self.make()
        for value in ({'enabled': 1}, {'enabled': 'false'}, {}, {'enabled': False, 'port': 80}):
            with self.assertRaises(ValueError): control.configure(value)

    def test_retry_backoff_after_crash(self):
        control, launch, child = self.make()
        with patch.object(bridge.time, 'monotonic', return_value=100):
            control._step()
            child.poll.return_value = 4
            control._step()
            control._step()
        self.assertEqual(launch.call_count, 1)
        self.assertIn('code 4', control.message)

    def test_retry_backoff_after_activation_failure(self):
        control, launch, child = self.make()
        launch.side_effect = OSError('missing package')
        with patch.object(bridge.time, 'monotonic', return_value=100):
            with self.assertRaises(OSError): control._step()
            control._step()
        launch.assert_called_once()

    def test_shutdown_is_nonblocking_and_wakes_worker(self):
        control, launch, child = self.make()
        control._step()
        control.close()
        self.assertTrue(control.stop.is_set() and control.wake.is_set())
        control._step()
        child.close.assert_called_once()

    def test_remote_http_cannot_read_or_change_settings(self):
        control, launch, child = self.make()
        handler = SimpleNamespace(client_address=('10.0.0.2', 1), command='POST', _json=Mock())
        self.assertTrue(bridge.handle(handler, control.owner, '/api/lockscreen/settings'))
        self.assertEqual(handler._json.call_args.args[0], 403)

    def lyric_owner(self, official=True):
        control, unused, child = self.make(official=official)
        owner = control.owner
        owner.workflows.app = SimpleNamespace(PROGRAM_TITLE='PAFplayer', PROGRAM_VERSION='V517')
        owner._lock = threading.RLock()
        owner.note_screensaver_activity = Mock()
        owner.note_client_activity = Mock()
        owner._state = {'program': 'PAFplayer', 'version': 'V517', 'playing': True,
                        'paused': False, 'lyric': 'Current line',
                        'metadata': {'Artist': 'Singer', 'Song': 'Song', 'large_unused': object()},
                        'track': {'filename': 'song.flac', 'path': 'private-path'},
                        'lyric_timeline': object(), 'spectrum': object()}
        return owner

    def lyric_handler(self, method='GET', address='127.0.0.1'):
        return SimpleNamespace(client_address=(address, 1), command=method,
                               path='/api/remote-tray/hello?lockscreen=1', _json=Mock())

    def test_lyric_poll_is_compact_official_and_does_not_activate_spectrum(self):
        owner = self.lyric_owner()
        handler = self.lyric_handler()
        self.assertTrue(bridge.handle(handler, owner, '/api/remote-tray/hello'))
        code, value = handler._json.call_args.args
        self.assertEqual(code, 200)
        self.assertTrue(value['official'])
        self.assertEqual(value['identity'], 'session-1')
        self.assertEqual(value['state']['lyric'], 'Current line')
        self.assertNotIn('lyric_timeline', value['state'])
        self.assertNotIn('spectrum', value['state'])
        self.assertNotIn('path', value['state']['track'])
        self.assertLess(len(json.dumps(value)), 1024)
        owner.note_screensaver_activity.assert_called_once()
        owner.note_client_activity.assert_not_called()

    def test_lyric_poll_rejects_remote_and_mutating_requests(self):
        for method, address, expected in [('GET', '10.0.0.2', 403), ('POST', '127.0.0.1', 405)]:
            owner, handler = self.lyric_owner(), self.lyric_handler(method, address)
            self.assertTrue(bridge.handle(handler, owner, '/api/remote-tray/hello'))
            self.assertEqual(handler._json.call_args.args[0], expected)
            owner.note_screensaver_activity.assert_not_called()

    def test_unofficial_lyric_poll_has_no_state_or_activity(self):
        owner, handler = self.lyric_owner(False), self.lyric_handler()
        bridge.handle(handler, owner, '/api/remote-tray/hello')
        value = handler._json.call_args.args[1]
        self.assertFalse(value['official'])
        self.assertEqual(value['identity'], '')
        self.assertEqual(value['state'], {})
        owner.note_screensaver_activity.assert_not_called()

    def test_previous_cue_recovers_a_line_shorter_than_poll_interval(self):
        cues = [[0, ''], [1, 'First'], [2, 'Brief'], [2.1, 'Current']]
        self.assertEqual(bridge.previous_lyric(cues, 2.2, 0, 'Current'), 'Brief')

    def test_previous_cue_follows_seek_and_offset(self):
        cues = [[0, ''], [1, 'First'], [2, 'Second'], [3, 'Third']]
        self.assertEqual(bridge.previous_lyric(cues, 2.9, .2, 'Third'), 'Second')
        self.assertEqual(bridge.previous_lyric(cues, 1.5, 0, 'First'), '')
        self.assertEqual(bridge.previous_lyric(cues, 2.5, -.6, 'First'), '')

    def test_previous_cue_does_not_leak_into_gap_or_next_track(self):
        self.assertEqual(bridge.previous_lyric([[0, 'First'], [1, '']], 1.5, 0, ''), '')
        self.assertEqual(bridge.previous_lyric([], 0, 0, ''), '')
        self.assertEqual(bridge.previous_lyric(None, 0, 0, 'Current'), '')

    def test_compact_reply_includes_previous_cue_but_no_timeline(self):
        owner, handler = self.lyric_owner(), self.lyric_handler()
        owner._state.update(lyric_timeline=[[0, ''], [1, 'Brief'], [1.1, 'Current']],
                            lyric_position_seconds=1.2, lyric='Current')
        bridge.handle(handler, owner, '/api/remote-tray/hello')
        state = handler._json.call_args.args[1]['state']
        self.assertEqual(state['lyric_previous'], 'Brief')
        self.assertNotIn('lyric_timeline', state)

    def test_lock_lyric_lead_is_exactly_250ms_before_boundary(self):
        cues = [[0, 'First'], [2, 'Second'], [3, '']]
        def at(position, **changes):
            options = dict(playing=True, paused=False, stopped=False)
            options.update(changes)
            return bridge.lockscreen_lyric_context(cues, position, 0, 'First', **options)
        self.assertEqual(at(1.749), ('First', ''))
        self.assertEqual(at(1.75), ('Second', 'First'))
        self.assertEqual(at(2.75), ('', ''))
        self.assertEqual(at(1.75, paused=True), ('First', ''))
        self.assertEqual(at(1.75, playing=False), ('First', ''))
        self.assertEqual(at(1.75, stopped=True), ('', ''))

    def test_lock_lyric_lead_respects_speed_offset_seek_and_fallback(self):
        cues = [[0, 'First'], [2, 'Second'], [4, 'Third']]
        options = dict(playing=True, paused=False, stopped=False)
        self.assertEqual(bridge.lockscreen_lyric_context(cues, 1.5, 0, 'First', speed=2, **options), ('Second', 'First'))
        self.assertEqual(bridge.lockscreen_lyric_context(cues, 1.5, .25, 'First', **options), ('Second', 'First'))
        self.assertEqual(bridge.lockscreen_lyric_context(cues, .5, 0, 'Third', **options), ('First', ''))
        self.assertEqual(bridge.lockscreen_lyric_context(None, 1.8, 0, 'Fallback', **options), ('Fallback', ''))
        self.assertEqual(bridge.lockscreen_lyric_context(cues, 1.75, 0, 'First', speed=float('nan'), **options), ('Second', 'First'))

    def test_endpoint_leads_lock_lyrics_without_mutating_other_displays(self):
        owner, handler = self.lyric_owner(), self.lyric_handler()
        owner._state.update(lyric_timeline=[[0, 'First'], [2, 'Next']],
                            lyric_position_seconds=1.75, lyric='First')
        bridge.handle(handler, owner, '/api/remote-tray/hello')
        state = handler._json.call_args.args[1]['state']
        self.assertEqual((state['lyric'], state['lyric_previous']), ('Next', 'First'))
        self.assertEqual(owner._state['lyric'], 'First')
        self.assertEqual(owner._state['lyric_position_seconds'], 1.75)

    def test_compact_status_includes_album_year_and_unshifted_playback_counter(self):
        owner, handler = self.lyric_owner(), self.lyric_handler()
        owner._state['metadata'].update(Album='The album', album='fallback', Year='1991', Date='fallback')
        owner._state.update(position_seconds=61.85, duration_seconds=120.0,
                            lyric_position_seconds=61.85, lyric_timeline=[[0, 'First'], [62, 'Next']])
        bridge.handle(handler, owner, '/api/remote-tray/hello')
        state = handler._json.call_args.args[1]['state']
        self.assertEqual(state['metadata']['Album'], 'The album')
        self.assertEqual(state['metadata']['album'], 'fallback')
        self.assertEqual(state['metadata']['Year'], '1991')
        self.assertEqual(state['metadata']['Date'], 'fallback')
        self.assertEqual(state['position_seconds'], 61.85)
        self.assertEqual(state['duration_seconds'], 120.0)
        self.assertEqual(state['lyric'], 'Next')
        self.assertNotIn('lyric_timeline', state)
        self.assertNotIn('spectrum', state)
        self.assertLess(len(json.dumps(state)), 1024)
        owner.note_client_activity.assert_not_called()

    def test_compact_counter_preserves_pause_seek_and_missing_time(self):
        owner, handler = self.lyric_owner(), self.lyric_handler()
        bridge.handle(handler, owner, '/api/remote-tray/hello')
        self.assertNotIn('position_seconds', handler._json.call_args.args[1]['state'])
        for position, paused in ((61.2, False), (61.2, True), (4.0, False)):
            owner._state.update(position_seconds=position, duration_seconds=120, paused=paused)
            bridge.handle(handler, owner, '/api/remote-tray/hello')
            state = handler._json.call_args.args[1]['state']
            self.assertEqual(state['position_seconds'], position)
            self.assertEqual(state['paused'], paused)

    def test_regular_tray_request_keeps_existing_handler(self):
        owner, handler = self.lyric_owner(), self.lyric_handler()
        handler.path = '/api/remote-tray/hello'
        self.assertFalse(bridge.handle(handler, owner, '/api/remote-tray/hello'))
        owner.note_screensaver_activity.assert_not_called()

    def test_real_lyric_http_keeps_status_active_with_browser_closed(self):
        import PAFPlayer as app
        control, unused, child = self.make(enabled=False)
        runtime = control.runtime
        runtime.app = app
        with patch.object(app, 'paf_workflows', return_value=runtime):
            server = app.PAFWebServer(host='127.0.0.1', port=0)
        control.owner = server
        server._lock_screen_controller = control
        self.assertTrue(server.start())
        connection = http.client.HTTPConnection('127.0.0.1', server.port, timeout=3)
        try:
            self.assertFalse(server.status_client_active())
            for lyric, paused in [('First line', False), ('Second line', False), ('Second line', True), ('', False)]:
                server.publish(lyric=lyric, paused=paused)
                connection.request('GET', '/api/remote-tray/hello?lockscreen=1')
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                state = json.loads(response.read())['state']
                self.assertEqual(state['lyric'], lyric)
                self.assertEqual(state['paused'], paused)
                self.assertTrue(server.status_client_active())
                self.assertFalse(server.web_visualizer_active())
            with patch.object(app.time, 'monotonic', return_value=server._last_screensaver_activity + 3.1):
                self.assertFalse(server.status_client_active())
        finally:
            connection.close()
            server.close()
            control.thread.join(timeout=3)

    def test_bundled_source_matches_module(self):
        tree = ast.parse((ROOT / 'PAFPlayer.py').read_text(encoding='utf-8'))
        bundled = {}
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '_PAF_BUNDLED_SOURCES':
                    bundled.update(ast.literal_eval(node.value))
                elif (isinstance(target, ast.Subscript)
                      and isinstance(target.value, ast.Name)
                      and target.value.id == '_PAF_BUNDLED_SOURCES'):
                    bundled[ast.literal_eval(target.slice)] = ast.literal_eval(node.value)
        expected = {
            'PAFPlayer_lockscreen': ROOT / 'lockscreen/src/PAFPlayer_lockscreen.py',
            'PAFPlayer_lockscreen_installer': ROOT / 'lockscreen/lockscreen_installer.py',
            'PAFPlayer_lockscreen_payload': ROOT / 'lockscreen/src/PAFPlayer_lockscreen_payload.py',
        }
        self.assertEqual({name: bundled[name] for name in expected},
                         {name: path.read_text(encoding='utf-8') for name, path in expected.items()})

    def test_embedded_payload_extracts_with_verified_hashes(self):
        payload_spec = importlib.util.spec_from_file_location(
            'PAFPlayer_lockscreen_payload', ROOT / 'lockscreen/src/PAFPlayer_lockscreen_payload.py')
        payload = importlib.util.module_from_spec(payload_spec)
        payload_spec.loader.exec_module(payload)
        local = Path(os.environ['LOCALAPPDATA']) / ('embedded-payload-' + str(time.time_ns()))
        with patch.dict(sys.modules, {'PAFPlayer_lockscreen_payload': payload}), \
             patch.dict(os.environ, {'LOCALAPPDATA': str(local)}):
            extracted = bridge.embedded_installer_root()
        for name, expected_hash in payload.PAYLOAD_SHA256.items():
            matches = list(extracted.rglob(name))
            self.assertEqual(len(matches), 1)
            self.assertEqual(hashlib.sha256(matches[0].read_bytes()).hexdigest(), expected_hash)

    def test_first_run_install_attempt_is_recorded_once(self):
        class Backend:
            def installed_version(self):
                return '528.0.0.0'
        fake_installer = SimpleNamespace(WindowsBackend=Backend)
        local = Path(os.environ['LOCALAPPDATA']) / ('auto-install-' + str(time.time_ns()))
        with patch.dict(sys.modules, {'PAFPlayer_lockscreen_installer': fake_installer}), \
             patch.dict(os.environ, {'LOCALAPPDATA': str(local)}), \
             patch.object(bridge, 'install_embedded_lockscreen', return_value=7) as install, \
             contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(bridge.maybe_auto_install_lockscreen(), 7)
                self.assertEqual(bridge.maybe_auto_install_lockscreen(), 0)
        install.assert_called_once()
        self.assertEqual(install.call_args.kwargs['ask']('ignored'), 'yes')
        self.assertTrue((local / 'PAFPlayer' / bridge.AUTO_INSTALL_MARKER).is_file())

    def test_new_web_section_keeps_existing_ids(self):
        page = '<div class="group" id="visualScreensaverSection"></div></body>'
        value = bridge.augment(page)
        self.assertIn('id="lockScreenEnabled"', value)
        self.assertEqual(value.count('id="visualScreensaverSection"'), 1)

    def test_real_http_settings_require_token_and_stop_on_server_close(self):
        import PAFPlayer as app
        control, launch, child = self.make(enabled=False)
        runtime = control.runtime
        runtime.token = 'test-only-token'
        with patch.object(app, 'paf_workflows', return_value=runtime):
            server = app.PAFWebServer(host='127.0.0.1', port=0)
        control.owner = server
        server._lock_screen_controller = control
        self.assertTrue(server.start())
        connection = http.client.HTTPConnection('127.0.0.1', server.port, timeout=3)
        try:
            connection.request('GET', '/api/lockscreen/settings')
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertFalse(json.loads(response.read())['enabled'])
            connection.request('POST', '/api/lockscreen/settings', json.dumps({'enabled': True}), {'Content-Type': 'application/json'})
            response = connection.getresponse()
            self.assertEqual(response.status, 403)
            response.read()
            self.assertFalse(control.enabled())
            connection.request('POST', '/api/lockscreen/settings', json.dumps({'enabled': True}),
                               {'Content-Type': 'application/json', 'X-PAF-Workflow-Token': runtime.token})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertTrue(json.loads(response.read())['enabled'])
            runtime.save_settings.assert_called_once()
        finally:
            connection.close()
            server.close()
            control.thread.join(timeout=3)
        self.assertFalse(control.thread.is_alive())
        self.assertTrue(control.stop.is_set())

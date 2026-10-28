"""Real HTTP/Wget and player-loop coverage for V417 transport and downloads."""
import contextlib
import http.client
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest
from unittest import mock
from urllib.parse import unquote

import play_audio_file as p


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = p.PAFWebServer(enabled=True, host='127.0.0.1', port=0)
        self.assertTrue(self.server.start())
        self.addCleanup(self.server.close)
        self.conn = http.client.HTTPConnection('127.0.0.1', self.server.port, timeout=5)
        self.addCleanup(self.conn.close)

    def request(self, method, path, body=None, headers=None):
        self.conn.request(method, path, body=body, headers=headers or {})
        response = self.conn.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def test_get_and_head_legacy_controls_execute_once_and_preserve_order(self):
        pairs = [('/play', p.WEB_PLAY), ('/pause', p.PAUSE_TOGGLE), ('/unpause', p.WEB_PLAY),
                 ('/stop', p.WEB_STOP), ('/next', p.NEXT_FILE), ('/prev', p.PREVIOUS_FILE),
                 ('/previous', p.PREVIOUS_FILE)]
        for method in ('GET', 'HEAD'):
            for path, expected in pairs:
                code, headers, data = self.request(method, path)
                self.assertEqual(200, code)
                self.assertGreater(int(headers['Content-Length']), 0)
                if method == 'HEAD': self.assertEqual(b'', data)
                self.assertEqual(expected, self.server.pop_action())
                self.assertIsNone(self.server.pop_action())

    def test_real_wget32_spider_does_not_toggle_twice(self):
        wget = shutil.which('wget32.exe') or shutil.which('wget.exe')
        if not wget: self.skipTest('GNU Wget unavailable')
        for path, action in [('/pause', p.PAUSE_TOGGLE), ('/stop', p.WEB_STOP), ('/play', p.WEB_PLAY)]:
            result = subprocess.run([wget, '--proxy=off', '--tries=1', '--timeout=4', '--spider',
                                     f'http://127.0.0.1:{self.server.port}{path}'], capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(action, self.server.pop_action(), (result.stdout, result.stderr))
            self.assertIsNone(self.server.pop_action())

    def test_main_matches_both_existing_status_parsers(self):
        for playing, paused, stopped, expected in [(True, False, False, 'PLAYING'),
                                                    (True, True, False, 'PAUSED'),
                                                    (False, True, True, 'STOPPED')]:
            self.server.publish(playing=playing, paused=paused, transport_stopped=stopped,
                                track={'filename': 'Playing track Paused in track stopped at track <x>.mp3'})
            for path in ('/main', '/winamp?page=main'):
                code, _, body = self.request('GET', path)
                self.assertEqual(200, code)
                mode = 'UNKNOWN'
                for line in body.decode().splitlines():
                    for needle, result in [('Playing track', 'PLAYING'), ('Paused in track', 'PAUSED'), ('Stopped at track', 'STOPPED')]:
                        if needle in line: mode = result
                self.assertEqual(expected, mode)
                perl = shutil.which('perl.exe') or shutil.which('perl')
                if perl:
                    result = subprocess.run([perl, 'winamp-status-from-file.pl'], input=body, capture_output=True)
                    self.assertEqual(expected, result.stdout.decode())
                self.assertNotIn(b'<x>', body)

    def test_stopped_state_survives_pause_refresh_then_play_clears_it(self):
        self.server.publish(transport_stopped=True, playing=False, paused=True)
        self.server.publish(playing=True, paused=True, position_seconds=0)
        self.assertFalse(self.server.snapshot()['playing'])
        self.server.publish(playing=True, paused=False)
        self.assertFalse(self.server.snapshot()['transport_stopped'])

    def test_download_exact_bytes_head_and_persistent_connection(self):
        path = Path(__file__).with_name('pafplayer_v416_timing_fixture.wav')
        self.assertTrue(path.is_file())
        self.server._current_audio = path
        code, headers, body = self.request('GET', '/api/audio/download?path=C:/not-the-track')
        self.assertEqual(200, code)
        self.assertEqual(path.read_bytes(), body)
        self.assertEqual(len(body), int(headers['Content-Length']))
        self.assertIn('attachment;', headers['Content-Disposition'])
        code, head, body = self.request('HEAD', '/api/audio/download')
        self.assertEqual(200, code)
        self.assertEqual(b'', body)
        self.assertEqual(headers['Content-Length'], head['Content-Length'])
        self.assertEqual(200, self.request('GET', '/api/status')[0])
        self.assertIsNone(self.server.pop_action())

    def test_download_missing_and_no_current_track(self):
        self.assertEqual(404, self.request('GET', '/api/audio/download')[0])
        self.server._current_audio = Path('nonexistent-v417-fixture.mp3')
        self.assertEqual(404, self.request('GET', '/api/audio/download')[0])

    def test_download_tracks_open_file_even_when_playlist_advances(self):
        first = Path(__file__).with_name('pafplayer_v416_timing_fixture.wav')
        with mock.patch.object(self.server, 'current_audio', side_effect=[first, Path('missing')]) as snapshot:
            code, _, data = self.request('GET', '/api/audio/download')
            self.assertEqual(200, code)
            self.assertEqual(first.read_bytes(), data)
            snapshot.assert_called_once()

    def test_per_connection_local_header_and_folder_authorization(self):
        self.assertEqual('1', self.request('GET', '/api/status')[1]['X-PAF-Client-Local'])
        payload = json.dumps({'action': p.WEB_OPEN_TRACK_FOLDER})
        self.assertEqual(202, self.request('POST', '/api/action', payload)[0])
        self.assertEqual(p.WEB_OPEN_TRACK_FOLDER, self.server.pop_action())
        with mock.patch.object(p, 'paf_web_client_is_local', return_value=False):
            self.assertEqual('0', self.request('GET', '/api/status')[1]['X-PAF-Client-Local'])
            self.assertEqual(403, self.request('POST', '/api/action', payload,
                {'Host': 'localhost', 'X-Forwarded-For': '127.0.0.1'})[0])
            self.assertIsNone(self.server.pop_action())
            self.server._current_audio = Path(__file__)
            self.assertEqual(200, self.request('HEAD', '/api/audio/download')[0])


class ClientTests(unittest.TestCase):
    def test_client_addresses(self):
        for peer, server, expected in [('127.0.0.1', '127.0.0.1', True), ('::1', '::1', True),
                ('::ffff:127.0.0.1', '::ffff:127.0.0.1', True),
                ('192.168.1.5', '192.168.1.5', True), ('192.168.1.6', '192.168.1.5', False),
                ('::ffff:192.168.1.5', '192.168.1.5', True), ('garbage', '127.0.0.1', False)]:
            self.assertEqual(expected, p.paf_web_client_is_local(peer, server))

    def test_unicode_and_header_injection_filename(self):
        filename = 'Björk – ❷ 東京.mp3'
        result = p.paf_web_download_disposition(filename)
        result.encode('ascii')
        self.assertEqual(filename, unquote(result.split("filename*=UTF-8''", 1)[1]))
        result = p.paf_web_download_disposition('evil";\r\nX-Fake: test.mp3')
        self.assertNotIn('\r', result)
        self.assertNotIn('\n', result)
        self.assertEqual(2, result.count('"'))

    def test_browser_link_behavior_and_all_javascript_parses(self):
        html = p._paf_web_html()
        js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', html, re.S))
        parsed = subprocess.run(['node', '--check'], input=js, text=True, encoding='utf-8', capture_output=True)
        self.assertEqual(0, parsed.returncode, parsed.stderr)
        start, end = js.index('function updateTrackLinks('), js.index('async function tick(')
        code = '''const assert=require('node:assert/strict');
const path={removeAttribute(k){delete this[k]},setAttribute(k,v){this[k]=v}},download={};
const document={getElementById:id=>id==='path'?path:download};let actions=[];
const action=a=>actions.push(a);
''' + js[start:end] + '''
updateTrackLinks({path:'C:/music/song.mp3'},true);
let prevented=false;path.onclick({preventDefault(){prevented=true}});
assert.equal(prevented,true);assert.deepEqual(actions,['web-open-track-folder']);
assert.equal(path.href,'#');assert.equal(download.hidden,false);
updateTrackLinks({path:'C:/music/song.mp3'},false);
assert.equal(path.href,'/api/audio/download');assert.equal(path.onclick,null);assert.equal(path.download,'');
updateTrackLinks({},false);assert.equal(download.hidden,true);assert.equal(path.href,undefined);
'''
        result = subprocess.run(['node'], input=code, text=True, encoding='utf-8', capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('aria-label="Download current audio file"', html)


class PlayerTests(unittest.TestCase):
    def test_stop_play_stop_while_paused_then_toggle_keep_server_and_reset_position(self):
        class Process:
            def __init__(self): self.running = True
            def poll(self): return None if self.running else 0
            def terminate(self): self.running = False
            kill = terminate
            def wait(self, timeout=None): self.running = False; return 0
        commands, observed = [], []
        clock, paused, position = [100.], [False], [0.]
        server = p.PAFWebServer(enabled=False)
        controller = p.PAFExternalPlaybackCoordinator(None)
        sequence = iter([p.WEB_STOP, p.WEB_PLAY, p.WEB_PAUSE, p.WEB_STOP, p.PAUSE_TOGGLE, p.STOP])
        def factory(command, **kwargs):
            commands.append(command)
            return Process()
        def action():
            observed.append((paused[0], position[0], server.snapshot()))
            clock[0] += 1
            return next(sequence)
        fixture = Path(__file__).with_name('pafplayer_v416_timing_fixture.wav')
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            for name in ('update_lastfm_now_playing_async', 'append_pafplayer_trace', 'record_local_play_history',
                         'write_now_playing_files', 'start_background_audio_health_check'):
                if hasattr(p, name): stack.enter_context(mock.patch.object(p, name))
            result = p.play_audio_file(fixture, ffplay=Path('ffplay.exe'), duration_probe=lambda _: 60,
                key_action_reader=action, process_factory=factory, monotonic=lambda: clock[0], sleeper=lambda _: None,
                install_signal_handlers=False, drcs_visualizer=False, sixel_visualizer=False, lyrics_display=False,
                looping=False, now_playing_targets=[], paused_state=paused, playback_position_state=position,
                initial_position=7, trim_edge_silence=False, manage_winamp=False, web_server=server,
                visualizer_input_source_state=[0],
                external_media_controller=controller, attribute_management_enabled=False, theory_modes={13})
        self.assertEqual('stopped', result)
        self.assertEqual(3, len(commands))
        self.assertEqual(['7.000', '0.000', '0.000'], [cmd[cmd.index('-ss') + 1] for cmd in commands])
        for index in (1, 4):
            self.assertTrue(observed[index][0])
            self.assertEqual(0, observed[index][1])
            self.assertTrue(observed[index][2]['transport_stopped'])
        self.assertFalse(observed[2][2]['transport_stopped'])

    def test_stop_cancels_automatic_resume(self):
        monitor = mock.Mock()
        monitor.snapshot.return_value = {'known': True, 'active': ('VLC',)}
        controller = p.PAFExternalPlaybackCoordinator(monitor)
        monitor.snapshot.return_value = {"known": True, "active": ()}
        controller.filter_action(None, False, 0)
        monitor.snapshot.return_value = {"known": True, "active": ("VLC",)}
        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, controller.filter_action(None, False, 1))
        self.assertEqual(p.WEB_STOP, controller.filter_action(p.WEB_STOP, True, 2))
        monitor.snapshot.return_value = {'known': True, 'active': ()}
        controller.filter_action(None, True, 3)
        self.assertIsNone(controller.filter_action(None, True, 10))


if __name__ == '__main__':
    unittest.main()

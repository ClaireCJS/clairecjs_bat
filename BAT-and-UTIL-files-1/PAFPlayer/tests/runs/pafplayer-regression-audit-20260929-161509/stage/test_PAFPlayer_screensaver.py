"""Sidecar HTTP, settings, compatibility and lifecycle tests; no audio or UI."""
import ast
import http.client
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

import PAFPlayer as app
import PAFPlayer_screensaver as saver
from PAFPlayer_workflows import Runtime


class ScreensaverHTTP(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='screensaver-tests-'))
        self.runtime = Runtime(app, self.root)
        with mock.patch.object(app, 'paf_workflows', return_value=self.runtime):
            self.server = app.PAFWebServer(host='127.0.0.1', port=0)
        with mock.patch.object(app, 'append_pafplayer_trace'):
            self.assertTrue(self.server.start())
        self.addCleanup(self.server.close)
        self.control = saver.controller(self.server)

    def request(self, path='state', payload=None, *, token=True, origin=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.port, timeout=3)
        headers = {}
        if token: headers['X-PAF-Workflow-Token'] = self.runtime.token
        if origin: headers['Origin'] = origin
        body = None if payload is None else json.dumps(payload)
        connection.request('GET' if payload is None else 'POST', '/api/screensaver/' + path, body=body, headers=headers)
        response = connection.getresponse(); data = response.read(); code = response.status
        connection.close()
        return code, data

    def enable(self):
        code, _ = self.request('settings', {'enabled': True})
        self.assertEqual(code, 200)

    def track(self, title='Song', lyric='Current timed line'):
        with self.server._lock:
            self.server._state.update(playing=True, paused=False, transport_stopped=False,
                                      metadata={'Act': 'Artist', 'Title': title, 'private': 'not sent'},
                                      track={'path': 'private/path.flac'}, lyric=lyric,
                                      lyric_timeline=[[0, lyric]])

    def test_default_off_and_no_spectrum_or_audio_activity(self):
        code, raw = self.request()
        self.assertEqual(code, 200)
        self.assertFalse(json.loads(raw)['enabled'])
        self.assertFalse(self.server.client_active())
        self.assertFalse(self.server.status_client_active())
        self.assertFalse(self.server.web_visualizer_active())
        self.assertIsNone(self.server.pop_action())
        self.assertFalse((self.root / 'settings.json').exists())

    def test_sidecar_keeps_status_active_without_enabling_spectrum(self):
        self.enable(); self.request()
        self.assertTrue(self.server.status_client_active())
        self.assertFalse(self.server.web_visualizer_active())
        at = self.server._last_screensaver_activity
        self.assertFalse(self.server.status_client_active(at + 4))

    def test_live_title_lyric_and_pause_updates(self):
        self.enable(); self.track()
        state = json.loads(self.request()[1])
        self.assertEqual((state['title'], state['lyric'], state['status']), ('Artist — Song', 'Current timed line', 'Playing'))
        self.assertNotIn('private', str(state))
        self.track('Second song', 'Second timed line')
        self.server.publish(paused=True)
        state = json.loads(self.request()[1])
        self.assertEqual((state['title'], state['lyric'], state['status']), ('Artist — Second song', 'Second timed line', 'Paused'))

    def test_stopped_clears_presentation(self):
        self.enable(); self.track()
        self.server.publish(playing=False, paused=False, transport_stopped=True)
        state = json.loads(self.request()[1])
        self.assertEqual((state['title'], state['lyric'], state['has_art']), ('', '', False))

    def test_missing_tags_and_lyrics_are_graceful(self):
        self.enable()
        self.server.publish(playing=True, track={'filename': 'untagged.flac'}, metadata={}, lyric='Untimed text', lyric_timeline=[])
        state = json.loads(self.request()[1])
        self.assertEqual(state['title'], 'untagged.flac')
        self.assertEqual(state['lyric'], '')
        self.assertFalse(state['has_art'])

    def test_settings_persist_and_preserve_existing_namespaces_and_unknown_keys(self):
        self.runtime.settings['windows_media'] = {'enabled': True, 'brightness': 83}
        self.runtime.settings['visual_screensaver'] = {'future_option': 'keep'}
        self.enable()
        self.assertEqual(self.request('settings', {'brightness': 21})[0], 200)
        stored = json.loads((self.root / 'settings.json').read_text())
        self.assertEqual(stored['visual_screensaver'], {'future_option': 'keep', 'enabled': True, 'brightness': 21})
        self.assertEqual(stored['windows_media'], {'enabled': True, 'brightness': 83})
        self.assertTrue(list(self.root.glob('settings.json.bak.*.replaced-by-chatgpt*.bak')))
        reloaded = Runtime(app, self.root)
        self.assertEqual(saver.settings(reloaded), {'enabled': True, 'brightness': 21})

    def test_failed_save_rolls_back_runtime(self):
        old = dict(self.runtime.settings)
        with mock.patch.object(self.runtime, 'save_settings', side_effect=OSError('disk unavailable')):
            self.assertEqual(self.request('settings', {'enabled': True})[0], 400)
        self.assertEqual(self.runtime.settings, old)

    def test_bad_settings_are_rejected_without_mutation(self):
        for payload in ({'enabled': 'yes'}, {'brightness': True}, {'brightness': -1}, {'brightness': 101}, {'brightness': 3.5}, {'other_id': 1}):
            with self.subTest(payload=payload): self.assertEqual(self.request('settings', payload)[0], 400)
        self.assertFalse(saver.settings(self.runtime)['enabled'])

    def test_write_requires_pairing_token_and_same_origin(self):
        self.assertEqual(self.request('settings', {'enabled': True}, token=False)[0], 403)
        self.assertEqual(self.request('settings', {'enabled': True}, origin='https://example.invalid')[0], 403)
        self.assertFalse(saver.settings(self.runtime)['enabled'])

    def test_remote_reads_are_rejected(self):
        handler = mock.Mock(client_address=('192.0.2.10', 1234), command='GET')
        self.assertTrue(saver.handle(handler, self.server, '/api/screensaver/state'))
        self.assertEqual(handler._json.call_args.args[0], 403)

    def test_art_revision_prevents_old_track_cover(self):
        self.enable(); self.track()
        with self.server._lock:
            self.server._art_variants = [b'cover']; self.server._art_variant_mimes = ['image/jpeg']
        revision = json.loads(self.request()[1])['art_revision']
        self.assertEqual(self.request('art?revision=' + revision), (200, b'cover'))
        with self.server._lock: self.server._art_worker_generation += 1
        self.assertEqual(self.request('art?revision=' + revision)[0], 404)
        with self.server._lock: self.server._art_variants = []
        self.assertFalse(json.loads(self.request()[1])['has_art'])

    def test_oversized_art_is_not_transferred(self):
        self.enable(); self.track()
        self.server._art_variants = [b'12345']; self.server._art_variant_mimes = ['image/jpeg']
        with mock.patch.object(saver, 'MAX_ART_BYTES', 4):
            state = json.loads(self.request()[1])
            self.assertFalse(state['has_art'])
            self.assertEqual(self.request('art?revision=' + state['art_revision'])[0], 404)

    def test_disabled_art_does_not_leak_current_cover(self):
        self.server._art_variants = [b'cover']; self.server._art_variant_mimes = ['image/jpeg']
        self.assertEqual(self.request('art?revision=anything')[0], 404)

    def test_start_is_explicit_and_duplicate_clicks_do_not_spawn_twice(self):
        executable = self.root / 'PAFPlayer.scr'; executable.write_bytes(b'fixture')
        process = mock.Mock(); process.poll.return_value = None
        with mock.patch.object(self.control, 'executable', return_value=executable), mock.patch.object(saver.subprocess, 'Popen', return_value=process) as spawn:
            self.assertEqual(self.request('show', {})[0], 400); spawn.assert_not_called()
            self.enable(); spawn.assert_not_called()
            self.assertEqual(self.request('show', {})[0], 200)
            self.assertEqual(self.request('show', {})[0], 200)
            spawn.assert_called_once()
            self.assertEqual(spawn.call_args.args[0], [str(executable), '/s', f'/port:{self.server.port}'])
            self.assertIsNone(self.server.pop_action())
            self.assertEqual(self.request('settings', {'enabled': False})[0], 200)
            process.terminate.assert_called_once()

    def test_close_revision_reaches_windows_started_sidecar(self):
        self.enable(); before = json.loads(self.request()[1])['close_revision']
        self.assertEqual(self.request('close', {})[0], 200)
        self.assertEqual(json.loads(self.request()[1])['close_revision'], before + 1)

    def test_missing_executable_and_launch_error_leave_audio_untouched(self):
        self.enable()
        with mock.patch.object(self.control, 'executable', return_value=self.root / 'missing.scr'):
            self.assertEqual(self.request('show', {})[0], 400)
        executable = self.root / 'present.scr'; executable.write_bytes(b'fixture')
        with mock.patch.object(self.control, 'executable', return_value=executable), mock.patch.object(saver.subprocess, 'Popen', side_effect=OSError('launch failed')):
            self.assertEqual(self.request('show', {})[0], 400)
        self.assertIsNone(self.server.pop_action())


class Compatibility(unittest.TestCase):
    def test_existing_configuration_constants_and_bundle_sources_unchanged(self):
        before = ast.parse(Path('PAFPlayer_v471_before_visual_screensaver.py').read_text(encoding='utf-8-sig'))
        after = ast.parse(Path(app.__file__).read_text(encoding='utf-8-sig'))
        def assignments(tree):
            return {node.targets[0].id: ast.dump(node.value) for node in tree.body
                    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
        old, new = assignments(before), assignments(after)
        for key, value in old.items():
            if key not in {'PLAYER_BUILD_ID', 'PROGRAM_VERSION', 'PROGRAM_RELEASE_LABEL'}:
                self.assertEqual(new[key], value, key)

    def test_embedded_bridge_matches_source(self):
        self.assertEqual(app._PAF_BUNDLED_SOURCES['PAFPlayer_screensaver'], Path('PAFPlayer_screensaver.py').read_text(encoding='utf-8'))

    def test_ui_keeps_existing_windows_ids_and_adds_unique_sidecar_ids(self):
        page = app._paf_web_html()
        for name in ('windowsMediaSection', 'windowsBrightness', 'visualScreensaverEnabled', 'visualScreensaverBrightness', 'visualScreensaverShow', 'visualScreensaverClose'):
            self.assertEqual(page.count('id="' + name + '"'), 1, name)
        self.assertIn('data-windows-setting="enabled"', page)
        self.assertIn('does not replace the Windows lock screen', page)

    def test_short_text_and_no_control_escape_sequences(self):
        self.assertEqual(saver.clean_text('\x1b[31mHello\x00', 5), 'Hello')


if __name__ == '__main__': unittest.main()

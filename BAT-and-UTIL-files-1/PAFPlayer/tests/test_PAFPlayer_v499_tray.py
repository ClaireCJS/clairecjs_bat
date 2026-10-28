import io
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import types
import unittest
from unittest import mock

import PAFPlayer as player
import PAFPlayer_web_workflows as web
from PAFPlayer_instance import Instance
from PAFPlayer_tray import ClickSequence, TrayController, augment, configure, enabled, parse_options


class FakeServer:
    enabled = True
    _httpd = object()
    url = 'http://127.0.0.1:666/'

    def __init__(self):
        self.actions = []
        self.exits = 0
        self.audio = None

    def enqueue_action(self, action):
        self.actions.append(action)
        return True

    def enqueue_tray_exit(self): self.exits += 1
    def current_audio(self): return self.audio
    def snapshot(self): return {'paused': False}


class FakeInstance:
    def __init__(self, owner=True): self.owner = owner
    def owns(self): return self.owner


class TrayTests(unittest.TestCase):
    def runtime(self, saved=1):
        server = FakeServer()
        app = types.SimpleNamespace(
            load_player_settings=lambda: {'TrayIconEnabled': saved},
            save_player_settings=mock.Mock(),
            PREVIOUS_FILE=player.PREVIOUS_FILE, NEXT_FILE=player.NEXT_FILE,
            PAUSE_TOGGLE=player.PAUSE_TOGGLE, PROGRAM_VERSION=player.PROGRAM_VERSION,
            AUDIO_EXTENSIONS=player.AUDIO_EXTENSIONS)
        return types.SimpleNamespace(app=app, server=server)

    def test_triple_left_previous_and_triple_right_next(self):
        clicks = ClickSequence(.5)
        self.assertIsNone(clicks.click('left', 0))
        self.assertIsNone(clicks.click('left', .24))
        self.assertEqual('previous', clicks.click('left', .47))
        self.assertIsNone(clicks.expire(1))
        self.assertIsNone(clicks.click('right', 2))
        self.assertIsNone(clicks.click('right', 2.3))
        self.assertEqual('next', clicks.click('right', 2.6))

    def test_double_click_pauses_after_window_and_single_right_delays_menu(self):
        clicks = ClickSequence(.5)
        self.assertIsNone(clicks.click('left', 0))
        self.assertIsNone(clicks.click('left', .2))
        self.assertIsNone(clicks.expire(.69))
        self.assertEqual('pause', clicks.expire(.7))
        self.assertIsNone(clicks.click('right', 1))
        self.assertIsNone(clicks.expire(1.49))
        self.assertEqual('menu', clicks.expire(1.5))
        self.assertIsNone(clicks.expire(2))
        self.assertIsNone(clicks.click('right', 3))
        self.assertIsNone(clicks.click('right', 3.2))
        self.assertEqual('pause', clicks.expire(3.8))

    def test_triple_right_suppresses_menu(self):
        clicks = ClickSequence(.5)
        for when in (0, .2): self.assertIsNone(clicks.click('right', when))
        self.assertEqual('next', clicks.click('right', .4))
        self.assertIsNone(clicks.expire(1))

    def test_command_routing_is_owner_local_and_cleanup(self):
        official = self.runtime()
        background = self.runtime()
        owner = FakeInstance(True)
        other = FakeInstance(False)
        tray = TrayController(official, owner)
        stray = TrayController(background, other)
        self.assertTrue(tray.dispatch('previous'))
        self.assertTrue(tray.dispatch('next'))
        self.assertTrue(tray.dispatch('pause'))
        self.assertEqual([player.PREVIOUS_FILE, player.NEXT_FILE, player.PAUSE_TOGGLE], official.server.actions)
        self.assertFalse(stray.dispatch('next'))
        self.assertEqual([], background.server.actions)
        owner.owner = False
        other.owner = True
        self.assertFalse(tray.dispatch('next'))
        self.assertTrue(stray.dispatch('next'))
        self.assertEqual([player.NEXT_FILE], background.server.actions)
        self.assertTrue(stray.dispatch('exit'))
        self.assertEqual(1, background.server.exits)
        stray.close()
        self.assertFalse(stray.dispatch('next'))

    def test_default_cli_precedence_and_web_control(self):
        self.assertTrue(enabled({}))
        self.assertEqual((['song.mp3'], True, False), parse_options(['--tray', 'song.mp3']))
        self.assertEqual((['song.mp3'], False, False), parse_options(['--no-tray', 'song.mp3']))
        self.assertEqual((['song.mp3'], None, True), parse_options(['--instance', 'song.mp3']))
        runtime = self.runtime(saved=0)
        tray = TrayController(runtime, FakeInstance(), override=True)
        runtime.tray = tray
        self.assertTrue(tray.wants_icon())
        self.assertFalse(tray.status()['saved_enabled'])
        self.assertTrue(tray.status()['enabled'])
        self.assertIn('trayIconEnabled', augment('<body><div class="group section-global-config" id="globalConfigSection"></div></body>'))
        with self.assertRaises(ValueError): configure(runtime, {'enabled': 'yes'})
        with mock.patch.object(tray, 'refresh') as refresh:
            configure(runtime, {'enabled': True})
            refresh.assert_called_once()
        runtime.app.save_player_settings.assert_called_once_with({'TrayIconEnabled': 1})

    def test_registry_default_and_saved_value(self):
        self.assertEqual(1, player.PLAYER_SETTING_DEFAULTS['TrayIconEnabled'])
        def query(name):
            if name == 'TrayIconEnabled': return 0, 4
            raise OSError('missing fixture value')
        with mock.patch.object(player, 'paf_registry_query_value', side_effect=query):
            self.assertEqual(0, player.load_player_settings()['TrayIconEnabled'])

    def test_web_status_schema_and_saved_control_endpoint(self):
        runtime = self.runtime()
        runtime.tray = TrayController(runtime, FakeInstance())
        runtime.settings = {}
        runtime.token = 'local-test-token'
        runtime.queue_history = []
        runtime.monitor = None
        runtime.index = {}
        runtime.windows_media = types.SimpleNamespace(status={})
        owner = types.SimpleNamespace(workflows=runtime)
        responses = []
        handler = types.SimpleNamespace(command='GET', headers={},
                                        _json=lambda code, value: responses.append((code, value)))
        with mock.patch.object(web, 'authorized', return_value=True), mock.patch.object(web, 'queue_snapshot', return_value={}):
            self.assertTrue(web.handle(handler, owner, '/api/workflows/status'))
        self.assertEqual(200, responses[-1][0])
        self.assertTrue(responses[-1][1]['tray']['saved_enabled'])
        self.assertEqual('official', responses[-1][1]['tray']['owner'])
        payload = b'{"enabled":false}'
        handler.command = 'POST'
        handler.headers = {'Content-Length': str(len(payload))}
        handler.rfile = io.BytesIO(payload)
        handler.connection = types.SimpleNamespace(settimeout=lambda value: None)
        with mock.patch.object(web, 'authorized', return_value=True):
            self.assertTrue(web.handle(handler, owner, '/api/workflows/tray'))
        self.assertEqual(200, responses[-1][0])
        runtime.app.save_player_settings.assert_called_once_with({'TrayIconEnabled': 0})

    @unittest.skipUnless(os.name == 'nt', 'Windows tray ownership')
    def test_only_official_starts_one_icon_and_shutdown_stops_thread(self):
        runtime = self.runtime()
        official = TrayController(runtime, FakeInstance(True))
        second = TrayController(runtime, FakeInstance(False))
        created = []
        def fake_native_run(controller):
            created.append(controller)
            controller._hwnd = 1
            controller._visible = True
            controller._ready.set()
            while not controller._closing: time.sleep(.005)
            controller._visible = False
            controller._hwnd = None
        with mock.patch.object(TrayController, '_run', fake_native_run):
            self.assertTrue(official.start())
            self.assertFalse(second.start())
            self.assertTrue(official.start())
            self.assertEqual([official], created)
            official.close()
            self.assertFalse(official._thread.is_alive())
            self.assertFalse(official._visible)

    @unittest.skipUnless(os.name == 'nt', 'Windows mutex ownership')
    def test_official_claim_explicit_handoff_and_stale_descriptor(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = types.SimpleNamespace(root=Path(folder), app=types.SimpleNamespace(),
                                            log=lambda *args, **kwargs: None)
            official = Instance(runtime)
            self.assertTrue(official.acquire())
            official.start()
            initial = json.loads((runtime.root / 'instance.json').read_text())
            explicit = Instance(runtime)
            self.assertFalse(explicit.acquire())
            self.assertFalse(explicit.owns())
            observed = threading.Event()
            explicit.watch_for_claim(observed.set)
            try:
                self.assertFalse(observed.wait(.8))
                official.close()
                self.assertTrue(observed.wait(4), 'remaining eligible instance did not claim mutex')
                self.assertTrue(explicit.owns())
                claimed = json.loads((runtime.root / 'instance.json').read_text())
                self.assertNotEqual(initial['identity'], claimed['identity'])
                self.assertEqual(explicit.identity, claimed['identity'])
                normal = Instance(runtime)
                self.assertFalse(normal.acquire())
            finally:
                official.close()
                explicit.close()
            successor = Instance(runtime)
            self.assertTrue(successor.acquire())
            successor.close()


if __name__ == '__main__': unittest.main()

"""V504 per-machine tray lyric and desktop-wallpaper regression tests."""

import io
import os
from pathlib import Path
import types
import unittest
from unittest import mock

import PAFPlayer as app
import PAFPlayer_track_details as details
import PAFPlayer_tray_machine as machine
import PAFPlayer_remote_tray as remote
from PAFPlayer_tray import TrayController


class FakeSettings:
    def __init__(self, **values):
        self.values = {'lyrics_tooltip': False, 'album_wallpaper': False, **values}
        self.lease = ('', '')

    def options(self):
        return dict(self.values)

    def set_option(self, name, enabled):
        self.values[name] = enabled

    def wallpaper_lease(self):
        return self.lease

    def save_wallpaper_lease(self, original, applied):
        self.lease = (original, applied)


class FakeServer:
    def __init__(self):
        self.connected = True
        self.owner_identity = 'official-1'
        self.poll_interval = 2.0
        self.state = {'program': 'PAFplayer', 'version': 'V504', 'playing': True,
                      'paused': False, 'track': {'path': 'C:/music/song.mp3'},
                      'art_count': 1, 'art_generation': 7, 'lyric': 'First lyric'}
        self.wallpaper_calls = []

    def snapshot(self):
        return dict(self.state)

    def wallpaper(self, generation, width, height):
        self.wallpaper_calls.append((generation, width, height))
        return b'BMexample'


class TrayMachineTests(unittest.TestCase):
    def effect(self, **options):
        server = FakeServer()
        settings = FakeSettings(**options)
        refreshed = []
        effect = machine.TrayMachineEffects(server, types.SimpleNamespace(owns=lambda: True),
                                            lambda: refreshed.append(True), remote=True,
                                            settings=settings)
        return effect, server, settings, refreshed

    def test_defaults_off_and_machine_scoped_store(self):
        self.assertEqual({'lyrics_tooltip': False, 'album_wallpaper': False,
                          'remote_hotkeys': True, 'remote_floating_lyrics': False,
                          'remote_album_art': False},
                         machine.MachineSettings().options() if os.name != 'nt' else
                         self._missing_registry_options())
        self.assertIn('TrayMachine', machine.REGISTRY_PATH)
        self.assertNotIn('TrayIconEnabled', machine.OPTION_VALUES.values())

    @staticmethod
    def _missing_registry_options():
        store = machine.MachineSettings()
        with mock.patch('winreg.OpenKey', side_effect=FileNotFoundError):
            return store.options()

    def test_lyric_tooltip_follows_current_line_and_remains_local(self):
        effect, server, settings, refreshed = self.effect(lyrics_tooltip=True)
        effect.step()
        self.assertEqual('First lyric', effect.tooltip_lyric())
        self.assertEqual(.4, server.poll_interval)
        server.state['lyric'] = 'Second\n lyric'
        effect.step()
        self.assertEqual('Second lyric', effect.tooltip_lyric())
        self.assertEqual(2, len(refreshed))
        server.connected = False
        effect.step()
        self.assertEqual('', effect.tooltip_lyric())
        self.assertTrue(effect.toggle('lyrics_tooltip'))
        self.assertFalse(settings.values['lyrics_tooltip'])
        self.assertEqual({}, {key: value for key, value in server.state.items() if key.startswith('Tray')})

    def test_wallpaper_uses_current_owner_and_restores_on_disable(self):
        effect, server, settings, _refreshed = self.effect(album_wallpaper=True)
        current = ['C:/wallpapers/original.bmp']
        applied = []
        def put(path):
            current[0] = str(path)
            applied.append(str(path))
        with mock.patch.object(effect, '_claim_wallpaper', return_value=True), \
             mock.patch.object(effect, '_release_wallpaper'), \
             mock.patch.object(machine.ctypes.windll.user32, 'GetSystemMetrics', side_effect=[1920, 1080]), \
             mock.patch.object(machine, 'cache_bitmap', return_value=Path('C:/cache/album-a.bmp')), \
             mock.patch.object(machine, 'current_wallpaper', side_effect=lambda: current[0]), \
             mock.patch.object(machine, 'set_wallpaper', side_effect=put), \
             mock.patch.object(machine, 'recycle_cached'):
            effect.step()
            self.assertEqual([(7, 1920, 1080)], server.wallpaper_calls)
            self.assertEqual('C:/wallpapers/original.bmp', settings.lease[0])
            self.assertTrue(machine.same_wallpaper('C:/cache/album-a.bmp', current[0]))
            self.assertTrue(effect.toggle('album_wallpaper'))
            effect.step()
        self.assertEqual('C:/wallpapers/original.bmp', current[0])
        self.assertEqual(('', ''), settings.lease)
        self.assertEqual(2, len(applied))

    def test_wallpaper_does_not_replace_user_change_or_stale_owner(self):
        effect, server, settings, _refreshed = self.effect(album_wallpaper=True)
        settings.lease = ('C:/original.bmp', 'C:/cache/album-old.bmp')
        effect._original, effect._applied = settings.lease
        server.owner_identity = 'official-2'
        server.connected = False
        with mock.patch.object(effect, '_claim_wallpaper', return_value=True), \
             mock.patch.object(effect, '_release_wallpaper'), \
             mock.patch.object(machine, 'current_wallpaper', return_value='C:/user/new.bmp'), \
             mock.patch.object(machine, 'set_wallpaper') as set_background, \
             mock.patch.object(machine, 'recycle_cached'):
            effect.step()
        set_background.assert_not_called()
        self.assertEqual(('', ''), settings.lease)
        self.assertEqual([], server.wallpaper_calls)

    def test_failed_new_art_restores_previous_track_background(self):
        effect, server, settings, _refreshed = self.effect(album_wallpaper=True)
        effect._original = 'C:/original.bmp'
        effect._applied = 'C:/cache/album-old.bmp'
        effect._last_key = ('official-1', 'C:/music/old.mp3', 6)
        effect._last_attempt = -1000
        current = ['C:/cache/album-old.bmp']
        with mock.patch.object(effect, '_claim_wallpaper', return_value=True), \
             mock.patch.object(effect, '_release_wallpaper'), \
             mock.patch.object(effect, '_bitmap', return_value=None), \
             mock.patch.object(machine.ctypes.windll.user32, 'GetSystemMetrics', side_effect=[800, 600]), \
             mock.patch.object(machine, 'current_wallpaper', side_effect=lambda: current[0]), \
             mock.patch.object(machine, 'set_wallpaper', side_effect=lambda path: current.__setitem__(0, str(path))), \
             mock.patch.object(machine, 'recycle_cached'):
            effect.step()
        self.assertEqual('C:/original.bmp', current[0])
        self.assertEqual(('', ''), settings.lease)

    def test_wallpaper_route_rejects_nonowner_then_serves_bmp(self):
        server = app.PAFWebServer(enabled=False)
        owner = types.SimpleNamespace(identity='current', owns=lambda: False)
        server.workflows = types.SimpleNamespace(instance=owner)
        with server._lock:
            server._state.update(art_generation=9, art_count=1)
            server._art_variants = [b'art']
            server._art_variant_mimes = ['image/png']
        responses = []
        handler = types.SimpleNamespace(
            path='/api/track-details/wallpaper?generation=9&width=800&height=600&identity=current',
            _json=lambda status, data: responses.append((status, data)),
            _send=lambda status, data, mime: responses.append((status, data, mime)))
        self.assertTrue(details.handle(handler, server, '/api/track-details/wallpaper', app))
        self.assertEqual(409, responses[-1][0])
        owner.owns = lambda: True
        with mock.patch.object(details, 'wallpaper_bitmap', return_value=b'BMP'):
            details.handle(handler, server, '/api/track-details/wallpaper', app)
        self.assertEqual((200, b'BMP', 'image/bmp'), responses[-1])
        handler.path = handler.path.replace('generation=9', 'generation=8')
        details.handle(handler, server, '/api/track-details/wallpaper', app)
        self.assertEqual(404, responses[-1][0])

    def test_wallpaper_bitmap_is_bounded_and_owner_change_during_render_is_rejected(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow is unavailable on the player server')
        picture = io.BytesIO()
        Image.new('RGB', (200, 200), 'red').save(picture, format='PNG')
        bitmap = details.wallpaper_bitmap(picture.getvalue(), 800, 600)
        self.assertTrue(bitmap.startswith(b'BM'))
        self.assertIsNone(details.wallpaper_bitmap(picture.getvalue(), 4000, 3000))
        server = app.PAFWebServer(enabled=False)
        owner = types.SimpleNamespace(identity='first', owns=lambda: True)
        server.workflows = types.SimpleNamespace(instance=owner)
        with server._lock:
            server._state.update(art_generation=11, art_count=1)
            server._art_variants = [picture.getvalue()]
            server._art_variant_mimes = ['image/png']
        responses = []
        handler = types.SimpleNamespace(
            path='/api/track-details/wallpaper?generation=11&width=800&height=600&identity=first',
            _json=lambda status, data: responses.append((status, data)),
            _send=lambda status, data, mime: responses.append((status, data, mime)))
        def change_owner(*_args):
            owner.identity = 'successor'
            return b'BM'
        with mock.patch.object(details, 'wallpaper_bitmap', side_effect=change_owner):
            details.handle(handler, server, '/api/track-details/wallpaper', app)
        self.assertEqual(409, responses[-1][0])

    def test_remote_bitmap_request_uses_verified_owner(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow is unavailable on the player server')
        picture = io.BytesIO()
        Image.new('RGB', (32, 32), 'blue').save(picture, format='PNG')
        server = app.PAFWebServer(host='127.0.0.1', port=0)
        owner = types.SimpleNamespace(identity='official', owns=lambda: True)
        server.workflows = types.SimpleNamespace(instance=owner)
        with server._lock:
            server._state.update(playing=True, paused=False, art_generation=6, art_count=1)
            server._art_variants = [picture.getvalue()]
            server._art_variant_mimes = ['image/png']
        self.assertTrue(server.start())
        try:
            client = remote.RemoteServer('127.0.0.1:' + str(server.port))
            self.assertTrue(client.poll_once())
            self.assertTrue(client.wallpaper(6, 800, 600).startswith(b'BM'))
            owner.identity = 'successor'
            with self.assertRaises(Exception):
                client.wallpaper(6, 800, 600)
            client.close()
        finally:
            server.close()

    def test_official_menu_exposes_both_machine_options(self):
        server = types.SimpleNamespace(current_audio=lambda: None)
        runtime = types.SimpleNamespace(server=server,
                                        app=types.SimpleNamespace(PROGRAM_VERSION='V504'))
        tray = TrayController(runtime, types.SimpleNamespace(owns=lambda: True))
        effect = types.SimpleNamespace(options={'lyrics_tooltip': True, 'album_wallpaper': False},
                                       tooltip_lyric=lambda: 'Now singing', toggle=mock.Mock(return_value=True))
        tray._machine = effect
        names = [row[1] for row in tray.menu_items({})]
        self.assertTrue(any('Show sung lyrics above tray' in name for name in names))
        self.assertTrue(any('Album art desktop wallpaper' in name for name in names))
        self.assertNotIn('Now singing', tray.tooltip_text())
        self.assertTrue(tray.dispatch('machine_album_wallpaper'))
        effect.toggle.assert_called_once_with('album_wallpaper')

    @unittest.skipUnless(os.name == 'nt', 'Windows tray-only mode')
    def test_tray_only_menu_has_local_options_without_starting_playback(self):
        observed = []
        fake_effect = types.SimpleNamespace(
            options={'lyrics_tooltip': False, 'album_wallpaper': False},
            tooltip_lyric=lambda: '', last_error='', start=lambda: None,
            close=lambda: None, toggle=mock.Mock(return_value=True))
        def fake_start(tray):
            observed.extend(tray.menu_items({}))
            tray._thread = types.SimpleNamespace(is_alive=lambda: False)
            self.assertTrue(tray.dispatch('machine_lyrics_tooltip'))
            return True
        with mock.patch.object(machine, 'TrayMachineEffects', return_value=fake_effect), \
             mock.patch.object(remote.RemoteServer, 'start_polling'), \
             mock.patch.object(remote.RemoteServer, 'close'), \
             mock.patch.object(TrayController, 'start', fake_start), \
             mock.patch.object(TrayController, 'close'), \
             mock.patch.object(app, 'paf_workflows', side_effect=AssertionError('playback started')):
            address = 'paf-v504-menu-' + os.urandom(6).hex() + ':666'
            self.assertEqual(0, remote.run_tray_only([address]))
        self.assertTrue(any('Show sung lyrics above tray' in row[1] for row in observed))
        self.assertTrue(any('Album art desktop wallpaper' in row[1] for row in observed))
        fake_effect.toggle.assert_called_once_with('lyrics_tooltip')


if __name__ == '__main__':
    unittest.main()

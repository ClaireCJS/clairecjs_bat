"""V522 remote controls, hover metadata, and synchronized lyric regression tests."""
import time
import types
import unittest
import inspect
import tempfile
from unittest import mock
from urllib.parse import parse_qs, urlsplit

import PAFPlayer as app
from PAFPlayer_remote_tray import (RemoteHotkeys, RemoteServer, RemoteTrayAppSettings,
                                   synchronized_position)
from PAFPlayer_remote_overlay import lyric_at
from PAFPlayer_tray_hover import hover_facts
from PAFPlayer_tray_machine import OPTION_DEFAULTS
from PAFPlayer_tray import augment


class RemoteControlsTests(unittest.TestCase):
    def test_remote_tray_settings_are_endpoint_specific_and_persistent(self):
        with tempfile.TemporaryDirectory() as folder:
            first = RemoteTrayAppSettings('demona:666', folder)
            second = RemoteTrayAppSettings('wyvern:666', folder)
            first.save_player_settings({'TrayIconStyle': 137})
            first.set_option('remote_floating_lyrics', True)
            self.assertEqual(137, RemoteTrayAppSettings('DEMONA:666', folder).load_player_settings()['TrayIconStyle'])
            self.assertTrue(RemoteTrayAppSettings('DEMONA:666', folder).options()['remote_floating_lyrics'])
            self.assertNotEqual(first.path, second.path)
            self.assertEqual({}, second.load_player_settings())

    def test_remote_floating_lyrics_use_the_player_renderer(self):
        source = inspect.getsource(__import__('PAFPlayer_remote_overlay'))
        self.assertIn('app.ExternalAlbumArtWindow(enabled=False)', source)
        self.assertIn('lyric_renderer.update_lyric(', source)
        self.assertIn('lyric_renderer.set_playback_position(', source)
        self.assertNotIn("lyrics = tk.Toplevel(root)", source)
        self.assertNotIn('lyric_label = tk.Label', source)

    def test_remote_renderer_preferences_use_endpoint_appdata_backend(self):
        source = inspect.getsource(RemoteTrayAppSettings.install_player_preference_backend)
        self.assertIn('app_module.paf_registry_query_value = query', source)
        self.assertIn('app_module.paf_registry_set_value = set_value', source)
        self.assertIn("settings.setdefault('RendererPreferences', {})", source)

    def sample(self, capture, *names, now=1.0, epoch=100.0):
        codes = {capture.VK[name] for name in names}
        return capture.sample(lambda code: code in codes, now=now, epoch=epoch)

    def test_volume_hold_repeats_without_flooding(self):
        h = RemoteHotkeys()
        self.assertEqual([('server', 'volume_up', 100.0)], self.sample(h, 'ctrl', 'alt', 'up'))
        self.assertEqual([], self.sample(h, 'ctrl', 'alt', 'up', now=1.1))
        self.assertEqual([('server', 'volume_up', 100.0)], self.sample(h, 'ctrl', 'alt', 'up', now=1.33))
        self.assertEqual([('server', 'volume_up', 100.0)], self.sample(h, 'ctrl', 'alt', 'up', now=1.42))
        self.sample(h, now=1.5)
        self.assertEqual([('server', 'volume_up', 100.0)], self.sample(h, 'ctrl', 'alt', 'up', now=1.6))

    def test_remote_vs_local_overlay_chords(self):
        h = RemoteHotkeys()
        self.assertEqual([('local', 'floating_toggle', 100.0)], self.sample(h, 'ctrl', 'alt', 'f'))
        self.sample(h, now=1.1)
        self.assertEqual([('local', 'floating_toggle', 100.0)], self.sample(h, 'ctrl', 'alt', 'shift', 'f', now=1.2))
        self.sample(h, now=1.3)
        self.assertEqual([('local', 'art_toggle', 100.0)], self.sample(h, 'ctrl', 'alt', 'a', now=1.4))
        self.sample(h, now=1.5)
        self.assertEqual([('local', 'art_toggle', 100.0)], self.sample(h, 'ctrl', 'alt', 'shift', 'a', now=1.6))

    def test_remote_timeline_is_downloaded_once_per_revision(self):
        server = RemoteServer('musicbox:666')
        replies = [
            {'program': 'PAFPlayer', 'version': 'V560', 'official': True,
             'identity': 'owner', 'server_epoch': 100.0,
             'state': {'program': 'PAFPlayer', 'version': 'V560',
                       'lyric_timeline_revision': 7}},
            {'program': 'PAFPlayer', 'version': 'V560', 'official': True,
             'identity': 'owner', 'server_epoch': 100.0,
             'state': {'program': 'PAFPlayer', 'version': 'V560',
                       'lyric_timeline_revision': 7,
                       'lyric_timeline': [[1.0, 'first']]}},
            {'program': 'PAFPlayer', 'version': 'V560', 'official': True,
             'identity': 'owner', 'server_epoch': 101.0,
             'state': {'program': 'PAFPlayer', 'version': 'V560',
                       'lyric_timeline_revision': 7}},
        ]
        with mock.patch.object(server, 'json', side_effect=replies) as request:
            self.assertTrue(server.poll_once())
            self.assertEqual([[1.0, 'first']], server.snapshot()['lyric_timeline'])
            self.assertTrue(server.poll_once())
            self.assertEqual([[1.0, 'first']], server.snapshot()['lyric_timeline'])
        self.assertEqual(3, request.call_count)
        self.assertEqual(1.0, server.poll_interval)

    def test_media_and_win_c(self):
        h = RemoteHotkeys()
        self.assertEqual([('server', 'pause', 100.0)], self.sample(h, 'win_l', 'c'))
        self.assertEqual([], self.sample(h, 'win_l', 'c', now=1.1))
        self.sample(h, now=1.2)
        self.assertEqual([('server', 'pause', 100.0)], self.sample(h, 'media_pause', now=1.3))
        self.sample(h, now=1.4)
        self.assertEqual([('server', 'seek_back', 100.0)], self.sample(h, 'media_prev', now=1.5))
        self.sample(h, now=1.6)
        self.assertEqual([('server', 'next', 100.0)], self.sample(h, 'ctrl', 'alt', 'media_next', now=1.7))
        self.sample(h, now=1.8)
        self.assertEqual([('server', 'previous', 100.0)], self.sample(h, 'ctrl', 'media_prev', now=1.9))

    def test_verified_command_and_timestamp(self):
        server = RemoteServer('musicbox:666')
        server.connected, server.owner_identity = True, 'owner-123'
        with mock.patch.object(server, 'json', return_value={'accepted': True}) as request:
            self.assertTrue(server.command('volume_down', 123.456))
        values = parse_qs(urlsplit(request.call_args.args[0]).query)
        self.assertEqual('owner-123', values['identity'][0])
        self.assertEqual('123.456000', values['client_epoch'][0])
        self.assertFalse(server.command('pause', expected_identity='stale-owner'))
        with self.assertRaises(ValueError): server.command('arbitrary')
        server.close()

    def test_live_server_routes_only_to_verified_official_owner(self):
        server = app.PAFWebServer(host='127.0.0.1', port=0)
        owner = types.SimpleNamespace(identity='official-one', owns=lambda: True)
        server.workflows = types.SimpleNamespace(instance=owner)
        self.assertTrue(server.start())
        client = RemoteServer('127.0.0.1:' + str(server.port))
        try:
            self.assertTrue(client.poll_once())
            for action, expected in (('volume_up', app.VOLUME_UP_5),
                                     ('volume_down', app.VOLUME_DOWN_5),
                                     ('art_foreground', app.EXTERNAL_ALBUM_ART_FOREGROUND),
                                     ('floating_foreground', app.EXTERNAL_FLOATING_LYRICS_FOREGROUND),
                                     ('seek_back', app.SEEK_BACK_10),
                                     ('seek_forward_fast', app.SEEK_FORWARD_80)):
                self.assertTrue(client.command(action, expected_identity='official-one'))
                self.assertEqual(expected, server.pop_action())
            owner.identity = 'official-two'
            self.assertFalse(client.command('pause', expected_identity='official-one'))
            self.assertIsNone(server.pop_action())
            self.assertTrue(client.poll_once())
            self.assertTrue(client.command('pause', expected_identity='official-two'))
            self.assertEqual(app.PAUSE_TOGGLE, server.pop_action())
        finally:
            client.close()
            server.close()

    def test_native_win_c_and_ctrl_alt_f_are_latched_and_configurable(self):
        import msvcrt
        keys = {0x5B, 0x43}
        old_latch = set(app._ASYNC_KEY_LATCH)
        try:
            app._ASYNC_KEY_LATCH.clear()
            with mock.patch.object(app, '_windows_key_down', side_effect=lambda code: code in keys), \
                 mock.patch.object(app, 'control_hotkeys_enabled', return_value=True), \
                 mock.patch.object(msvcrt, 'kbhit', return_value=False):
                self.assertEqual(app.PAUSE_TOGGLE, app.read_windows_key_action())
                self.assertIsNone(app.read_windows_key_action())
                keys.clear()
                app.read_windows_key_action()
                keys.update({0x11, 0x12, 0x46})
                self.assertEqual(app.FLOATING_LYRICS_TOGGLE, app.read_windows_key_action())
                self.assertIsNone(app.read_windows_key_action())
            app._ASYNC_KEY_LATCH.clear()
            with mock.patch.object(app, '_windows_key_down', side_effect=lambda code: code in keys), \
                 mock.patch.object(app, 'control_hotkeys_enabled', return_value=False), \
                 mock.patch.object(msvcrt, 'kbhit', return_value=False):
                self.assertIsNone(app.read_windows_key_action())
        finally:
            app._ASYNC_KEY_LATCH.clear()
            app._ASYNC_KEY_LATCH.update(old_latch)

    def test_saved_control_setting_updates_runtime_cache(self):
        original = list(app._CONTROL_HOTKEYS_CACHE)
        try:
            with mock.patch.object(app, 'save_player_setting_value') as saved:
                app.set_control_hotkeys_enabled(False)
                self.assertFalse(app.control_hotkeys_enabled())
                saved.assert_called_once_with('ControlHotkeysEnabled', 0)
        finally:
            app._CONTROL_HOTKEYS_CACHE[:] = original

    def test_server_timestamp_drives_local_lyrics(self):
        state = {'playing': True, 'paused': False, 'lyric_position_seconds': 4.5,
                 'lyric_clock_epoch': 100.0, 'speed': 1.0,
                 'lyric_timeline': [[0.0, 'A'], [5.0, 'B'], [8.0, 'C']]}
        self.assertAlmostEqual(5.0, synchronized_position(state, 100.3, .2))
        self.assertEqual('B', lyric_at(state, 100.3, .2))
        state['paused'] = True
        self.assertEqual('A', lyric_at(state, 101.0, .2))

    def test_machine_defaults_hover_and_web_control(self):
        self.assertTrue(OPTION_DEFAULTS['remote_hotkeys'])
        self.assertFalse(OPTION_DEFAULTS['remote_floating_lyrics'])
        self.assertFalse(OPTION_DEFAULTS['remote_album_art'])
        facts = hover_facts({'metadata': {'Artist': 'Artist', 'Song': 'Song', 'Album': 'Album',
                                          'Year': '2001', 'Genre': 'Jazz'}, 'duration_seconds': 125})
        self.assertEqual({'artist': 'Artist', 'title': 'Song', 'album': 'Album',
                          'year': '2001', 'genre': 'Jazz', 'length': '2:05'}, facts)
        self.assertEqual('2005', hover_facts({'metadata': {'DATE': '2005-09-01'}})['year'])
        self.assertIn('controlHotkeysEnabled', augment('<div class="group section-global-config" id="globalConfigSection"></div></body>'))
        self.assertEqual(1, app.PLAYER_SETTING_DEFAULTS['ControlHotkeysEnabled'])

    def test_v560_hud_state_colors_and_first_lyric_prewarm(self):
        source = inspect.getsource(app.play_audio_file)
        self.assertIn('"255;75;75" if header_stopped', source)
        self.assertIn('"255;235;70" if header_paused', source)
        self.assertIn('header_stopped = action == WEB_STOP', source)
        warmed = app.prewarm_first_lyric_render(
            [(1.0, 2.0, 'Darkness imprisoning me'), (3.0, 4.0, 'All that I see')],
            1, True,
        )
        self.assertEqual(2, warmed)


if __name__ == '__main__': unittest.main()

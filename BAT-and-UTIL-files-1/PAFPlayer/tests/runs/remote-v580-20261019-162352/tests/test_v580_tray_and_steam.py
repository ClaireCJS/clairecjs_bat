"""Behavioral checks for Steam budgeting, inherited art, and detached tray launch."""
import io
import json
from pathlib import Path
import queue
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest import mock

import PAFPlayer as app
import PAFPlayer_steam as steam
import PAFPlayer_remote_tray as remote
import PAFPlayer_tray_options as options
import PAFPlayer_web_workflows as web
from PAFPlayer_remote_overlay import RemoteOverlays


class SteamTests(unittest.TestCase):
    def setUp(self):
        self.saved = {}
        self.app = NS(load_player_settings=lambda: self.saved.copy(),
                      save_player_settings=lambda value: self.saved.update(value))
        self.rows = [{'name': 'steam.exe', 'exe': r'C:\Steam\steam.exe', 'pid': 10}]
        self.apps = {'42': {'name': 'Example Game', 'directory': r'D:\Steam Library\steamapps\common\Example'}}
        self.monitor = steam.Monitor(self.app, processes=lambda: self.rows,
                                     registry=lambda: ([], []), inventory=lambda roots: self.apps)

    def game(self):
        self.rows.append({'name': 'game.exe', 'exe': r'D:\Steam Library\steamapps\common\Example\bin\game.exe', 'pid': 20})
        self.monitor.tick()

    def test_steam_alone_does_not_count_but_any_installed_game_process_does(self):
        self.monitor.tick(); self.assertFalse(self.monitor.running())
        self.game(); self.assertTrue(self.monitor.running())
        self.assertEqual(['Example Game'], self.monitor.status()['games'])
        self.assertEqual(30, self.monitor.visualizer_fps(60))
        self.assertEqual(21, self.monitor.visualizer_fps(42))
        self.assertTrue(self.monitor.block_gallery())

    def test_exiting_game_restores_full_budget(self):
        self.game(); self.rows.pop(); self.monitor.tick()
        self.assertEqual(60, self.monitor.visualizer_fps(60)); self.assertFalse(self.monitor.block_gallery())

    def test_saved_independent_checkbox_changes_apply_immediately(self):
        self.game(); self.monitor.configure({steam.REDUCE: False})
        self.assertEqual(60, self.monitor.visualizer_fps(60)); self.assertTrue(self.monitor.block_gallery())
        self.monitor.configure({steam.REDUCE: True, steam.NO_GALLERY: False})
        self.assertEqual(30, self.monitor.visualizer_fps(60)); self.assertFalse(self.monitor.block_gallery())
        self.assertEqual({steam.REDUCE: 1, steam.NO_GALLERY: 0}, self.saved)
        other = steam.Monitor(self.app, processes=lambda: self.rows, registry=lambda: ([], []), inventory=lambda roots: self.apps)
        other.tick(); self.assertFalse(other.block_gallery()); self.assertEqual(30, other.visualizer_fps(60))

    def test_both_disabled_skip_process_and_disk_work(self):
        self.monitor.configure({key: False for key in steam.DEFAULTS})
        self.monitor.processes = mock.Mock(side_effect=AssertionError('No scan expected'))
        self.monitor.tick(); self.assertFalse(self.monitor.running())
        self.monitor.processes.assert_not_called()

    def test_stale_detection_expires_without_blocking_rendering(self):
        self.game(); self.monitor._state = (time.monotonic() - 9, ('Old game',), '')
        self.assertEqual(60, self.monitor.visualizer_fps(60)); self.assertFalse(self.monitor.block_gallery())

    def test_render_reads_perform_no_registry_process_or_filesystem_work(self):
        self.game()
        self.monitor.processes = mock.Mock(side_effect=AssertionError('render scanned'))
        self.app.load_player_settings = mock.Mock(side_effect=AssertionError('render read settings'))
        for _ in range(1000):
            self.assertEqual(30, self.monitor.visualizer_fps(60)); self.assertTrue(self.monitor.block_gallery())

    def test_path_boundary_case_and_installers(self):
        rows = [{'name': 'game.exe', 'exe': r'd:\steam library\STEAMAPPS\common\Example2\game.exe'}]
        self.assertEqual((), steam.detect_games(rows, self.apps, []))
        rows[0]['exe'] = r'd:\steam library\STEAMAPPS\common\Example\game.exe'
        self.assertEqual(('Example Game',), steam.detect_games(rows, self.apps, []))
        rows[0]['exe'] = r'D:\Steam Library\steamapps\common\Example\_CommonRedist\setup.exe'
        self.assertEqual((), steam.detect_games(rows, self.apps, []))

    def test_registry_flags_need_live_steam_to_avoid_crash_residue(self):
        self.assertEqual((), steam.detect_games([], self.apps, ['42']))
        self.assertEqual(('Example Game',), steam.detect_games(self.rows, self.apps, ['42']))

    def test_invalid_settings_rejected_without_write(self):
        for payload in ({steam.REDUCE: 'false'}, {'Volume': True}, {}, []):
            with self.assertRaises(ValueError): self.monitor.configure(payload)
        self.assertEqual({}, self.saved)

    def test_inventory_caches_for_a_minute(self):
        self.monitor.inventory = mock.Mock(return_value=self.apps)
        self.monitor.tick(); self.monitor.tick()
        self.assertEqual(1, self.monitor.inventory.call_count)

    def test_detection_failure_fails_open_and_thread_stops(self):
        self.monitor.processes = mock.Mock(side_effect=OSError('No access'))
        self.monitor.start()
        for _ in range(100):
            if 'unavailable' in self.monitor.status()['status']: break
            time.sleep(.01)
        self.monitor.close()
        self.assertIn('unavailable', self.monitor.status()['status'])
        self.assertEqual(60, self.monitor.visualizer_fps(60)); self.assertFalse(self.monitor._thread.is_alive())

    def test_library_manifest_with_spaces_and_traversal_rejection(self):
        root = Path(tempfile.mkdtemp()); library = root/'Second Library'; (root/'steamapps').mkdir()
        (library/'steamapps').mkdir(parents=True)
        (root/'steamapps/libraryfolders.vdf').write_text('"path" "'+str(library).replace('\\', '\\\\')+'"', encoding='utf-8')
        (library/'steamapps/appmanifest_42.acf').write_text('"appid" "42" "name" "The Game" "installdir" "The Game"', encoding='utf-8')
        (library/'steamapps/appmanifest_43.acf').write_text('"appid" "43" "installdir" "../escape"', encoding='utf-8')
        found = steam.catalog([str(root)])
        self.assertEqual(['42'], list(found)); self.assertEqual('The Game', found['42']['name'])

    def test_idle_gallery_manual_start_blocked_and_existing_gallery_stopped(self):
        from test_v574_remote_floating import renderer_helpers
        ns = renderer_helpers({'begin_idle_art_routine', 'idle_art_watch'})
        fake = NS(_idle_foreground_seconds=1, _lock=threading.Lock(), _playback_running=True)
        state = {'idle_promoted': True}; ended = mock.Mock(); root = mock.Mock()
        ns.update(self=fake, state=state, root=root, end_idle_art_routine=ended)
        self.game()
        with mock.patch.object(steam, 'get_monitor', return_value=self.monitor):
            ns['begin_idle_art_routine'](manual=True)
            ns['idle_art_watch']()
        ended.assert_called_once_with(); root.after.assert_called_once()


class RemoteOptionsTests(unittest.TestCase):
    def setUp(self):
        self.settings = remote.RemoteTrayAppSettings('test:19333', Path(tempfile.mkdtemp()))
        self.backend = NS(EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE=app.EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE)
        self.settings.install_player_preference_backend(self.backend)

    def test_defaults_inherit_and_artwork_lyric_override_does_not_change_server(self):
        name = app.EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE
        self.settings.set_server_preferences({name: {'type': 4, 'value': 0}})
        self.assertEqual({'inherit': True, 'artwork_lyrics': 'server'}, self.settings.presentation_options())
        self.assertEqual((0, 4), self.backend.paf_registry_query_value(name))
        self.settings.set_presentation_option('artwork_lyrics', 'on')
        self.assertEqual((1, 4), self.backend.paf_registry_query_value(name))
        self.assertEqual(0, self.settings._server_preferences[name]['value'])

    def test_local_appearance_edit_stops_following_but_placement_does_not(self):
        self.backend.paf_registry_set_value('ExternalAlbumArtGeometry', 1, '500x400+10+20')
        self.assertTrue(self.settings.presentation_options()['inherit'])
        self.backend.paf_registry_set_value('ExternalAlbumArtKaraokeColorMode', 4, 3)
        self.assertFalse(self.settings.presentation_options()['inherit'])
        self.settings.set_server_preferences({'ExternalAlbumArtKaraokeColorMode': {'type': 4, 'value': 7}})
        self.assertEqual((3, 4), self.backend.paf_registry_query_value('ExternalAlbumArtKaraokeColorMode'))

    def test_geometry_and_irrelevant_server_changes_do_not_trigger_renderer_reload(self):
        before = self.settings.presentation_key()
        self.backend.paf_registry_set_value('ExternalFloatingLyricsGeometry', 1, '300x100+4+5')
        self.assertEqual(before, self.settings.presentation_key())
        self.settings.set_presentation_option('inherit', False); before = self.settings.presentation_key()
        self.settings.set_server_preferences({'ExternalAlbumArtKaraokeColorMode': {'type': 4, 'value': 7}})
        self.assertEqual(before, self.settings.presentation_key())

    def test_only_portable_preferences_are_accepted(self):
        valid = {'ArtworkLyricSolutionDistanceV494': {'type': 4, 'value': 10},
                 'ExternalAlbumArtKaraokeColorMode': {'type': 4, 'value': 3}}
        incoming = dict(valid, Volume={'type': 4, 'value': 0},
                        ExternalAlbumArtGeometry={'type': 1, 'value': '1x1+0+0'},
                        ExternalAlbumArtLyricsModeV180={'type': 4, 'value': 0},
                        ExternalAlbumArtKaraokeColorPalettes={'type': 1, 'value': 'a'*5000})
        self.assertEqual(valid, options.validated_preferences(incoming))

    def test_canonical_registry_names_translate_back_to_renderer_ids_and_cache(self):
        owner = NS(); snapshot = {'ArtworkPopup\\KaraokeColorMode': {'kind': 'REG_DWORD', 'value': 5}}
        location = app._PAF_REGISTRY_EXACT_LOCATIONS['ExternalAlbumArtKaraokeColorMode']
        snapshot = {'\\'.join(location): {'kind': 'REG_DWORD', 'value': 5}}
        with mock.patch.object(app, '_global_config_registry_value_snapshot', return_value=snapshot) as read, \
             mock.patch.object(app, 'load_external_album_art_karaoke_enabled', return_value=True), \
             mock.patch.object(app, 'load_external_album_art_popup_color_emoji', return_value=False):
            value = options.server_presentation(app, owner)
            self.assertIs(value, options.server_presentation(app, owner))
        read.assert_called_once()
        self.assertEqual(5, value['ExternalAlbumArtKaraokeColorMode']['value'])
        self.assertEqual(1, value[app.EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE]['value'])

    def test_artwork_only_still_receives_clock_and_timed_lyrics(self):
        server = NS(connected=True, owner_identity='owner', clock_offset=0)
        overlays = RemoteOverlays(server, NS(options={}))
        state = {'playing': True, 'lyric_timeline': [[0,'first'],[4,'second']],
                 'lyric_position_seconds': 5, 'lyric_clock_epoch': 100, 'speed': 1,
                 'decensor_artwork_lyrics': True}
        renderer = mock.Mock(); overlays._refresh_lyrics(renderer, state, False, 100, artwork=True)
        renderer.update_lyric.assert_called_once_with('second', 0., emojimax=False,
                                                       decensor_floating=False, decensor_artwork=True)
        renderer.set_playback_running.assert_called_once_with(True)

    def test_reload_before_gui_start_preserves_visibility_and_updates_flags(self):
        window = app.ExternalAlbumArtWindow.__new__(app.ExternalAlbumArtWindow)
        window._lock = threading.RLock(); window._thread = None
        window._ensure_started = mock.Mock(); window._queue_latest_presentation_command = mock.Mock()
        with mock.patch.object(app, 'load_external_album_art_popup_color_emoji', return_value=False), \
             mock.patch.object(app, 'load_external_album_art_popup_emojimax', return_value=True):
            window.reload_remote_presentation()
        self.assertFalse(window._popup_color_emoji_enabled); self.assertTrue(window._popup_emojimax_enabled)
        window._ensure_started.assert_not_called(); window._queue_latest_presentation_command.assert_not_called()

    def test_art_bytes_coalesce_without_opening_remote_paths(self):
        window = app.ExternalAlbumArtWindow.__new__(app.ExternalAlbumArtWindow)
        window._lock = threading.RLock(); window._closed = False; window._generation = 0
        window._pending_presentation_commands = {}; window._commands = queue.Queue()
        window._ensure_started = mock.Mock()
        window.update_remote_artwork([b'old']); window.update_remote_artwork([b'new'])
        self.assertEqual(1, window._commands.qsize()); self.assertIsNone(window._current_audio)
        self.assertEqual(('art-variants',2,None,[b'new']),window._take_pending_presentation_command('art-variants'))

    def test_detached_launch_redirects_all_streams_and_preserves_command(self):
        with mock.patch.object(remote, 'RemoteTrayAppSettings', return_value=self.settings), \
             mock.patch.object(remote.subprocess, 'Popen') as launch:
            launch.return_value.pid = 123
            self.assertEqual(0, remote.launch_background_tray('test:19333'))
            call = launch.call_args
        self.assertEqual(['--tray-only','test:19333','--foreground'], call.args[0][-3:])
        self.assertEqual(remote.subprocess.DEVNULL, call.kwargs['stdin'])
        self.assertEqual(remote.subprocess.STDOUT, call.kwargs['stderr'])
        self.assertTrue(call.kwargs['creationflags'] & remote.subprocess.DETACHED_PROCESS)
        self.assertTrue(call.kwargs['stdout'].closed)
        self.assertEqual(1, len(list((self.settings.path.parent/'logs').glob('*.log'))))


class SteamWebTests(unittest.TestCase):
    def request(self, method, payload=None, *, local=True, token='token'):
        data = json.dumps(payload or {}).encode()
        handler = NS(command=method, headers={'Host':'127.0.0.1:33333','Content-Length':str(len(data)),
                                             'X-PAF-Workflow-Token': token},
                     rfile=io.BytesIO(data), connection=mock.Mock(), _json=mock.Mock(),
                     _client_is_local=lambda:local)
        runtime = NS(app=NS(), token='token', settings={'remote_uploads':True})
        owner = NS(host='127.0.0.1',port=33333,workflows=runtime)
        monitor = mock.Mock(); monitor.status.return_value={'settings': dict(steam.DEFAULTS)}
        monitor.configure.return_value={'settings': dict(steam.DEFAULTS)}
        with mock.patch.object(steam, 'get_monitor', return_value=monitor):
            self.assertTrue(web.handle(handler, owner, '/api/workflows/steam'))
        return handler._json.call_args.args, monitor

    def test_get_and_paired_local_post(self):
        result, monitor = self.request('GET')
        self.assertEqual(200,result[0]); self.assertTrue(result[1]['local']); self.assertEqual('token',result[1]['token'])
        result, monitor = self.request('POST',{steam.REDUCE:False})
        self.assertEqual(200,result[0]); monitor.configure.assert_called_once_with({steam.REDUCE:False})

    def test_remote_and_unpaired_writes_rejected(self):
        for local,token in ((False,'token'),(True,'wrong')):
            result, monitor = self.request('POST',{steam.REDUCE:False},local=local,token=token)
            self.assertNotEqual(200,result[0]); monitor.configure.assert_not_called()

    def test_real_page_contains_both_checked_controls_and_navigation(self):
        page=app._paf_web_html()
        self.assertIn('[\'steamSection\',\'Steam\']',page)
        self.assertIn('id="steamReduce" checked',page); self.assertIn('id="steamGallery" checked',page)
        self.assertIn('/api/workflows/steam',page)

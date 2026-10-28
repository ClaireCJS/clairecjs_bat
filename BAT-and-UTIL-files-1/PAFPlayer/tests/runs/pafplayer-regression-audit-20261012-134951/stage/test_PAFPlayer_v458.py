"""Long-session retention and V458 regression tests; no playback or GUI required."""
import io
import json
from pathlib import Path
import queue
import threading
import unittest
import urllib.request
from unittest import mock

import PAFPlayer as app


def popup():
    window = app.ExternalAlbumArtWindow.__new__(app.ExternalAlbumArtWindow)
    window._lock = threading.RLock()
    window._closed = False
    window._commands = queue.Queue()
    window._pending_presentation_commands = {}
    window._window_title = ""
    window._thread = mock.Mock()
    window._thread.is_alive.return_value = True
    return window


class ArtworkRetention(unittest.TestCase):
    def setUp(self):
        self.patches = [
            mock.patch.object(app, '_ALBUM_ART_BYTES_CACHE', {}),
            mock.patch.object(app, '_ALBUM_ART_SOURCE_CACHE', {}),
            mock.patch.object(app, 'ALBUM_ART_CACHE_MAX_ENTRIES', 3),
            mock.patch.object(app, 'ALBUM_ART_CACHE_MAX_BYTES', 12),
        ]
        for patch in self.patches:
            patch.start()
            self.addCleanup(patch.stop)

    def put(self, key, value=b'art'):
        app._remember_album_art((key, 0, 0), value, 'embedded')

    def test_track_churn_bounds_entries_and_sources(self):
        for index in range(1000):
            self.put(str(index))
        self.assertEqual(len(app._ALBUM_ART_BYTES_CACHE), 3)
        self.assertEqual(set(app._ALBUM_ART_SOURCE_CACHE), set(app._ALBUM_ART_BYTES_CACHE))

    def test_large_covers_obey_byte_budget(self):
        for key in ('a', 'b', 'c'):
            self.put(key, b'1234567')
        self.assertEqual(list(app._ALBUM_ART_BYTES_CACHE), [('c', 0, 0)])

    def test_oversized_cover_does_not_flush_working_set(self):
        self.put('a')
        self.put('huge', b'x' * 13)
        self.assertEqual(list(app._ALBUM_ART_BYTES_CACHE), [('a', 0, 0)])

    def test_negative_lookups_are_bounded(self):
        for index in range(20):
            self.put(str(index), None)
        self.assertEqual(len(app._ALBUM_ART_BYTES_CACHE), 3)

    def test_revised_file_replaces_stale_payload(self):
        self.put('same')
        app._remember_album_art(('same', 2, 4), b'new', 'local-sidecar')
        self.assertEqual(app._ALBUM_ART_BYTES_CACHE, {('same', 2, 4): b'new'})
        self.assertEqual(app._ALBUM_ART_SOURCE_CACHE, {('same', 2, 4): 'local-sidecar'})

    def test_hit_refreshes_lru_and_preserves_sidecar_policy(self):
        path = Path('cached.flac')
        with mock.patch.object(Path, 'stat', side_effect=OSError), mock.patch.object(app, '_materialize_cover_sidecar_from_embedded_art') as sidecar:
            for key in (str(path), 'b', 'c'):
                self.put(key)
            self.assertEqual(app.extract_album_art(path), b'art')
            sidecar.assert_called_once_with(path, b'art')
            self.put('d')
        self.assertIn((str(path), 0, 0), app._ALBUM_ART_BYTES_CACHE)
        self.assertNotIn(('b', 0, 0), app._ALBUM_ART_BYTES_CACHE)

    def test_simultaneous_consumers_keep_caches_consistent(self):
        def churn(prefix):
            for index in range(250):
                self.put(f'{prefix}-{index}')
        threads = [threading.Thread(target=churn, args=(index,)) for index in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertLessEqual(len(app._ALBUM_ART_BYTES_CACHE), 3)
        self.assertEqual(set(app._ALBUM_ART_SOURCE_CACHE), set(app._ALBUM_ART_BYTES_CACHE))


class PopupBacklog(unittest.TestCase):
    def test_slow_gui_retains_latest_title_only(self):
        window = popup()
        for index in range(100000):
            window.update_title(str(index))
        self.assertEqual(window._commands.qsize(), 1)
        self.assertEqual(window._commands.get_nowait(), ('latest-presentation', 'player-title'))
        self.assertEqual(window._take_pending_presentation_command('player-title'), ('player-title', '99999'))
        window.update_title('next')
        self.assertEqual(window._commands.qsize(), 1)

    def test_unchanged_title_does_not_schedule_another_update(self):
        window = popup()
        window.update_title('same')
        window._commands.get_nowait()
        window._take_pending_presentation_command('player-title')
        window.update_title('same')
        self.assertTrue(window._commands.empty())

    def test_latest_art_releases_obsolete_payload_and_keeps_controls(self):
        window = popup()
        for index in range(100):
            window._queue_latest_presentation_command(('art-variants', index, Path(str(index)), [bytes(1000)]))
            if index == 0:
                window._commands.put(('foreground',))
        self.assertEqual(window._commands.qsize(), 2)
        self.assertEqual(window._commands.get_nowait(), ('latest-presentation', 'art-variants'))
        self.assertEqual(window._take_pending_presentation_command('art-variants')[1], 99)
        self.assertEqual(window._commands.get_nowait(), ('foreground',))

    def test_closed_popup_does_not_retain_work(self):
        window = popup()
        window._closed = True
        window.update_title('ignored')
        window._queue_latest_presentation_command(('art-variants', 1, Path('a'), [b'art']))
        self.assertTrue(window._commands.empty())
        self.assertFalse(window._pending_presentation_commands)


class ShortWrites(unittest.TestCase):
    def test_completes_text_and_bytes_without_repeating_prefix(self):
        for payload in ('ab\U0001f600cd', b'abcdef'):
            with self.subTest(payload=payload):
                accepted = []
                def write(part):
                    accepted.append(part[:2])
                    return len(part[:2])
                app._write_console_payload(mock.Mock(write=write), payload)
                self.assertEqual(payload[:0].join(accepted), payload)

    def test_none_returning_adapter_is_written_once(self):
        stream = mock.Mock()
        stream.write.return_value = None
        app._write_console_payload(stream, 'whole')
        stream.write.assert_called_once_with('whole')

    def test_no_progress_raises_instead_of_spinning(self):
        for count in (0, -1, 20, '2'):
            with self.subTest(count=count):
                stream = mock.Mock()
                stream.write.return_value = count
                with self.assertRaises(OSError):
                    app._write_console_payload(stream, 'abc')

    def test_failure_after_prefix_does_not_retry_prefix(self):
        stream = mock.Mock()
        stream.write.side_effect = [2, OSError('closed')]
        with self.assertRaises(OSError):
            app._write_console_payload(stream, 'abcdef')
        self.assertEqual(stream.write.call_args_list, [mock.call('abcdef'), mock.call('cdef')])

    def test_empty_payload_needs_no_write(self):
        stream = mock.Mock()
        app._write_console_payload(stream, '')
        stream.write.assert_not_called()


class ReleaseIdentity(unittest.TestCase):
    def test_legacy_entry_point_executes_canonical_functions(self):
        import play_audio_file as legacy
        self.assertEqual(legacy.PROGRAM_VERSION, app.PROGRAM_VERSION)
        self.assertEqual(Path(legacy.write_console.__code__.co_filename), Path(app.__file__))
        with mock.patch.object(legacy, '_write_console_payload') as write, mock.patch.object(legacy.sys, 'stdout', io.StringIO()):
            legacy.write_console('check')
            self.assertTrue(write.called)


class RuntimeDiagnostics(unittest.TestCase):
    def test_diagnostics_are_available_over_real_local_http(self):
        server = app.PAFWebServer(host='127.0.0.1', port=0)
        with mock.patch.object(app, 'append_pafplayer_trace'):
            server.start()
            try:
                with urllib.request.urlopen(server.url.rstrip('/') + '/api/runtime-diagnostics', timeout=3) as response:
                    report = json.load(response)
                self.assertEqual(report['version'], app.PROGRAM_VERSION)
                self.assertIn('artwork_cache', report)
                self.assertIn('function_caches', report)
            finally:
                server.close()

    def test_snapshot_reports_limits_without_collecting_or_exposing_paths(self):
        with mock.patch.object(app, '_ALBUM_ART_BYTES_CACHE', {('private/song.flac', 0, 0): b'cover'}), mock.patch.object(app.gc, 'collect') as collect:
            report = app.paf_runtime_diagnostics_snapshot()
        self.assertEqual(report['artwork_cache']['bytes'], 5)
        self.assertEqual(report['artwork_cache']['entries'], 1)
        self.assertEqual(report['artwork_cache']['max_bytes'], 64 * 1024 * 1024)
        self.assertNotIn('private/song', json.dumps(report))
        collect.assert_not_called()

    def test_snapshot_reports_popup_backlog(self):
        window = popup()
        window._pending_lyric_command = None
        window.update_title('latest')
        with mock.patch.object(app, '_PAF_POPUP_WINDOWS', {window}):
            report = app.paf_runtime_diagnostics_snapshot()
        self.assertEqual(report['popups'][0]['queued_commands'], 1)
        self.assertEqual(report['popups'][0]['pending_presentation_kinds'], ['player-title'])

    def test_windows_memory_snapshot_is_available(self):
        if app.os.name != 'nt':
            self.skipTest('Windows memory counters')
        report = app.paf_runtime_diagnostics_snapshot()
        self.assertGreater(report['memory']['private_bytes'], 0)
        self.assertGreater(report['memory']['working_set_bytes'], 0)


if __name__ == '__main__':
    unittest.main()

"""V482 regressions; real console and SMTC probes are isolated and silent."""
import ast
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import PAFPlayer as app
import PAFPlayer_windows_media as media


class FixedRows(unittest.TestCase):
    def test_fixed_rows_reassert_no_wrap_after_a_visualizer_frame(self):
        for double in (False, True):
            prefix = app.fixed_console_row_sequence(4, 6, line_rendition=not double)
            self.assertTrue(prefix.startswith('\x1b[?7l'))
            self.assertIn('\x1b[10;1H', prefix)
            self.assertEqual(not double, '\x1b#5' in prefix)

    def test_live_painter_uses_protected_rows_and_shutdown_restores_wrap(self):
        import inspect
        source = inspect.getsource(app.play_audio_file)
        self.assertIn('return fixed_console_row_sequence(origin, row, line_rendition=line_rendition)', source)
        self.assertIn('write_console(move_to(0) + "\\033[?7h\\033[?25h")', source)

    @unittest.skipUnless(os.name == 'nt', 'Windows console required')
    def test_real_console_track_renderer_stays_in_its_viewport(self):
        from probe_v482_track_renderer import TRACK
        if not TRACK.exists():
            self.skipTest('User-provided reproduction track is not available')
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        args = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).with_name('probe_v482_track_renderer.py')), '--native-track']
        result = subprocess.run(args, startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE,
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(0, result.returncode, result.stderr)
        trial = json.loads(result.stdout)
        self.assertEqual(0, trial['max_viewport_top'], trial)
        self.assertEqual(240, trial['frames'], trial)
        print('Private console real-lyric replay:', json.dumps(trial))

    def test_corrupt_embedded_art_is_skipped_for_valid_sidecar(self):
        import io
        from PIL import Image
        image = io.BytesIO()
        Image.new('RGB', (16,16), 'blue').save(image, format='PNG')
        valid = image.getvalue()
        candidate = mock.Mock()
        candidate.read_bytes.return_value = valid
        with mock.patch.object(app, '_folder_uses_per_track_sidecar_art', return_value=True), \
             mock.patch.object(app, '_album_art_candidates', return_value=[candidate]), \
             mock.patch.object(app, '_extract_tagged_embedded_cover_art', return_value=b'\x10JFIF\x00broken'), \
             mock.patch.object(app, 'extract_album_art', return_value=b'\x10JFIF\x00broken'):
            self.assertEqual([valid], app._extract_album_art_variants_uncached(Path('song.mp3')))


class WindowsMedia(unittest.TestCase):
    def options(self, **kw):
        return dict(media.DEFAULTS, **kw)

    def test_title_artist_and_optional_lyric_are_published_without_changing_state(self):
        state = {'metadata': {'Act': 'Dethklok', 'Song': "Murdertrain A Comin' (TV Edit)"},
                 'lyric': 'what I’m talking about'}
        import copy
        before = copy.deepcopy(state)
        normal = media.presentation(state, self.options())
        self.assertNotIn('talking', normal['title'])
        with_lyric = media.presentation(state, self.options(lyrics=True))
        self.assertEqual(normal['title'] + ' | what I’m talking about', with_lyric['title'])
        self.assertEqual('Dethklok', with_lyric['artist'])
        self.assertEqual(before, state)

    def test_shared_timing_handles_speed_pause_offset_seek_and_blank_cues(self):
        state = dict(lyric_timeline=[[0, 'first'], [3, 'second'], [5, '']],
                     lyric_position_seconds=2, lyric_clock_epoch=100, playing=True, paused=False, speed=2)
        self.assertEqual('second', media.current_lyric(state, now=101))
        state['paused'] = True
        self.assertEqual('first', media.current_lyric(state, now=101))
        state['karaoke_offset_seconds'] = 1
        self.assertEqual('second', media.current_lyric(state, now=101))
        state['lyric_position_seconds'] = 4
        self.assertEqual('', media.current_lyric(state, now=101))
        state['lyric_position_seconds'] = 0
        self.assertEqual('first', media.current_lyric(state, now=101))

    def test_new_lyrics_do_not_reencode_artwork_but_track_and_art_changes_do(self):
        state = dict(track={'path':'one'},metadata={'Act':'Artist','Song':'Song'},
                     lyric='first',art_generation=1,art_count=1,duration_seconds=20,position_seconds=1)
        rt = SimpleNamespace(settings={'windows_media':self.options(enabled=True,lyrics=True)},
                             server=SimpleNamespace(snapshot=lambda:state), app=app)
        b = media.Bridge(rt)
        updater = SimpleNamespace(music_properties=SimpleNamespace(), update=mock.Mock())
        controls = SimpleNamespace(display_updater=updater, update_timeline_properties=mock.Mock())
        b.backend = (None, controls, SimpleNamespace(MUSIC=1), SimpleNamespace(PAUSED=1,PLAYING=2,STOPPED=3),
                     SimpleNamespace, None, None, None)
        with mock.patch.object(media, 'artwork_bytes', return_value=None) as artwork:
            b.tick(); state['lyric'] = 'second'; b.tick()
            self.assertEqual(1, artwork.call_count)
            self.assertEqual(2, updater.update.call_count)
            self.assertIn('second', updater.music_properties.title)
            state['art_count'] = 2; b.tick()
            self.assertEqual(2, artwork.call_count)
            state['track'] = {'path':'two'}; b.tick()
            self.assertEqual(3, artwork.call_count)
            rt.settings['windows_media']['enabled'] = False; b.tick()
            self.assertFalse(controls.is_enabled)

    def test_bundled_sources_and_web_checkbox(self):
        for name in ('PAFPlayer_windows_media', 'PAFPlayer_windows_ui'):
            ast.parse(app._PAF_BUNDLED_SOURCES[name])
        self.assertIn('data-windows-setting="lyrics"', app._PAF_BUNDLED_SOURCES['PAFPlayer_windows_ui'])
        self.assertFalse(media.DEFAULTS['lyrics'])


def native_console():
    import msvcrt
    from ctypes import wintypes
    kernel = app._windows_console_text_api()
    class Coord(ctypes.Structure):
        _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]
    class Rect(ctypes.Structure):
        _fields_ = [(name, ctypes.c_short) for name in ('Left','Top','Right','Bottom')]
    class Info(ctypes.Structure):
        _fields_ = [('size', Coord), ('cursor', Coord), ('attributes', wintypes.WORD),
                    ('window', Rect), ('maximum', Coord)]
    kernel.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]
    kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, Coord]
    kernel.SetConsoleCursorPosition.argtypes = [wintypes.HANDLE, Coord]
    kernel.SetConsoleWindowInfo.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(Rect)]
    stream = open('CONOUT$', 'w', encoding='utf-8')
    handle = msvcrt.get_osfhandle(stream.fileno())
    info = Info()
    assert kernel.GetConsoleScreenBufferInfo(handle, ctypes.byref(info))
    width = info.window.Right - info.window.Left + 1
    height = info.window.Bottom - info.window.Top + 1
    assert kernel.SetConsoleScreenBufferSize(handle, Coord(width, max(1000, height * 10)))
    mode = wintypes.DWORD()
    assert kernel.GetConsoleMode(handle, ctypes.byref(mode))
    assert kernel.SetConsoleMode(handle, mode.value | 4)
    rendition = '\x1b#' + sys.argv[sys.argv.index('--native-console') + 1]
    fixed = '--fixed' in sys.argv
    trial = {'rendition': rendition, 'bottom': height-1, 'fixed':fixed}
    assert kernel.SetConsoleCursorPosition(handle, Coord(0, 0))
    # Each case gets its OWN private console. Conhost retains a virtual viewport
    # after scrolling even if SetConsoleWindowInfo pans the visible window back.
    prefix = (app.fixed_console_row_sequence(1, height-1) if fixed
              else '\x1b(B' + app.absolute_viewport_cursor_sequence(1, height-1) + app.BIG_OFF)
    with mock.patch.object(app.sys, 'stdout', stream):
        app.write_console('\x1b[?7h' + prefix + rendition + 'X' * (width * 3))
    assert kernel.GetConsoleScreenBufferInfo(handle, ctypes.byref(info))
    trial['cursor_y'] = info.cursor.Y
    trial['viewport_top'] = info.window.Top
    stream.close()
    print(json.dumps(trial))


async def native_media():
    """Publish a paused/silent test, read it back from Windows, then remove it."""
    import asyncio
    import io
    from PIL import Image
    from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager
    cover = io.BytesIO()
    Image.new('RGB', (16,16), 'blue').save(cover, format='PNG')
    state = dict(track={'title':'PAFPlayer SMTC verification','artist':'PAFPlayer'},
                 lyric='Current lyric verification', paused=True,duration_seconds=60,position_seconds=1)
    rt = SimpleNamespace(settings={'windows_media':dict(media.DEFAULTS, enabled=True,artwork=True,lyrics=True)},
                         server=SimpleNamespace(snapshot=lambda:state,art_snapshot=lambda:(cover.getvalue(),'image/png')),
                         app=app,stop_event=threading.Event())
    bridge = media.Bridge(rt)
    try:
        bridge.start()
        manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        found = False
        for attempt in range(20):
            await asyncio.sleep(0.2)
            for session in manager.get_sessions():
                props = await session.try_get_media_properties_async()
                if 'PAFPlayer SMTC verification' in props.title:
                    assert props.artist == 'PAFPlayer'
                    assert 'Current lyric verification' in props.title
                    assert props.thumbnail is not None
                    found = True
                    print(json.dumps({'verified':True,'title':props.title,'artist':props.artist,'artwork':True}))
                    break
            if found: break
        assert found, ('Windows did not enumerate the published session', bridge.status)
    finally:
        bridge.close()


if __name__ == '__main__':
    if '--native-console' in sys.argv: native_console()
    elif '--native-media' in sys.argv:
        import asyncio
        asyncio.run(native_media())
    else: unittest.main()

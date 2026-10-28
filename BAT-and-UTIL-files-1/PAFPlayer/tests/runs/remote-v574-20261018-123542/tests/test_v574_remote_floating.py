"""Remote presentation transitions and real-font Whip regression checks."""
import ast
import ctypes
import os
from pathlib import Path
import queue
import threading
import types
import unittest
from unittest import mock

import PAFPlayer as app
from PAFPlayer_remote_overlay import RemoteOverlays


class RemotePresentationTests(unittest.TestCase):
    def setUp(self):
        self.server = types.SimpleNamespace(connected=True, owner_identity='owner-a', clock_offset=0.0)
        self.overlay = RemoteOverlays(self.server, types.SimpleNamespace(options={}))
        self.renderer = mock.Mock()
        self.state = {'playing': True, 'paused': False, 'track': {'path': 'song-a.flac'},
                      'metadata': {'Artist': 'Test', 'Song': 'Song'}, 'speed': 1.0,
                      'lyric_clock_epoch': 100.0, 'lyric_position_seconds': 5.0,
                      'lyric_timeline': [[0.0, 'Whip it'], [10.0, 'Next line']],
                      'karaoke_emojimax': True}

    def tick(self, enabled=True, at=100.0):
        self.overlay._refresh_lyrics(self.renderer, self.state, enabled, at)

    def test_repeated_heartbeat_does_not_restart_track_intro(self):
        for index in range(480): self.tick(at=100 + index / 20)
        self.renderer.update_track_identity.assert_called_once_with('Test', 'Song')
        self.renderer.set_floating_lyrics_enabled.assert_called_once_with(True)
        self.assertEqual(self.renderer.set_playback_position.call_count, 480)
        self.renderer.update_lyric.assert_any_call('Whip it', 0.0, emojimax=True, decensor_floating=False)

    def test_real_track_change_with_same_title_and_owner_change_are_not_lost(self):
        self.tick()
        self.state['track']['path'] = 'different-recording.flac'
        self.tick()
        self.server.owner_identity = 'owner-b'
        self.tick()
        self.assertEqual(self.renderer.update_track_identity.call_count, 3)

    def test_metadata_change_only_reintroduces_once(self):
        self.tick()
        self.state['metadata']['Song'] = 'Corrected title'
        for _ in range(20): self.tick()
        self.assertEqual(self.renderer.update_track_identity.call_count, 2)

    def test_slow_tk_cannot_accumulate_toggle_requests(self):
        for _ in range(30): self.tick()
        for _ in range(30): self.tick(False)
        for _ in range(30): self.tick()
        self.assertEqual(self.renderer.set_floating_lyrics_enabled.call_args_list,
                         [mock.call(True), mock.call(False), mock.call(True)])
        self.renderer.toggle_floating_lyrics.assert_not_called()

    def test_disconnect_and_reconnect_keep_a_stable_message(self):
        self.tick()
        self.server.connected = False
        self.state = {}
        for _ in range(20): self.tick()
        self.renderer.update_lyric.assert_called_with('PAFPlayer disconnected', 0.0,
                                                      emojimax=False, decensor_floating=False)
        self.assertEqual(self.renderer.update_track_identity.call_count, 2)
        self.server.connected = True
        self.tick()
        self.assertEqual(self.renderer.update_track_identity.call_count, 3)

    def test_paused_and_stopped_clocks_do_not_animate(self):
        for field in ('paused', 'transport_stopped'):
            self.state['paused'] = False
            self.state['transport_stopped'] = False
            self.state[field] = True
            self.tick()
            self.renderer.set_playback_running.assert_called_with(False)
            self.assertEqual(self.renderer.set_playback_position.call_args.kwargs['speed'], 0.0)


class AbsoluteVisibilityTests(unittest.TestCase):
    def test_restored_enabled_renderer_starts_and_coalesces_absolute_state(self):
        window = app.ExternalAlbumArtWindow.__new__(app.ExternalAlbumArtWindow)
        window._lock = threading.RLock()
        window._closed = False
        window._thread = types.SimpleNamespace(is_alive=lambda: True)
        window._pending_presentation_commands = {}
        window._commands = queue.Queue()
        window._ensure_started = mock.Mock()
        for _ in range(50): window.set_floating_lyrics_enabled(True)
        self.assertEqual(window._commands.qsize(), 1)
        self.assertEqual(window._take_pending_presentation_command('set-floating-lyrics'),
                         ('set-floating-lyrics', True))
        self.assertTrue(window._ensure_started.called)
        window._closed = True
        window.set_floating_lyrics_enabled(False)
        self.assertFalse(window._pending_presentation_commands)

    def test_real_cue_cancels_intro_expiry_even_when_text_matches_title(self):
        # Execute the production cancellation helper with a scheduled timer.
        functions = renderer_helpers({'cancel_floating_track_intro'})
        fake = mock.Mock()
        functions['state'] = {'floating_window': fake, 'floating_intro_after': 'timer-1'}
        functions['cancel_floating_track_intro']()
        functions['cancel_floating_track_intro']()
        fake.after_cancel.assert_called_once_with('timer-1')
        source = Path(app.__file__).read_text(encoding='utf-8')
        self.assertIn('if kind == "lyric":\n                        cancel_floating_track_intro()', source)


def renderer_helpers(names):
    tree = ast.parse(Path(app.__file__).read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ExternalAlbumArtWindow')
    gui = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '_gui_main')
    functions = [node for node in gui.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert {node.name for node in functions} == names
    namespace = dict(vars(app))
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<renderer helpers>', 'exec'), namespace)
    return namespace


@unittest.skipUnless(os.name == 'nt', 'Uses installed Windows font coverage')
class WhipGlyphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PIL import ImageFont
        cls.functions = renderer_helpers({'_pillow_char_is_emojiish', '_pillow_font_codepoints',
            '_pillow_symbol_font', '_pillow_historic_font', '_pillow_font_for_run',
            '_pillow_mixed_font_runs', '_pillow_render_runs'})
        fonts = Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts'
        if not (fonts / 'seguihis.ttf').is_file(): raise unittest.SkipTest('Segoe UI Historic not installed')
        cls.primary = ImageFont.truetype(str(fonts / 'segoeuib.ttf'), 48)
        cls.emoji = ImageFont.truetype(str(fonts / 'seguiemj.ttf'), 48)

    def test_whip_mapping_is_preserved_and_real_historic_glyphs_are_selected(self):
        text, _solutions = app.emojimax_plain_with_solutions('Whip it with a rainbow', True)
        self.assertIn('𓀓𓀝', text)
        runs = list(self.functions['_pillow_render_runs'](text, self.primary, self.emoji))
        self.assertEqual(''.join(run for run, flag in runs), text)
        seen = []
        for run, flag in runs:
            font = self.functions['_pillow_font_for_run'](run, flag, self.primary, self.emoji)
            if any(ch in '𓀓𓀝' for ch in run):
                seen.extend(ch for ch in run if ch in '𓀓𓀝')
                self.assertEqual(Path(font.path).name.casefold(), 'seguihis.ttf')
                coverage = self.functions['_pillow_font_codepoints'](str(font.path))
                self.assertTrue(all(ord(ch) in coverage for ch in run))
                self.assertNotEqual(bytes(font.getmask(run)), bytes(self.primary.getmask(run)))
        self.assertEqual(seen, list('𓀓𓀝'))

    def test_mixed_text_fallback_preserves_text_and_joined_emoji(self):
        text = 'Whip 𓀓𓀝 with 👩‍🎤 and 🇺🇸'
        runs = list(self.functions['_pillow_render_runs'](text, self.primary, self.emoji))
        self.assertEqual(''.join(run for run, flag in runs), text)
        self.assertTrue(any('👩‍🎤' in run for run, flag in runs))
        self.assertTrue(any('🇺🇸' in run for run, flag in runs))


if __name__ == '__main__': unittest.main()

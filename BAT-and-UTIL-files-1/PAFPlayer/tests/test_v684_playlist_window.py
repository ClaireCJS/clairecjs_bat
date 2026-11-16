import ast
import importlib.util
import queue
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('playlist_view_v684', ROOT / 'src' / 'PAFPlayer_playlist_window.py')
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)

class PlaylistViewTests(unittest.TestCase):
    def test_expand_filters_and_preserves_directory_order(self):
        window = view.PlaylistWindow(lambda: ([], None), {'.mp3', '.flac'})
        with mock.patch.object(view.Path, 'is_dir', return_value=True), mock.patch.object(view.os, 'walk', return_value=[('C:/music', ['z', 'a'], ['b.MP3', 'a.flac', 'cover.jpg'])]):
            window._expand(['C:/music'])
        self.assertEqual([('add', str(Path('C:/music/a.flac'))), ('add', str(Path('C:/music/b.MP3')))], [window.events.get_nowait(), window.events.get_nowait()])
        with self.assertRaises(queue.Empty): window.events.get_nowait()

    def test_toggle_never_spawns_duplicate_while_opening(self):
        window = view.PlaylistWindow(lambda: ([], None), {'.mp3'})
        with mock.patch.object(view.threading, 'Thread') as thread, mock.patch.object(view.time, 'monotonic', side_effect=[10, 10, 11, 11]):
            window.toggle(); window.toggle()
        thread.assert_called_once()
        self.assertEqual('close', window.commands.get_nowait())

    def test_repeated_key_debounced(self):
        window = view.PlaylistWindow(lambda: ([], None), {'.mp3'})
        with mock.patch.object(view.threading, 'Thread') as thread, mock.patch.object(view.time, 'monotonic', side_effect=[10, 10, 10.1]):
            window.toggle(); window.toggle()
        thread.assert_called_once()
        self.assertTrue(window.commands.empty())

    def test_single_file_bundle_matches_module(self):
        tree = ast.parse((ROOT / 'PAFPlayer.py').read_text(encoding='utf-8-sig'))
        embedded = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == '_PAF_BUNDLED_SOURCES' and isinstance(t.slice, ast.Constant) and t.slice.value == 'PAFPlayer_playlist_window' for t in node.targets))
        self.assertEqual((ROOT / 'src' / 'PAFPlayer_playlist_window.py').read_text(encoding='utf-8-sig'), embedded)

if __name__ == '__main__': unittest.main()

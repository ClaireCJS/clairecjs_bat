import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V557ScopedSongDialogTests(unittest.TestCase):
    def test_fixed_catalog_cannot_reconcile_outside_playlist(self):
        source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
        start = source.index('class FixedAudioCatalogIndex')
        section = source[start:source.index('def traditional_windows_folder_picker', start)]
        self.assertIn('def _start_query_reconciliation', section)
        self.assertIn('return None', section)

    def test_j_and_qq_choose_different_sources_in_same_picker(self):
        source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
        self.assertIn('picker_catalog = audio_catalog_index', source)
        self.assertIn('picker_catalog = FixedAudioCatalogIndex(', source)
        self.assertIn('add_track_via_insert(False, library_scope=True)', source)
        self.assertIn('library_scope=(action in {PLAYLIST_ADD_SEARCH_Q, PLAYLIST_ADD_PICKER})', source)

    def test_existing_playlist_member_is_queued_before_add_attempt(self):
        source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
        queue_at = source.index("queued = int(playlist_queue_callback([str(selected_path)])")
        add_at = source.index('playlist_add_callback(selected_path)', queue_at)
        self.assertLess(queue_at, add_at)


if __name__ == '__main__':
    unittest.main()

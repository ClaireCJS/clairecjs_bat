import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V556RegressionTests(unittest.TestCase):
    def test_lyric_option_is_a_click_through_tray_bubble(self):
        source = (ROOT / 'src' / 'PAFPlayer_tray.py').read_text(encoding='utf-8')
        hover = (ROOT / 'src' / 'PAFPlayer_tray_hover.py').read_text(encoding='utf-8')
        self.assertIn('Show sung lyrics above tray', source)
        self.assertIn('self._lyric_bubble.show(lyric)', source)
        lyric_path = source[source.index('def _sync_lyric_bubble'):source.index('def _log')]
        self.assertNotIn('NIF_INFO', lyric_path)
        self.assertIn('NIF_INFO', source)  # Error alerts use shell notifications separately.
        self.assertIn('class LyricBubble', hover)
        self.assertIn('Shell_NotifyIconGetRect', hover)
        self.assertIn('0x00000020', hover)  # WS_EX_TRANSPARENT: clicks pass through.

    def test_packed_tray_events_and_full_size_previews(self):
        source = (ROOT / 'src' / 'PAFPlayer_tray.py').read_text(encoding='utf-8')
        self.assertIn('def create_menu_bitmap(style, size=32):', source)
        self.assertIn('event = int(lparam) & 0xFFFF', source)

    def test_cooldown_replacement_updates_visit_history(self):
        source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
        marker = 'current_audio = shuffle_candidate_avoiding_recent('
        start = source.index(marker)
        nearby = source[start:start + 900]
        self.assertIn('playlist_navigation_history[playlist_navigation_cursor] = current_audio', nearby)


if __name__ == '__main__':
    unittest.main()

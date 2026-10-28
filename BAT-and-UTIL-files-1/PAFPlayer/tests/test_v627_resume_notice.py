"""Separate, aligned playlist and song labels on a resumed launch."""

import re
import unittest
from pathlib import Path

import PAFPlayer as app


class ResumeNoticeTests(unittest.TestCase):
    def test_playlist_and_song_filenames_align_and_song_keeps_position(self):
        notice = app.format_playlist_resume_notice(
            Path('C:/mp3/lists/whatever.m3u'),
            Path('C:/music/10_Wasted.flac'), 94.8)
        visible = re.sub(r'\x1b\[[0-9;]*m', '', notice).splitlines()
        self.assertEqual(2, len(visible))
        self.assertTrue(visible[0].startswith(' ↩ Resuming playlist: '))
        self.assertTrue(visible[1].startswith(' ↩ Resuming song:'))
        self.assertEqual(visible[0].index('whatever.m3u'), visible[1].index('10_Wasted.flac'))
        self.assertTrue(visible[1].endswith('10_Wasted.flac at 1:34'))
        self.assertNotIn('10_Wasted.flac', visible[0])

    def test_only_filenames_use_italic_escape(self):
        notice = app.format_playlist_resume_notice(
            Path('C:/lists/a.m3u8'), Path('C:/music/b.mp3'), 0)
        self.assertIn('\x1b[3ma.m3u8\x1b[23m', notice)
        self.assertIn('\x1b[3mb.mp3\x1b[23m at 0:00', notice)
        self.assertEqual(2, notice.count('\x1b[3m'))
        self.assertEqual(2, notice.count('\x1b[23m'))


if __name__ == '__main__':
    unittest.main()

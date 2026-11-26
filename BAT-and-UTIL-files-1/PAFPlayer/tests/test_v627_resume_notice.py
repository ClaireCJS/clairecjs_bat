"""Separate, aligned playlist and song labels on a resumed launch."""

import re
import unittest
from pathlib import Path

import PAFPlayer as app


class ResumeNoticeTests(unittest.TestCase):
    def test_resume_rows_align_with_port_and_time_has_own_row(self):
        label = f'🌐 {app.PROGRAM_TITLE} {app.PROGRAM_VERSION.casefold()} webserver OPEN on port 666'
        heading = app.format_startup_status(label, 'http://127.0.0.1:666/')
        self.assertIn('666: http', heading)
        notice = app.format_playlist_resume_notice(Path('C:/mp3/lists/whatever.m3u'), Path('C:/music/10_Wasted.flac'), 94.8)
        visible = re.sub(r'\x1b\[[0-9;]*m', '', notice).splitlines()
        self.assertEqual(3, len(visible))
        self.assertTrue(visible[0].endswith(': whatever.m3u'))
        self.assertTrue(visible[1].endswith(': 10_Wasted.flac'))
        self.assertTrue(visible[2].lstrip().startswith('↩ Resuming at'))
        self.assertTrue(visible[2].endswith(': 1:34'))
        for line in visible:
            self.assertEqual(app.terminal_cell_width(line.split(':',1)[0]), app.terminal_cell_width(label))

    def test_only_filenames_use_italic_escape(self):
        notice = app.format_playlist_resume_notice(Path('C:/lists/a.m3u8'), Path('C:/music/b.mp3'), 0)
        self.assertIn('\x1b[3ma.m3u8\x1b[23m', notice)
        self.assertIn('\x1b[3mb.mp3\x1b[23m', notice)
        self.assertNotIn('b.mp3\x1b[23m at', notice)
        self.assertEqual(2, notice.count('\x1b[3m'))
        self.assertEqual(2, notice.count('\x1b[23m'))


if __name__ == '__main__':
    unittest.main()

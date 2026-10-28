"""V621 external web queue actions announce accepted work on the HUD."""
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as player


class WebQueueHudTests(unittest.TestCase):
    def test_web_queue_and_clear_report_only_accepted_counts(self):
        server=player.PAFWebServer.__new__(player.PAFWebServer)
        server._lock=threading.RLock()
        note=mock.Mock()
        server.workflows=SimpleNamespace(note_external_activity=note)
        server._playlist_queue_callback=lambda paths: len(paths)
        server._playlist_clear_queue_callback=lambda: 2
        self.assertEqual(2,server.playlist_queue([r'C:\private\one.flac',r'C:\private\two.flac']))
        self.assertEqual(2,server.playlist_clear_queue())
        self.assertEqual([
            mock.call('Enqueued 2 tracks via web or remote control'),
            mock.call('Cleared 2 queued tracks via web or remote control'),
        ],note.call_args_list)
        self.assertNotIn('private',str(note.call_args_list).lower())

    def test_no_callback_or_zero_change_has_no_hud_message(self):
        server=player.PAFWebServer.__new__(player.PAFWebServer)
        server._lock=threading.RLock()
        note=mock.Mock();server.workflows=SimpleNamespace(note_external_activity=note)
        server._playlist_queue_callback=lambda paths: 0
        server._playlist_clear_queue_callback=None
        self.assertEqual(0,server.playlist_queue(['ignored']))
        self.assertEqual(0,server.playlist_clear_queue())
        note.assert_not_called()


if __name__=='__main__': unittest.main()

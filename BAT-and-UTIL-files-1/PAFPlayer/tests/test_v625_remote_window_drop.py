"""Tray-only artwork/lyric drops go to the verified central player."""

import json
from pathlib import Path
import threading
import unittest
from unittest import mock

import PAFPlayer as app
from PAFPlayer_remote_tray import RemoteServer


class RemoteWindowDropTests(unittest.TestCase):
    def test_drop_handler_overrides_local_queue_bridge(self):
        received = []
        ready = threading.Event()
        def handle(paths):
            received.append(paths)
            ready.set()
        with mock.patch.object(app, "windows_dropped_paths", return_value=[Path("D:/music/song.mp3")]), \
             mock.patch.object(app, "queue_dropped_media_targets", side_effect=AssertionError("local queue used")):
            window = app.ExternalAlbumArtWindow(enabled=False, drop_handler=handle)
            window._handle_windows_drop(123)
            self.assertTrue(ready.wait(2))
        self.assertEqual([[Path("D:/music/song.mp3")]], received)

    def test_remote_enqueue_binds_request_to_verified_owner(self):
        server = RemoteServer("musicbox:666")
        server.hello = mock.Mock(return_value=("official-owner-7", {"version": "V625"}))
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok":true,"queued":1}'
        server._opener = mock.Mock()
        server._opener.open.return_value = response
        selectors = [{"kind": "path", "value": "D:/music/song.mp3", "size": 42}]
        with mock.patch("PAFPlayer_remote_tray.parse_enqueue_arguments", return_value=(None, selectors)):
            answer = server.enqueue_dropped_paths([Path("D:/music/song.mp3")])
        self.assertTrue(answer["ok"])
        server.hello.assert_called_once_with(include_timeline=False)
        request = server._opener.open.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/api/remote-enqueue"))
        self.assertEqual({"identity": "official-owner-7", "selectors": selectors}, json.loads(request.data))


if __name__ == "__main__":
    unittest.main()

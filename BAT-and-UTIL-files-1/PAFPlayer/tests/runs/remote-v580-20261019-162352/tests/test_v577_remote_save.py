"""Remote tray Save As must target one verified owner and one track visit."""
import io
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from unittest.mock import patch

import PAFPlayer as player
from PAFPlayer_remote_tray import RemoteServer, RemoteTrayAppSettings


class Response(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.headers = {'Content-Length': str(len(data))}


class Opener:
    def __init__(self, data):
        self.data = data
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request.full_url)
        return Response(self.data)


class RemoteSaveTests(unittest.TestCase):
    def test_current_file_ticket_and_transfer(self):
        with tempfile.TemporaryDirectory() as raw:
            server = RemoteServer('musicserver:666')
            state = {'track': {'path': r'C:\Music\a.flac', 'filename': 'a.flac'},
                     'track_visit': 7}
            server.hello = lambda **_kw: ('official-1', state)
            server._opener = Opener(b'FLAC' * 100)
            ticket = server.current_file_ticket()
            self.assertEqual(('official-1', r'C:\Music\a.flac', 7, 'a.flac'), ticket)
            updates = []
            dest = Path(raw) / 'a.flac'
            self.assertEqual(dest, server.download_current(ticket, dest, progress=lambda a, b: updates.append((a, b))))
            self.assertEqual(b'FLAC' * 100, dest.read_bytes())
            self.assertEqual((400, 400), updates[-1])
            self.assertIn('/api/remote-tray/download?', server._opener.requests[0])
            self.assertRaises(FileExistsError, server.download_current, ticket, dest)

    def test_changed_owner_or_visit_rejects_before_opening_destination(self):
        with tempfile.TemporaryDirectory() as raw:
            server = RemoteServer('musicserver:666')
            state = {'track': {'path': 'a.flac', 'filename': 'a.flac'}, 'track_visit': 3}
            server.hello = lambda **_kw: ('official-2', state)
            server._opener = Opener(b'audio')
            dest = Path(raw) / 'a.flac'
            for ticket in [('official-1', 'a.flac', 3, 'a.flac'),
                           ('official-2', 'a.flac', 2, 'a.flac')]:
                self.assertRaises(ValueError, server.download_current, ticket, dest)
            self.assertFalse(dest.exists())
            self.assertFalse(server._opener.requests)

    def test_destination_history_falls_back_to_existing_folder(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            settings = RemoteTrayAppSettings('musicserver:666', config_root=base / 'settings')
            first, second = base / 'USB', base / 'Downloads'
            first.mkdir()
            second.mkdir()
            settings.remember_download_folder(second)
            settings.remember_download_folder(first)
            self.assertEqual(first, settings.recent_download_folder())
            first.rmdir()
            self.assertEqual(second, settings.recent_download_folder())

    def test_http_download_rejects_wrong_owner_and_track_visit(self):
        with tempfile.TemporaryDirectory() as raw:
            audio = Path(raw) / 'playing.flac'
            audio.write_bytes(b'FLAC-audio')
            web = player.PAFWebServer(host='127.0.0.1', port=0)
            original_instance = getattr(web.workflows, 'instance', None)
            web.workflows.instance = SimpleNamespace(identity='official-1', owns=lambda: True)
            with web._lock:
                web._current_audio = audio
                web._track_visit = 11
                web._state['track'] = {'path': str(audio), 'filename': audio.name}
                web._state['track_visit'] = 11
            try:
                self.assertTrue(web.start())
                client = RemoteServer(f'127.0.0.1:{web.port}')
                ticket = client.current_file_ticket()
                saved = Path(raw) / 'copy.flac'
                client.download_current(ticket, saved)
                self.assertEqual(audio.read_bytes(), saved.read_bytes())
                for identity, visit in [('other-owner', 11), ('official-1', 10)]:
                    query = urlencode({'identity': identity, 'path': str(audio), 'visit': visit})
                    with self.assertRaises(HTTPError) as error:
                        urlopen(web.url.rstrip('/') + '/api/remote-tray/download?' + query)
                    self.assertEqual(409, error.exception.code)
            finally:
                web.close()
                web.workflows.instance = original_instance


if __name__ == '__main__':
    unittest.main()

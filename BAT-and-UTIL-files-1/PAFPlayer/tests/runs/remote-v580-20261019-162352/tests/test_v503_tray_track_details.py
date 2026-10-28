"""Regression checks for V503 local and household tray tag viewers."""

import http.client
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

import PAFPlayer as app
from PAFPlayer_tray import TrayController
import PAFPlayer_track_details as details
import PAFPlayer_remote_tray as remote


class FakeOwner:
    def __init__(self, audio):
        self.audio = audio
        self.state = {"track": {"path": str(audio)}, "duration_seconds": 42.5,
                      "art_count": 2, "art_generation": 8}

    def current_audio(self):
        return self.audio

    def snapshot(self):
        return self.state


class TrackDetailsTests(unittest.TestCase):
    def test_snapshot_contains_tags_complete_lyrics_artwork_and_technical_data(self):
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "song.wav"
            audio.write_bytes(b"RIFF sample")
            owner = FakeOwner(audio)
            payload = {"format": {"format_name": "wav"},
                       "streams": [{"codec_name": "pcm_s16le", "sample_rate": "44100"}],
                       "chapters": [{"start_time": "0.0", "end_time": "42.5"}]}
            probe = types.SimpleNamespace(returncode=0, stdout=json.dumps(payload))
            with mock.patch.object(app, "load_lyrics", return_value=[(1.0, 3.0, "first\nline"), (4.0, None, "second")]), \
                 mock.patch.object(app, "_find_timed_lyric_sidecar", return_value=None), \
                 mock.patch.object(app, "complete_audio_tag_rows", return_value=[("ID3", "Composer", "Someone")]), \
                 mock.patch.object(app, "ffprobe_executable", return_value=Path("ffprobe")), \
                 mock.patch.object(details.subprocess, "run", return_value=probe) as run:
                result = details.snapshot(owner, app)
            self.assertTrue(result["available"])
            self.assertEqual(audio.name, result["file"]["name"])
            self.assertEqual(str(audio), result["file"]["path"])
            self.assertEqual([("ID3", "Composer", "Someone")], result["tags"])
            self.assertEqual("first\nline", result["lyrics"][0]["text"])
            self.assertEqual(2, result["art_count"])
            self.assertEqual(8, result["art_generation"])
            self.assertEqual(payload, result["technical"])
            self.assertIn("-show_chapters", run.call_args.args[0])

    def test_missing_track_and_unavailable_ffprobe_are_reported(self):
        owner = FakeOwner(None)
        owner.current_audio = lambda: None
        self.assertFalse(details.snapshot(owner, app)["available"])
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "song.wav"
            audio.write_bytes(b"RIFF sample")
            owner = FakeOwner(audio)
            with mock.patch.object(app, "load_lyrics", return_value=[]), \
                 mock.patch.object(app, "_find_timed_lyric_sidecar", return_value=None), \
                 mock.patch.object(app, "complete_audio_tag_rows", return_value=[]), \
                 mock.patch.object(app, "ffprobe_executable", return_value=None):
                result = details.snapshot(owner, app)
            self.assertTrue(result["available"])
            self.assertIn("unavailable", result["technical_error"])

    def test_read_only_data_routes_are_available_to_household_clients(self):
        responses = []
        handler = types.SimpleNamespace(
            path="/api/track-details", _client_is_local=lambda: False,
            _json=lambda status, data: responses.append((status, data)),
            _send=lambda status, data, mime: responses.append((status, data)),
        )
        with mock.patch.object(details, "snapshot", return_value={"available": False}):
            self.assertTrue(details.handle(handler, None, "/api/track-details", app))
        self.assertEqual((200, {"available": False}), responses[-1])
        self.assertFalse(details.handle(handler, None, "/track-details", app))
        self.assertFalse(details.handle(handler, None, "/api/status", app))

    def test_artwork_generation_blocks_stale_or_wrong_track_images(self):
        server = app.PAFWebServer(enabled=False)
        with server._lock:
            server._state["art_generation"] = 9
            server._state["art_count"] = 1
            server._art_variants = [b"image"]
            server._art_variant_mimes = ["image/png"]
        self.assertEqual((b"image", "image/png"), server.art_snapshot_at_generation(9, 0))
        self.assertIsNone(server.art_snapshot_at_generation(8, 0)[0])
        self.assertIsNone(server.art_snapshot_at_generation(9, 1)[0])
        with server._lock:
            server._state["art_count"] = 0
        self.assertIsNone(server.art_snapshot_at_generation(9, 0)[0])

    def test_official_tray_launches_native_viewer_only_from_owner(self):
        server = types.SimpleNamespace(enabled=True, _httpd=object(), url="http://127.0.0.1:666/",
                                       current_audio=lambda: None)
        runtime = types.SimpleNamespace(server=server, app=types.SimpleNamespace(load_player_settings=lambda: {}))
        owner = types.SimpleNamespace(owns=lambda: True)
        other = types.SimpleNamespace(owns=lambda: False)
        with mock.patch.object(remote, "launch_viewer") as opened:
            self.assertTrue(TrayController(runtime, owner).dispatch("details"))
            self.assertFalse(TrayController(runtime, other).dispatch("details"))
        opened.assert_called_once_with("http://127.0.0.1:666/")
        self.assertIn("Open tag viewer", [item[1] for item in TrayController(runtime, owner).menu_items({})])

    def test_remote_client_verifies_server_and_routes_commands_to_it(self):
        server = app.PAFWebServer(host="127.0.0.1", port=0)
        current_owner = types.SimpleNamespace(identity="official-first", owns=lambda: True)
        server.workflows = types.SimpleNamespace(instance=current_owner)
        self.assertTrue(server.start())
        try:
            client = remote.RemoteServer("127.0.0.1:" + str(server.port))
            self.assertTrue(client.poll_once())
            self.assertTrue(client.connected)
            self.assertEqual("official-first", client.owner_identity)
            self.assertTrue(client.command("next"))
            self.assertEqual(app.NEXT_FILE, server.pop_action())
            self.assertTrue(client.command("previous"))
            self.assertEqual(app.PREVIOUS_FILE, server.pop_action())
            self.assertTrue(client.command("pause"))
            self.assertEqual(app.PAUSE_TOGGLE, server.pop_action())
            current_owner.owns = lambda: False
            self.assertFalse(client.command("next"))
            self.assertIsNone(server.pop_action())
            self.assertFalse(client.connected)
            current_owner.owns = lambda: True
            current_owner.identity = "official-successor"
            self.assertTrue(client.poll_once())
            self.assertEqual("official-successor", client.owner_identity)
            self.assertTrue(client.command("next"))
            self.assertEqual(app.NEXT_FILE, server.pop_action())
            connection = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
            connection.request("GET", "/api/track-details")
            response = connection.getresponse()
            data = json.loads(response.read())
            self.assertEqual(200, response.status)
            self.assertFalse(data["available"])
            connection.close()
            client.close()
        finally:
            server.close()

    def test_server_address_and_non_pafplayer_heartbeat(self):
        self.assertEqual(("http://machineservername:666/", "machineservername:666"),
                         remote.server_address("machineservername:666"))
        for invalid in ("", "http://user:pass@host:666", "https://host:666", "host:0"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                remote.server_address(invalid)
        client = remote.RemoteServer("localhost:666")
        with mock.patch.object(client, "json", return_value={"program": "other", "version": "V1"}):
            self.assertFalse(client.poll_once())
        self.assertFalse(client.connected)
        self.assertFalse(client.command("next"))

    def test_tray_only_cli_bypasses_official_instance_and_viewer_has_native_tabs(self):
        with mock.patch.object(remote, "run_tray_only", return_value=17) as run, \
             mock.patch.object(app, "paf_workflows", side_effect=AssertionError("official startup ran")):
            self.assertEqual(17, app.main(["--tray-only", "machineservername:666"]))
        run.assert_called_once_with(["machineservername:666"])
        source = Path(remote.__file__.split('::')[0]).read_text(encoding='utf-8') if '::' not in remote.__file__ else app._PAF_BUNDLED_SOURCES['PAFPlayer_remote_tray']
        self.assertIn("ttk.Notebook(root)", source)
        self.assertIn("('Overview', 'Tags', 'Lyrics', 'Artwork', 'Technical')", source)
        self.assertIn("'--tag-viewer'", source)

    @unittest.skipUnless(os.name == 'nt', 'Windows named-mutex behavior')
    def test_one_remote_tray_per_target_and_stale_mutex_recovers(self):
        label = 'paf-test-' + next(tempfile._get_candidate_names()) + ':666'
        first = remote._remote_mutex(label)
        self.assertIsNotNone(first)
        try:
            self.assertIsNone(remote._remote_mutex(label))
        finally:
            ctypes = remote.ctypes
            ctypes.windll.kernel32.ReleaseMutex(first)
            ctypes.windll.kernel32.CloseHandle(first)
        again = remote._remote_mutex(label)
        self.assertIsNotNone(again)
        ctypes.windll.kernel32.ReleaseMutex(again)
        ctypes.windll.kernel32.CloseHandle(again)


if __name__ == "__main__":
    unittest.main()

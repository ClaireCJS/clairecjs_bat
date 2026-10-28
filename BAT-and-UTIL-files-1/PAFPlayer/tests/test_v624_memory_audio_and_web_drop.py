"""RAM-backed decoder input and local browser-drop authorization."""

import urllib.error
import urllib.request
import unittest
from unittest import mock
from pathlib import Path

import PAFPlayer as app
from PAFPlayer_memory_audio import MemoryAudioSource
from PAFPlayer_web_workflows import receive_upload


class MemoryAudioTests(unittest.TestCase):
    def test_seekable_loopback_source_serves_exact_bytes(self):
        payload = bytes(range(256)) * 4
        source = MemoryAudioSource(payload, ".flac")
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(source.url, timeout=3) as response:
                self.assertEqual(payload, response.read())
                self.assertEqual("bytes", response.headers["Accept-Ranges"])
            with opener.open(urllib.request.Request(source.url, headers={"Range": "bytes=17-31"}), timeout=3) as response:
                self.assertEqual(206, response.status)
                self.assertEqual(payload[17:32], response.read())
                self.assertEqual("bytes 17-31/1024", response.headers["Content-Range"])
            with opener.open(urllib.request.Request(source.url, headers={"Range": "bytes=-4"}), timeout=3) as response:
                self.assertEqual(payload[-4:], response.read())
            with self.assertRaises(urllib.error.HTTPError) as caught:
                opener.open(urllib.request.Request(source.url, headers={"Range": "bytes=1024-"}), timeout=3)
            self.assertEqual(416, caught.exception.code)
        finally:
            source.close()

    def test_decoder_command_uses_ram_url_while_probing_original_file(self):
        from pathlib import Path
        audio = Path("C:/music/song.flac")
        url = "http://127.0.0.1:12345/track.flac"
        with mock.patch.object(app, "probe_audio_stream_layout", return_value=(2, "stereo")):
            ffplay = app.ffplay_command(Path("ffplay.exe"), audio, 12.0, 100, input_url=url)
            ffmpeg = app.matrixmixer_inspired_ffmpeg_command(
                Path("ffmpeg.exe"), audio, 12.0, 100, 1.0, 2, 0,
                input_url=url,
            )
        self.assertEqual(url, ffplay[-1])
        self.assertEqual(url, ffmpeg[ffmpeg.index("-i") + 1])
        self.assertNotIn(str(audio), ffplay)
        self.assertNotIn(str(audio), ffmpeg)


class BrowserDropTests(unittest.TestCase):
    def test_local_drop_does_not_require_remote_upload_setting(self):
        handler = mock.Mock()
        handler._client_is_local.return_value = True
        runtime = mock.Mock()
        runtime.settings = {"remote_uploads": False}
        runtime.app.AUDIO_EXTENSIONS = {".mp3"}
        with mock.patch("PAFPlayer_web_workflows.safe_filename", side_effect=ValueError("checked local file")):
            with self.assertRaisesRegex(ValueError, "checked local file"):
                receive_upload(handler, runtime)
        handler._client_is_local.return_value = False
        with self.assertRaisesRegex(PermissionError, "Remote uploads are disabled"):
            receive_upload(handler, runtime)

    def test_native_window_drop_uses_owner_queue_bridge(self):
        runtime = mock.Mock()
        runtime.queue_bridge = mock.Mock()
        with mock.patch("PAFPlayer_instance.resolve_request", return_value={
                "paths": ["C:/music/a.mp3", "C:/music/b.mp3"]}), \
             mock.patch("PAFPlayer_web_workflows.queue_snapshot", return_value={"revision": "r1"}), \
             mock.patch("PAFPlayer_web_workflows.edit_queue") as edit:
            self.assertEqual(2, app.queue_dropped_media_targets([Path("C:/music")], runtime=runtime))
        edit.assert_called_once_with(runtime, {
            "op": "add", "paths": ["C:/music/a.mp3", "C:/music/b.mp3"], "revision": "r1",
        }, source="Windows file drop")

    def test_native_drop_without_playlist_changes_nothing(self):
        runtime = mock.Mock(queue_bridge=None)
        with self.assertRaisesRegex(ValueError, "Open a playlist"):
            app.queue_dropped_media_targets([Path("C:/music/song.mp3")], runtime=runtime)


if __name__ == "__main__":
    unittest.main()

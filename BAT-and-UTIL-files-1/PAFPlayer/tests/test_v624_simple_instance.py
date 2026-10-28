"""A simple launch plays locally without contacting or claiming the official player."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as app
from PAFPlayer_workflows import Runtime


class StopBeforeAudio(BaseException):
    pass


class FakeInstance:
    created = []

    def __init__(self, runtime):
        self.runtime = runtime
        self.created.append(self)

    def acquire(self):
        raise AssertionError("simple playback must not claim official ownership")

    def forward(self, request):
        raise AssertionError("simple playback must not hand off its track")

    def start(self):
        raise AssertionError("simple playback must not publish an IPC listener")

    def owns(self):
        return False

    def watch_for_claim(self, callback):
        raise AssertionError("simple playback must not become the official owner")

    def close(self):
        pass


class FakeTray:
    def __init__(self, *args, **kwargs):
        pass

    def attach_machine_options(self):
        raise AssertionError("simple playback must not attach tray options")

    def start(self):
        raise AssertionError("simple playback must not create a tray icon")

    def close(self):
        pass


class FakeWebServer:
    def __init__(self, *, enabled, host, port):
        self.enabled = enabled
        self._httpd = None
        self.port = port

    def start(self):
        if self.enabled:
            raise AssertionError("simple playback should default to no web listener")
        return False

    def enqueue_instance_seek(self, *args):
        raise AssertionError("simple playback must not forward seeks")

    def close(self, **kwargs):
        pass


class SimpleInstanceTests(unittest.TestCase):
    def test_simple_file_bypasses_official_handoff_even_when_owner_exists(self):
        track = Path.cwd() / "Rudy Vallee & His Connecticut Yankees - Life Is Just A Bowl Of Cherries (1931 version) (1931) {{{{{TODO DUPECHECK}}}}}.mp3"
        runtime = Runtime(app, root=Path.cwd() / "tests" / "runs" / "v624-simple-fixture")
        runtime.activate = mock.Mock(side_effect=AssertionError("simple playback must not start official integrations"))
        FakeInstance.created.clear()
        seen_targets = []

        def resolve(_runtime, targets):
            seen_targets.extend(targets)
            return {"paths": [str(track)], "playlist": None}

        with (
                mock.patch.object(app, "paf_workflows", return_value=runtime),
                mock.patch("PAFPlayer_cli_workflows.dispatch", side_effect=lambda _runtime, args: (None, args)),
                mock.patch("PAFPlayer_monkeymote.parse_options", side_effect=lambda args: (args, {})),
                mock.patch("PAFPlayer_instance.Instance", FakeInstance),
                mock.patch("PAFPlayer_instance.resolve_request", side_effect=resolve),
                mock.patch("PAFPlayer_tray.TrayController", FakeTray),
                mock.patch.object(app, "PAFWebServer", FakeWebServer),
                mock.patch.object(app, "ExternalAlbumArtWindow", side_effect=StopBeforeAudio),
                mock.patch.object(app, "ensure_standard_music_collection_aliases", return_value=True),
                mock.patch.object(app, "ensure_clairecjs_dependency"),
                mock.patch.object(app, "load_mp3_base_attribute_rules"),
                mock.patch.object(app, "load_player_settings", return_value=dict(app.PLAYER_SETTING_DEFAULTS)),
                mock.patch.object(app, "start_pafplayer_diagnostic_session"),
                mock.patch.object(app, "maybe_prompt_for_lastfm_setup", side_effect=AssertionError("simple playback should not prompt for Last.fm")),
                contextlib.redirect_stdout(io.StringIO()) as output,
        ):
            with self.assertRaises(StopBeforeAudio):
                app.main(["--simple", str(track)])
        self.assertEqual([str(track)], seen_targets)
        self.assertEqual(1, len(FakeInstance.created))
        self.assertEqual([], [line for line in output.getvalue().splitlines() if "Queued next" in line])
        runtime.activate.assert_not_called()

    def test_simple_alias_and_timestamp_remain_local(self):
        with mock.patch.object(app, "ensure_standard_music_collection_aliases", return_value=True), mock.patch.object(app, "ensure_clairecjs_dependency"), mock.patch.object(app, "load_mp3_base_attribute_rules"), mock.patch.object(app, "load_player_settings", return_value=dict(app.PLAYER_SETTING_DEFAULTS)), mock.patch.object(app, "start_pafplayer_diagnostic_session"), contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(2, app.main(["--light", "60s"]))
        self.assertIn("standalone timestamp controls only", error.getvalue().lower())


if __name__ == "__main__":
    unittest.main()

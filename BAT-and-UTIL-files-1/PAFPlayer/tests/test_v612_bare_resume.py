"""V612 read-only bare-resume lookup and CLI regressions."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import PAFPlayer as app


@unittest.skipUnless(os.name == "nt", "Windows registry resume behavior")
class BareResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.track = root / "song.flac"
        self.track.write_bytes(b"fixture")
        self.playlist = root / "list.m3u"
        self.playlist.write_text("song.flac\n", encoding="utf-8")

    def payload(self, **overrides):
        data = {"playlist": str(self.playlist), "track": str(self.track), "position": 32.5}
        data.update(overrides)
        return json.dumps(data)

    def test_checkpoint_records_playlist_in_existing_global_value(self):
        with mock.patch.object(app, "paf_registry_set_value") as write:
            app.save_playlist_resume(self.playlist, self.track, 32.5, next_track=self.track)
        self.assertEqual(2, write.call_count)
        name, _kind, raw = write.call_args.args
        self.assertEqual(app.LAST_PLAYLIST_RESUME_VALUE, name)
        self.assertEqual(str(self.playlist.absolute()), json.loads(raw)["playlist"])
        self.assertEqual(str(self.track.absolute()), json.loads(raw)["track"])

    def test_lookup_is_read_only_and_accepts_valid_playlist(self):
        with mock.patch.object(app, "paf_registry_query_value_read_only", return_value=(self.payload(), 1)) as read, mock.patch.object(app, "paf_registry_set_value") as write:
            self.assertEqual(self.playlist.resolve(), app.load_last_resumable_playlist())
        read.assert_called_once_with(app.LAST_PLAYLIST_RESUME_VALUE)
        write.assert_not_called()

    def test_legacy_malformed_and_missing_playlists_are_not_advertised(self):
        cases = (
            json.dumps({"track": str(self.track), "position": 1}),
            "not json",
            self.payload(playlist=str(self.playlist.with_name("missing.m3u"))),
            self.payload(position="bad"),
        )
        for raw in cases:
            with self.subTest(raw=raw), mock.patch.object(app, "paf_registry_query_value_read_only", return_value=(raw, 1)):
                self.assertIsNone(app.load_last_resumable_playlist())
        self.playlist.write_text("", encoding="utf-8")
        with mock.patch.object(app, "paf_registry_query_value_read_only", return_value=(self.payload(), 1)):
            self.assertIsNone(app.load_last_resumable_playlist())

    def test_resume_without_checkpoint_exits_before_playback(self):
        stderr = io.StringIO()
        with mock.patch.object(app, "load_last_resumable_playlist", return_value=None), mock.patch.object(app, "start_pafplayer_diagnostic_session"), mock.patch.object(app, "ensure_standard_music_collection_aliases") as collection, contextlib.redirect_stderr(stderr):
            self.assertEqual(2, app.main(["resume"]))
        self.assertIn("no usable saved playlist session", stderr.getvalue())
        collection.assert_not_called()

    def test_resume_reaches_normal_playlist_startup_with_saved_path(self):
        class StopAfterParsing(Exception):
            pass

        seen = []

        def capture(arguments):
            seen.extend(arguments)
            raise StopAfterParsing

        with mock.patch.object(app, "load_last_resumable_playlist", return_value=self.playlist), mock.patch.object(app, "start_pafplayer_diagnostic_session"), mock.patch.object(app, "ensure_standard_music_collection_aliases", return_value=True), mock.patch.object(app, "load_player_settings", return_value=dict(app.PLAYER_SETTING_DEFAULTS)), mock.patch.object(app, "command_line_player_setting_override_keys", side_effect=capture):
            with self.assertRaises(StopAfterParsing):
                app.main(["resume"])
        self.assertEqual([str(self.playlist)], seen)

    def test_bare_help_footer_only_when_resumable(self):
        for saved, expected in ((self.playlist, True), (None, False)):
            output = io.StringIO()
            with mock.patch.object(app, "load_last_resumable_playlist", return_value=saved), mock.patch.object(app, "start_pafplayer_diagnostic_session"), contextlib.redirect_stdout(output):
                self.assertEqual(0, app.main([]))
            text = output.getvalue()
            hint = "PAFPlayer resume - resumes previous pafplayer session"
            self.assertEqual(2 if expected else 0, text.count(hint))
            if expected:
                self.assertIn("\033#3\033[5;1;93m" + hint, text)
                self.assertIn("\033#4\033[5;1;93m" + hint, text)
                self.assertTrue(text.endswith(app.BIG_OFF))


if __name__ == "__main__":
    unittest.main()

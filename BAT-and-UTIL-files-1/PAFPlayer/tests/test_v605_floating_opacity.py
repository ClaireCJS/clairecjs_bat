"""Floating Lyrics whole-window opacity: CLI, persistence, web and UI routing."""

import unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace

import PAFPlayer as app


class FloatingOpacityTests(unittest.TestCase):
    def tearDown(self):
        app._floating_lyrics_opacity_session_override = None

    def test_cli_session_and_default_are_separate(self):
        rest, session, default = app.parse_floating_lyrics_opacity_options([
            "--floating-lyrics-opacity=45", "song.flac",
            "--default-floating-lyrics-opacity", "75",
        ])
        self.assertEqual(rest, ["song.flac"])
        self.assertEqual((session, default), (45, 75))
        with mock.patch.object(app, "load_external_floating_lyrics_opacity", return_value=75):
            self.assertEqual(app.effective_floating_lyrics_opacity(), 75)
            app._floating_lyrics_opacity_session_override = session
            self.assertEqual(app.effective_floating_lyrics_opacity(), 45)

    def test_cli_rejects_bad_values_without_saving(self):
        for args in (["--floating-lyrics-opacity"],
                     ["--floating-lyrics-opacity=0"],
                     ["--default-floating-lyrics-opacity=101"],
                     ["--floating-lyrics-opacity=45.5"],
                     ["--default-floating-lyrics-opacity", "--tray"]):
            with self.subTest(args=args), self.assertRaises(ValueError):
                app.parse_floating_lyrics_opacity_options(args)

    def test_saved_setting_defaults_to_full_opacity_and_uses_global_registry(self):
        with mock.patch.object(app, "paf_registry_query_value", side_effect=OSError):
            self.assertEqual(app.load_external_floating_lyrics_opacity(), 100)
        with mock.patch.object(app, "paf_registry_query_value", return_value=(62, 4)):
            self.assertEqual(app.load_external_floating_lyrics_opacity(), 62)
        with mock.patch.object(app, "paf_registry_set_value") as save:
            app.save_external_floating_lyrics_opacity(62)
            save.assert_called_once_with(app.EXTERNAL_FLOATING_LYRICS_OPACITY_VALUE,
                                         app.winreg.REG_DWORD if hasattr(app, "winreg") else 4, 62)

    def test_web_slider_and_whitelist(self):
        html = app._paf_web_html()
        self.assertIn('id="floatingLyricsOpacity"', html)
        self.assertIn('id="floatingLyricsOpacityValue"', html)
        self.assertIn("web-set:floating_opacity:", html)
        self.assertTrue(app.paf_web_action_is_allowed("web-set:floating_opacity:10"))
        self.assertTrue(app.paf_web_action_is_allowed("web-set:floating_opacity:100"))
        self.assertFalse(app.paf_web_action_is_allowed("web-set:floating_opacity:9"))
        self.assertFalse(app.paf_web_action_is_allowed("web-set:floating_opacity:101"))
        self.assertIn("floating_opacity", app.PAFWebServer(enabled=False)._state)

    def test_owner_routes_opacity_to_existing_renderer_queue(self):
        owner = object.__new__(app.ExternalAlbumArtWindow)
        import queue
        owner._commands = queue.Queue()
        with mock.patch.object(app, "save_external_floating_lyrics_opacity") as save, \
             mock.patch.object(owner, "_ensure_started") as start:
            self.assertEqual(owner.set_floating_opacity(43), 43)
        save.assert_called_once_with(43)
        start.assert_called_once()
        self.assertEqual(owner._commands.get_nowait(), ("set-floating-opacity", 43))
        with mock.patch.object(app, "save_external_floating_lyrics_opacity") as save, \
             mock.patch.object(owner, "_ensure_started"):
            owner.set_floating_opacity(37, persist=False)
        save.assert_not_called()
        self.assertEqual(owner._commands.get_nowait(), ("set-floating-opacity", 37))

    def test_session_handoff_targets_the_official_owner_without_saving(self):
        import PAFPlayer_instance as single
        received = []
        runtime = SimpleNamespace(root=Path('.'), opacity_bridge=lambda value: received.append(value) or True)
        owner = single.Instance(runtime)
        descriptor = {}
        try:
            with mock.patch.object(single, 'write_json', side_effect=lambda _path, data: descriptor.update(data)), \
                 mock.patch.object(single, 'read_json', return_value=descriptor):
                owner.start()
                result = owner.forward({'floating_opacity': 37})
                self.assertTrue(result['ok'])
                self.assertEqual(result['queued'], 0)
                self.assertEqual(received, [37])
                for bad in (0, 101, True, '37'):
                    with self.subTest(value=bad), self.assertRaises(ValueError):
                        owner.forward({'floating_opacity': bad})
                self.assertEqual(received, [37])
        finally:
            owner.close()

    def test_default_only_command_saves_and_exits_without_starting_player(self):
        with mock.patch.object(app, 'save_external_floating_lyrics_opacity') as save, \
             mock.patch.object(app, 'paf_workflows', side_effect=AssertionError('player started')):
            self.assertEqual(app.main(['--default-floating-lyrics-opacity=68']), 0)
        save.assert_called_once_with(68)


if __name__ == "__main__":
    unittest.main()

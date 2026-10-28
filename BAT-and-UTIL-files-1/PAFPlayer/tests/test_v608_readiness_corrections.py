"""V608 readiness checks must describe the candidate and its actual needs."""

from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as app


class ReadinessCorrectionsTests(unittest.TestCase):
    def test_bundled_features_are_counted_in_the_checked_file(self):
        checks = app.paf_readiness_checks(Path(__file__))
        self.assertEqual((False, True), next(
            (okay, required) for name, okay, required, _detail in checks
            if name == "Bundled player features"))
        self.assertTrue(next(
            okay for name, okay, _required, _detail
            in app.paf_readiness_checks(Path(app.__file__))
            if name == "Bundled player features"))

    def test_ffplay_is_required_for_playback_but_not_remote_tray(self):
        def ffmpeg_path(name):
            return None if name == "ffplay" else "fixture.exe"

        with mock.patch.object(app, "paf_ffmpeg_tool_path", side_effect=ffmpeg_path):
            player = app.paf_readiness_checks()
            tray = app.paf_readiness_checks(tray_only=True)
        self.assertEqual((False, True), next(
            (okay, required) for name, okay, required, _detail in player
            if name == "FFPLAY"))
        self.assertEqual((False, False), next(
            (okay, required) for name, okay, required, _detail in tray
            if name == "FFPLAY"))

    def test_optional_tray_packages_do_not_block_install(self):
        original = app.importlib.util.find_spec

        def find_spec(name):
            return None if name in {"PIL", "send2trash"} else original(name)

        with mock.patch.object(app.importlib.util, "find_spec", side_effect=find_spec):
            player = app.paf_readiness_checks()
            tray = app.paf_readiness_checks(tray_only=True)
        for name in ("Pillow", "Recycle Bin support"):
            with self.subTest(name=name):
                self.assertEqual((False, True), next(
                    (okay, required) for label, okay, required, _detail in player
                    if label == name))
                self.assertEqual((False, False), next(
                    (okay, required) for label, okay, required, _detail in tray
                    if label == name))


if __name__ == "__main__":
    unittest.main()

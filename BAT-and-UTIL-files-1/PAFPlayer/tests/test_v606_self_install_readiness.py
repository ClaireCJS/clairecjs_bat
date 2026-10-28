"""V606 self-install and readiness regressions; never launch playback."""

from __future__ import annotations

from contextlib import redirect_stdout
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as app


RUN = Path(__file__).resolve().parent / "runs" / ("v606-self-install-" + datetime.now().strftime("%Y%m%d%H%M%S%f"))


class SelfInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True, exist_ok=True)

    def fixture(self, name: str) -> tuple[Path, Path]:
        root = RUN / name
        root.mkdir()
        source = root / "loose" / "PAFPlayer.py"
        source.parent.mkdir()
        source.write_text("print('PAFPlayer fixture')\n", encoding="utf-8")
        base = root / "destination"
        base.mkdir()
        return source, base

    def test_destination_sequence_and_collisions_preserve_existing_content(self):
        source, base = self.fixture("collisions")
        now = datetime(2026, 10, 23, 14, 5, 6)
        names = ("PAFPlayer", "PAFPlayer_v606", "PAFPlayer_v606_20261023140506",
                 "PAFPlayer_v606_20261023140506 (1)")
        for name in names:
            (base / name).mkdir()
            (base / name / "keep.txt").write_text(name, encoding="utf-8")
        self.assertEqual(base / "PAFPlayer_v606_20261023140506 (2)",
                         app.paf_next_install_destination(base, "V606", now=now))
        installed = app.paf_stage_self_install(source, base, version="V606", now=now)
        self.assertEqual(names[-1].replace(" (1)", " (2)"), installed.name)
        for name in names:
            self.assertEqual(name, (base / name / "keep.txt").read_text(encoding="utf-8"))

    def test_copy_is_verified_and_original_and_data_are_untouched(self):
        source, base = self.fixture("copy")
        (source.parent / "PAFPlayer.dcc").write_text("active settings", encoding="utf-8")
        (source.parent / "playlist.m3u").write_text("active playlist", encoding="utf-8")
        original = source.read_bytes()
        installed = app.paf_stage_self_install(source, base)
        self.assertEqual(original, source.read_bytes())
        self.assertEqual(original, (installed / "PAFPlayer.py").read_bytes())
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         json.loads((installed / "state" / "install.json").read_text(encoding="utf-8"))["sha256"])
        self.assertTrue((installed / "PAFPlayer.md").is_file())
        self.assertTrue((installed / "docs" / "README.md").is_file())
        self.assertFalse((installed / "PAFPlayer.dcc").exists())
        self.assertFalse((installed / "playlist.m3u").exists())
        self.assertEqual("active settings", (source.parent / "PAFPlayer.dcc").read_text(encoding="utf-8"))

    def test_failed_readiness_never_launches_and_keeps_installed_copy(self):
        source, base = self.fixture("failed-check")
        with mock.patch.object(app, "run_paf_readiness_check", return_value=2), \
             mock.patch.object(app.subprocess, "Popen") as launch, redirect_stdout(io.StringIO()):
            self.assertEqual(2, app.run_paf_self_install([], source=source, base=base))
        launch.assert_not_called()
        self.assertTrue((base / "PAFPlayer" / "PAFPlayer.py").is_file())

    def test_success_launches_exact_installed_copy_with_original_arguments(self):
        source, base = self.fixture("launch")
        with mock.patch.object(app, "run_paf_readiness_check", return_value=0), \
             mock.patch.object(app.subprocess, "Popen") as launch, redirect_stdout(io.StringIO()):
            self.assertEqual(0, app.run_paf_self_install(["--tray-only", "music:666"], source=source, base=base))
        command = launch.call_args.args[0]
        self.assertEqual(str(base / "PAFPlayer" / "PAFPlayer.py"), command[2])
        self.assertEqual(["--bootstrap-installed", "--tray-only", "music:666"], command[3:])

    def test_loose_detection_avoids_reinstall_loop(self):
        source, base = self.fixture("loose-detection")
        self.assertTrue(app.paf_is_loose_script(source))
        installed = app.paf_stage_self_install(source, base)
        self.assertFalse(app.paf_is_loose_script(installed / "PAFPlayer.py"))
        (source.parent / "AGENTS.md").write_text("development checkout", encoding="utf-8")
        (source.parent / "src").mkdir()
        (source.parent / "src" / "PAFPlayer_workflows.py").write_text("", encoding="utf-8")
        self.assertFalse(app.paf_is_loose_script(source))


class ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RUN.mkdir(parents=True, exist_ok=True)

    def test_every_check_is_printed_and_failures_have_nonzero_exit(self):
        checks = [("Windows", True, True, "nt"), ("NumPy", False, True, "missing"),
                  ("Optional artwork", False, False, "missing")]
        output = io.StringIO()
        with mock.patch.object(app, "paf_readiness_checks", return_value=checks), redirect_stdout(output):
            self.assertEqual(2, app.run_paf_readiness_check())
        for label in ("[PASS] Windows", "[FAIL] NumPy", "[WARN] Optional artwork"):
            self.assertIn(label, output.getvalue())
        self.assertIn("pip install", output.getvalue())

    def test_readyness_alias_is_supported_but_corrected(self):
        output = io.StringIO()
        with mock.patch.object(app, "run_paf_readiness_check", return_value=0) as check, redirect_stdout(output):
            self.assertEqual(0, app.main(["--readyness-check", "--tray-only"]))
        check.assert_called_once_with(tray_only=True)
        self.assertIn("--readiness-check", output.getvalue())

    def test_integrity_check_detects_changed_installed_script(self):
        root = RUN / "integrity"
        root.mkdir()
        script = root / "PAFPlayer.py"
        script.write_text("print('fixture')\n", encoding="utf-8")
        (root / "state").mkdir()
        marker = root / "state" / "install.json"
        marker.write_text(json.dumps({"sha256": hashlib.sha256(script.read_bytes()).hexdigest()}), encoding="utf-8")
        with mock.patch.object(app.os, "name", "nt"):
            checks = app.paf_readiness_checks(script)
        self.assertTrue(next(c for c in checks if c[0] == "Installed copy integrity")[1])
        script.write_text("print('different')\n", encoding="utf-8")
        with mock.patch.object(app.os, "name", "nt"):
            checks = app.paf_readiness_checks(script)
        self.assertEqual((False, True), next((c[1], c[2]) for c in checks if c[0] == "Installed copy integrity"))

    def test_passion_family_is_literal_without_substitution(self):
        for word in ("passion", "passions", "Passion", "PASSIONS"):
            with self.subTest(word=word):
                self.assertIsNone(app.emojimax_replacement_for_key(word))
                rendered, solutions = app.emojimax_plain_with_solutions(word)
                self.assertEqual((word, []), (rendered, solutions))
        self.assertNotIn("compassion", app.EMOJIMAX_V606_REMOVED)


if __name__ == "__main__":
    unittest.main()

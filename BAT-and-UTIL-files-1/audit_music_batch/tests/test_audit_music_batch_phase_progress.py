import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class AuditPhaseProgressTests(unittest.TestCase):
    def test_phase_resets_its_counter_and_announces_even_without_bar(self):
        root = Path(tempfile.mkdtemp(prefix="audit-phase-"))
        scanner = audit.BatchAudit(root)
        scanner.progress = mock.Mock()
        scanner.progress.format_dict = {}
        scanner.progress.n = 0
        scanner.progress.initial = 0
        scanner.progress.unit = "checks"
        with contextlib.redirect_stdout(io.StringIO()) as output:
            scanner.progress_phase("🎵 Reading audio metadata", total=7)
        scanner.progress.reset.assert_called_once_with(total=7)
        self.assertEqual(scanner.progress.total, 7)
        self.assertEqual("", output.getvalue())
        scanner.progress.set_description.assert_called_with("🎵 Reading audio metadata", refresh=False)
        self.assertIn("{percentage:3.0f}", scanner.progress.bar_format)
        self.assertIn("{n:01.0f}", scanner.progress.bar_format)
        scanner.progress = None
        with contextlib.redirect_stdout(io.StringIO()) as output:
            scanner.progress_phase("📂 Checking sidecars", total=4)
        self.assertIn("📂 Checking sidecars", output.getvalue())

    def test_real_shared_progress_renders_for_each_scan_phase(self):
        self.assertIsNone(audit._PROGRESS_IMPORT_ERROR, audit._PROGRESS_IMPORT_ERROR)
        root = Path(tempfile.mkdtemp(prefix="audit-visible-phase-"))
        (root / "notes.txt").write_text("fixture", encoding="utf-8")
        output = io.StringIO()
        bars = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(bars), mock.patch.object(audit, "progress_terminal_enabled", return_value=True):
            audit.BatchAudit(root).audit(embed_lyrics_first=False)
        for stage in ("Finding files", "Recording file state", "Checking filenames and sidecars", "Checking duplicates and archives", "Reading audio metadata"):
            self.assertIn(stage, bars.getvalue())
        self.assertIn("Finding audio and sidecar files", output.getvalue())
        self.assertIn("\r", bars.getvalue())

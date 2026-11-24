import unittest
from pathlib import Path
from unittest import mock
import audit_music_batch as audit


class FixedProgressTests(unittest.TestCase):
    def test_fixed_width_speed_time_and_long_filename(self):
        scanner = audit.BatchAudit(Path.cwd())
        scanner.progress = mock.Mock()
        scanner.progress.total = 1110
        scanner.progress.n = 32
        scanner.progress.format_dict = {"elapsed": 22, "rate": 1.27}
        scanner._fixed_audit_progress = True
        scanner._audit_filename_width = 60
        scanner._progress_audio_preview = "02_Blood.flac"
        scanner.refresh_progress_postfix(refresh=False)
        first = scanner.progress.set_postfix_str.call_args.args[0]
        self.assertIn("     1.3 ✓/s", first)
        self.assertNotIn("000001.3", first)
        self.assertIn("00:00:22", first)
        self.assertIn("02_Blood.flac", first)
        scanner.progress.n = 900
        scanner.progress.format_dict = {"elapsed": 3601, "rate": 123.45}
        scanner._progress_audio_preview = "A much longer recognizable song title with a featured artist.flac"
        scanner.refresh_progress_postfix(refresh=False)
        second = scanner.progress.set_postfix_str.call_args.args[0]
        self.assertEqual(audit.visible_cell_width(first), audit.visible_cell_width(second))
        self.assertIn(".flac", second)
        self.assertNotIn("checks/s", second)

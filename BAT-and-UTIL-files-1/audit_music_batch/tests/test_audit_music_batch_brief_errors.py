import contextlib
import io
from pathlib import Path
import unittest
from unittest import mock

import audit_music_batch as audit


class BriefErrorTests(unittest.TestCase):
    def test_console_omits_raw_tags_paths_and_decoder_dump(self):
        detail = "Audio integrity check failed: Header missing\nLYRICS_PRIVATE " + "decoder output " * 1000
        with mock.patch.object(audit, "batch_event") as journal, contextlib.redirect_stdout(io.StringIO()) as output:
            audit.print_file_error(Path("C:/private-folder/track.mp3"), RuntimeError(detail), "Bake skipped", False)
        text = output.getvalue()
        self.assertIn("track.mp3", text)
        self.assertIn("Invalid audio frame/header", text)
        self.assertNotIn("LYRICS_PRIVATE", text)
        self.assertNotIn("private-folder", text)
        self.assertLess(len(text), 200)
        self.assertEqual(journal.call_args.kwargs["error"], detail)

    def test_unknown_diagnostic_is_not_echoed(self):
        self.assertEqual(audit.brief_file_error_reason(ValueError("lyrics and private metadata")), "Operation failed")

    def test_recovery_warning_survives_summary(self):
        with mock.patch.object(audit, "batch_event"), contextlib.redirect_stdout(io.StringIO()) as output:
            audit.print_file_error(Path("track.flac"), OSError("backup failure"), "ROLLBACK FAILED — recovery needed", False)
        self.assertIn("ROLLBACK FAILED", output.getvalue())

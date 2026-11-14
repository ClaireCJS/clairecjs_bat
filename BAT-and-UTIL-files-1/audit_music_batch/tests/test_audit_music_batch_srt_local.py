import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class LocalSrtTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="audit-local-srt-"))
        self.audio = self.root / "track.flac"
        self.audio.write_bytes(b"fixture")
        self.audio.with_suffix(".lrc").write_text("[00:01.00]fixture\n")
        self.audio.with_suffix(".txt").write_text("fixture\n")
        self.finding = {"category": "missing_srt_from_lrc_txt", "path": ".",
                        "code": "a", "severity": "safe_fix", "message": "Missing SRT",
                        "suggestion": "Generate", "details": {"affected_files": ["track.flac"], "folder_level": True}}

    def test_reused_auditor_does_not_accumulate_findings(self):
        scanner = audit.BatchAudit(self.root)
        def add_finding():
            scanner.add("safe_fix", "missing_srt_from_lrc_txt", self.root, "Missing", "Generate")
        with mock.patch.object(scanner, "audit_filesystem", side_effect=add_finding), mock.patch.object(scanner, "audit_duplicates_and_archives"), mock.patch.object(scanner, "audit_audio_tags"), contextlib.redirect_stdout(io.StringIO()):
            first = scanner.audit()
            second = scanner.audit()
        self.assertEqual(len(first["findings"]), 1)
        self.assertEqual(len(second["findings"]), 1)

    def test_duplicate_folder_actions_convert_once_without_batch_rescan(self):
        finding2 = {**self.finding, "code": "b"}
        commands = []
        def convert(command, **kwargs):
            commands.append(command)
            self.audio.with_suffix(".srt").write_text("1\n00:00:01,000 --> 00:00:02,000\nfixture\n")
            return mock.Mock(returncode=0, stdout="done")
        key = mock.Mock(return_value="y")
        with mock.patch.object(audit, "lrc2srt_executable", return_value=self.root / "converter.py"), mock.patch.object(audit.subprocess, "run", side_effect=convert), mock.patch.object(audit, "audit_categories_by_path", side_effect=AssertionError("Full batch scan forbidden")) as scan, contextlib.redirect_stdout(io.StringIO()):
            result = audit.interactive_apply({"resolved_root": str(self.root), "findings": [self.finding, finding2]}, False, key_reader=key)
        self.assertEqual(result["failed_codes"], "", result)
        self.assertEqual(result["applied_codes"], "a")
        self.assertEqual(result["skipped_codes"], "b")
        self.assertEqual(key.call_count, 1)
        self.assertEqual(len(commands), 1)
        self.assertNotIn("--recursive", commands[0])
        scan.assert_not_called()

    def test_satisfied_action_skips_before_prompt_or_converter(self):
        self.audio.with_suffix(".srt").write_text("existing sidecar")
        key = mock.Mock(side_effect=AssertionError("No prompt needed"))
        with mock.patch.object(audit, "generate_missing_srt_sidecars", side_effect=AssertionError("No converter needed")), contextlib.redirect_stdout(io.StringIO()):
            result = audit.interactive_apply({"resolved_root": str(self.root), "findings": [self.finding]}, False, key_reader=key)
        self.assertEqual(result["skipped_codes"], "a")
        key.assert_not_called()

    def test_empty_or_missing_srt_does_not_count_as_resolved(self):
        self.assertFalse(audit.nonempty_srt_exists(self.audio))
        self.audio.with_suffix(".srt").write_bytes(b"")
        self.assertFalse(audit.nonempty_srt_exists(self.audio))

    def test_failed_generation_is_not_reported_as_success(self):
        with mock.patch.object(audit, "generate_missing_srt_sidecars", return_value=[]), mock.patch.object(audit, "audit_categories_by_path", side_effect=AssertionError("Full batch scan forbidden")), contextlib.redirect_stdout(io.StringIO()):
            result = audit.interactive_apply({"resolved_root": str(self.root), "findings": [self.finding]}, False, key_reader=lambda: "y")
        self.assertEqual(result["failed_codes"], "a")
        self.assertEqual(result["applied_codes"], "")

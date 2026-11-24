import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


@unittest.skipUnless(os.name == "nt", "Windows backup limits")
class LongBackupTests(unittest.TestCase):
    def test_component_overflow_automatically_uses_shorter_backup_suffix(self):
        root = Path(tempfile.mkdtemp(prefix="audit-backup-limit-"))
        source = root / (("a" * 220) + ".mp3")
        source.write_bytes(b"unchanged")
        backup = audit.backup_before_inline_replacement(source, "202611131033")
        self.assertLessEqual(len(backup.name.encode("utf-16-le")) // 2, 255)
        self.assertTrue(backup.name.endswith(".bak.202611131033.gptrepl.bak"))
        self.assertEqual(backup.read_bytes(), b"unchanged")
        self.assertEqual(source.read_bytes(), b"unchanged")

    def test_prompted_backup_stem_is_remembered_and_reused(self):
        root = Path(tempfile.mkdtemp(prefix="audit-backup-alias-"))
        source = root / (("a" * 240) + ".mp3")
        source.write_bytes(b"unchanged")
        memory = root / "backup-names.jsonl"
        prompts = []
        backup = audit.backup_before_inline_replacement(
            source, "202611131033", input_reader=lambda prompt: prompts.append(prompt) or "short-name",
            memory_path=memory,
        )
        self.assertTrue(prompts)
        self.assertTrue(backup.name.startswith("short-name.mp3.bak."))
        self.assertEqual(backup.read_bytes(), b"unchanged")
        remembered = audit.replacement_backup_path(
            source, "202611131034", input_reader=lambda _prompt: self.fail("Should remember alias"),
            memory_path=memory,
        )
        self.assertTrue(remembered.name.startswith("short-name.mp3.bak."))
        self.assertFalse(source.name.startswith("short-name"))

    def test_real_long_path_copy_and_collision(self):
        root = Path(tempfile.mkdtemp(prefix="audit-backup-long-"))
        folder = root / ("a" * 90) / ("b" * 90)
        audit.windows_file_io_path(folder).mkdir(parents=True)
        source = folder / ("track-" + "c" * 60 + ".flac")
        audit.windows_file_io_path(source).write_bytes(b"synthetic audio fixture")
        one = audit.backup_before_inline_replacement(source, "202611121850")
        two = audit.backup_before_inline_replacement(source, "202611121850")
        self.assertGreater(len(str(one)), 260)
        self.assertNotEqual(one, two)
        self.assertTrue(two.name.endswith(" (1).bak"))
        self.assertEqual(audit.windows_file_io_path(one).read_bytes(), b"synthetic audio fixture")
        self.assertEqual(audit.windows_file_io_path(two).read_bytes(), b"synthetic audio fixture")

    def test_unc_prefix(self):
        self.assertEqual(str(audit.windows_file_io_path(Path(r"\\server\share\song.flac"))), r"\\?\UNC\server\share\song.flac")

    def test_embedding_failure_continues_to_next_file(self):
        root = Path(tempfile.mkdtemp(prefix="audit-embed-failure-"))
        paths = [root / "first.flac", root / "second.flac"]
        for path in paths:
            path.write_bytes(b"fixture")
        scanner = audit.BatchAudit(root)
        with mock.patch.object(audit, "embed_lyrics", side_effect=[OSError("WinError 123 backup refused"), ["embedded"]]) as embed, mock.patch.object(scanner, "audit_filesystem"), mock.patch.object(scanner, "audit_duplicates_and_archives"), mock.patch.object(scanner, "audit_audio_tags"), contextlib.redirect_stdout(io.StringIO()):
            report = scanner.audit(embed_lyrics_first=True)
        self.assertEqual(embed.call_count, 2)
        self.assertEqual(len(report["embedding_failures"]), 1)
        self.assertEqual(len(report["embedded_lyrics"]), 1)
        self.assertEqual(paths[0].read_bytes(), b"fixture")

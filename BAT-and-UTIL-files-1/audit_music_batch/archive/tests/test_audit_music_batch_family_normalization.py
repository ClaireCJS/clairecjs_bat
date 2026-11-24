import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class FamilyNormalizationTests(unittest.TestCase):
    def test_one_approval_renames_family_and_suppresses_duplicate_findings(self):
        root = Path(tempfile.mkdtemp(prefix="audit-family-normalization-"))
        stem = "Artist - Song [feat. Guest]"
        new_stem = "Artist - Song [feat Guest]"
        suffixes = [".flac", ".jpg", ".lrc", ".srt", ".txt", ".log", ".flac.bak.202601010101.replaced-by-chatgpt.bak"]
        for suffix in suffixes:
            (root / (stem + suffix)).write_bytes(b"fixture")
        playlist = root / "album.m3u"
        playlist.write_text(stem + ".flac\n", encoding="utf-8")
        findings = []
        for suffix in [".jpg", ".flac", ".lrc", ".flac", ".jpg"]:
            findings.append({"path": stem + suffix, "category": "filename_marker_style", "code": "a",
                             "severity": "review", "message": "Normalize filename", "suggestion": "Rename family",
                             "details": {"proposed_name": new_stem + suffix}})
        key = mock.Mock(return_value="y")
        with mock.patch.object(audit, "migrate_waveform_review_cache_path", return_value=[]) as migrate, contextlib.redirect_stdout(io.StringIO()):
            result = audit.interactive_apply({"resolved_root": str(root), "findings": findings}, False, key_reader=key)
        self.assertFalse(result["failed_codes"], result)
        self.assertEqual(key.call_count, 1)
        self.assertEqual(migrate.call_count, 1)
        for suffix in suffixes:
            self.assertFalse((root / (stem + suffix)).exists())
            self.assertEqual((root / (new_stem + suffix)).read_bytes(), b"fixture")
        self.assertIn(new_stem + ".flac", playlist.read_text(encoding="utf-8"))

    def test_preflight_folder_progress_uses_shared_live_bar(self):
        progress = mock.Mock()
        folders = [Path("one"), Path("two")]
        with mock.patch.object(audit, "live_bake_progress", return_value=contextlib.nullcontext(progress)) as bar:
            self.assertEqual(list(audit.progress_preflight_folders(folders)), folders)
        self.assertEqual(bar.call_args.kwargs["total"], 2)
        self.assertEqual(progress.update.call_count, 2)
        self.assertEqual(progress.set_postfix_str.call_count, 2)

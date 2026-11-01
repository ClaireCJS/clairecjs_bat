"""Isolated batch safeguards; retain TEMP fixtures for inspection."""
import contextlib
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class BatchSafetyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="audit-v165-"))
        self.session = audit._BATCH_SESSION
        self.guard = audit._ACTIVE_CHANGE_GUARD
        audit._BATCH_SESSION = None
        audit._ACTIVE_CHANGE_GUARD = None
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()

    def tearDown(self):
        audit._BATCH_SESSION = self.session
        audit._ACTIVE_CHANGE_GUARD = self.guard
        self.output.__exit__(None, None, None)

    def fixture(self, name, content=b"original"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    @unittest.skipUnless(os.name == "nt", "Windows locks")
    def test_parent_child_conflict_both_directions_and_siblings_allowed(self):
        child = self.root / "child"
        sibling = self.root / "sibling"
        child.mkdir()
        sibling.mkdir()
        code = "from audit_music_batch import BatchFolderLock; import sys; lock=BatchFolderLock(sys.argv[1]); lock.close()"
        for owner, contender, allowed in ((self.root, child, False), (child, self.root, False), (child, sibling, True), (child, child / '..' / 'child', False)):
            lock = audit.BatchFolderLock(owner)
            try:
                result = subprocess.run([sys.executable, "-B", "-c", code, str(contender)], capture_output=True, timeout=15)
                self.assertEqual(result.returncode == 0, allowed, result.stderr)
            finally:
                lock.close()
        lock = audit.BatchFolderLock(self.root)
        lock.close()

    def test_changed_target_since_audit_rejected(self):
        source = self.fixture("song.flac")
        observed = audit.folder_file_states(self.root)
        source.rename(self.root / "old.flac")
        source.write_bytes(b"external replacement")
        with self.assertRaises(audit.ExternalFileChange):
            audit.ActionChangeGuard(self.root, observed)

    def test_sidecar_arriving_during_prompt_blocks_rename(self):
        source = self.fixture("song.flac")
        audit._ACTIVE_CHANGE_GUARD = audit.ActionChangeGuard(self.root)
        self.fixture("song.lrc")
        with self.assertRaises(audit.ExternalFileChange):
            audit.tracked_rename(source, self.root / "new.flac")
        self.assertTrue(source.exists())
        self.assertFalse((self.root / "new.flac").exists())

    def test_approved_rename_is_accepted_by_next_guard(self):
        source = self.fixture("song.flac")
        observed = audit.folder_file_states(self.root)
        guard = audit.ActionChangeGuard(self.root, observed)
        audit._ACTIVE_CHANGE_GUARD = guard
        target = self.root / "new.flac"
        audit.tracked_rename(source, target)
        for name in guard.touched:
            state = audit.action_file_state(name)
            if state is None:
                observed.pop(name, None)
            else:
                observed[name] = state
        audit.ActionChangeGuard(self.root, observed).check(target)

    def test_folder_choices_resume_only_same_batch(self):
        database = self.root / "journal.sqlite3"
        session = audit.BatchSession(self.root, database)
        session.remember_folder("embedded_art_without_sidecar", self.root, "stop_folder")
        session.remember_folder("missing_album", self.root, "skip_album")
        session.remember_folder("simplify_punk_genre", self.root, "Alternative")
        session.finish(False)
        resumed = audit.BatchSession(self.root, database, session.run_id)
        self.assertEqual(resumed.folder_choices(), session.folder_choices())
        self.assertEqual(len(resumed.folder_choices()), 3)
        self.assertEqual(audit.BatchSession(self.root, database).folder_choices(), {})

    def test_folder_action_checks_contents_without_treating_folder_as_file(self):
        self.fixture("track.flac")
        guard = audit.ActionChangeGuard(self.root)
        guard.check(self.root, consume=False)
        guard.check(self.root / "track.flac")

    def test_failure_resolution_retains_other_failures(self):
        session = audit.BatchSession(self.root, self.root / "journal.sqlite3")
        session.event("failure", operation="bake", path="a")
        session.event("failure", operation="bake", path="b")
        session.resolve_failure("bake", "a")
        self.assertTrue(session.has_failures)
        session.resolve_failure("bake", "b")
        self.assertFalse(session.has_failures)

    def test_waveform_retry_only_failed_paths(self):
        bad = self.fixture("failed.flac")
        result = {"failed": [{"path": str(bad), "error": "decode failed"}], "fine": ["already done"]}
        with mock.patch.object(audit, "prompt_for_approval", return_value=True), mock.patch.object(audit, "review_waveforms", return_value={"failed": [], "fine": [str(bad)]}) as review:
            retried = audit.retry_failed_waveforms(self.root, result, False)
        self.assertEqual(review.call_args.kwargs["only_paths"], [bad])
        self.assertEqual(retried["failed"], [])
        self.assertEqual(len(retried["fine"]), 2)

    def test_retry_decline_does_not_render(self):
        result = {"failed": [{"path": "missing", "error": "bad"}]}
        with mock.patch.object(audit, "prompt_for_approval", return_value=False), mock.patch.object(audit, "review_waveforms") as review:
            self.assertIs(audit.retry_failed_waveforms(self.root, result, False), result)
        review.assert_not_called()

    def test_action_retry_filters_fresh_scan_and_forces_new_prompt(self):
        finding = {"category": "missing_genre", "code": "G", "path": "song.flac"}
        other = {"category": "missing_album", "code": "A", "path": "other.flac"}
        result = {"decisions": [{"finding": finding, "code": "G", "error": "stale"}]}
        fresh = {"resolved_root": str(self.root), "findings": [finding, other]}
        success = {"decisions": [{"finding": finding, "code": "G", "applied": True}]}
        with mock.patch.object(audit, "prompt_for_approval", return_value=True), mock.patch.object(audit, "BatchAudit") as scan, mock.patch.object(audit, "interactive_apply", return_value=success) as apply:
            scan.return_value.audit.return_value = fresh
            result = audit.retry_failed_findings({"resolved_root": str(self.root)}, result, False)
        self.assertEqual(apply.call_args.args[0]["findings"], [finding])
        self.assertTrue(apply.call_args.args[0]["_force_prompts"])
        self.assertEqual(result["failed_codes"], "")

    def test_cleanup_two_confirmations_and_backup_only(self):
        backup = self.fixture("song.flac.bak")
        self.fixture("song.flac")
        for choices, expected in (([False], []), ([True, False], []), ([True, True], [backup])):
            with mock.patch.object(audit, "prompt_for_approval", side_effect=choices), mock.patch.object(audit, "recycle_path") as recycle:
                self.assertEqual(audit.offer_backup_cleanup(self.root, False), expected)
                self.assertEqual(recycle.call_count, len(expected))

    def test_cleanup_stale_preview_and_unresolved_failures_do_not_recycle(self):
        self.fixture("song.flac.bak")
        with mock.patch.object(audit, "prompt_for_approval", return_value=True), mock.patch.object(audit, "action_file_state", side_effect=[[8, 1], [9, 2]]), mock.patch.object(audit, "recycle_path") as recycle:
            self.assertEqual(audit.offer_backup_cleanup(self.root, False), [])
            recycle.assert_not_called()
        audit._BATCH_SESSION = mock.Mock(has_failures=True)
        with mock.patch.object(audit, "prompt_for_approval") as prompt:
            self.assertEqual(audit.offer_backup_cleanup(self.root, False), [])
            prompt.assert_not_called()

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_multichannel_unicode_long_path_and_bad_metadata(self):
        folder = self.root / ("Unicode-é-" + "x" * 80) / ("album-" + "y" * 80)
        folder.mkdir(parents=True)
        audio = folder / "01_音楽 — six channels.flac"
        subprocess.run([shutil.which("ffmpeg"), "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=5.1", "-t", "0.15", "-c:a", "flac", str(audio)], check=True, capture_output=True, timeout=15)
        original = hashlib.sha256(audio.read_bytes()).hexdigest()
        audit.validate_audio_decode(audio, shutil.which("ffmpeg"), visible=False)
        self.assertEqual(hashlib.sha256(audio.read_bytes()).hexdigest(), original)
        bad = folder / "02_malformed.flac"
        bad.write_bytes(b"fLaC\x80\xff\xff\xfftruncated metadata")
        with self.assertRaises(RuntimeError):
            audit.validate_audio_decode(bad, shutil.which("ffmpeg"), visible=False)
        self.assertEqual(bad.read_bytes(), b"fLaC\x80\xff\xff\xfftruncated metadata")
        report = audit.BatchAudit(folder).audit(embed_lyrics_first=False)
        self.assertTrue(report["findings"])
        self.assertEqual(hashlib.sha256(audio.read_bytes()).hexdigest(), original)


if __name__ == "__main__":
    unittest.main()

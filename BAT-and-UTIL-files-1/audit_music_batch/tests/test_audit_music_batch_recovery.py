"""Recovery tests use isolated scratch directories; no music-library writes."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import audit_music_batch as audit
from audit_music_batch import BatchSession, monitored_process, history_lines


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="audit-recovery-test-"))
        self.database = self.root / "history.sqlite3"
        self.previous_session = audit._BATCH_SESSION
        audit._BATCH_SESSION = None

    def tearDown(self):
        audit._BATCH_SESSION = self.previous_session
        # Retain scratch artifacts rather than permanently deleting them.

    def test_resume_requires_same_file_and_explicit_session(self):
        path = self.root / "song.flac"
        path.write_bytes(b"original")
        session = BatchSession(self.root, self.database)
        session.remember("genre", path, "applied")
        self.assertIsNone(session.previous("genre", path))
        session.finish(False)
        self.assertEqual(BatchSession.unfinished(self.root, self.database), (session.run_id,))
        resumed = BatchSession(self.root, self.database, session.run_id)
        self.assertEqual(resumed.previous("genre", path), "applied")
        path.rename(self.root / "original.flac")
        path.write_bytes(b"different")
        self.assertEqual(resumed.previous("genre", path), "file changed since checkpoint")

    def test_fresh_choice_does_not_resume(self):
        prior = BatchSession(self.root, self.database)
        prior.finish(False)
        factory = lambda root, run_id=None: BatchSession(root, self.database, run_id)
        with mock.patch.object(audit, "BatchSession") as cls, mock.patch("builtins.input", return_value=""), contextlib.redirect_stdout(io.StringIO()):
            cls.unfinished.return_value = (prior.run_id,)
            cls.side_effect = factory
            audit.start_batch_session(self.root)
        self.assertFalse(audit._BATCH_SESSION.resuming)
        self.assertNotEqual(prior.run_id, audit._BATCH_SESSION.run_id)
        with prior.connect() as db:
            self.assertEqual(db.execute("SELECT status FROM runs WHERE id=?", (prior.run_id,)).fetchone()[0], "superseded")

    def test_failure_keeps_run_resumable(self):
        session = BatchSession(self.root, self.database)
        session.event("failure", error="decoder failed")
        session.finish(True)
        self.assertIsNotNone(BatchSession.unfinished(self.root, self.database))

    def test_monitored_process_drains_more_than_pipe_capacity(self):
        result = monitored_process([sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x'*200000); sys.stderr.write('last error')"], timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(result.stdout), 200010)
        self.assertIn(b"last error", result.stdout)

    def test_timeout_contains_child_diagnostics_and_reaps_child(self):
        children = []
        real_popen = subprocess.Popen
        def capture(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child
        with mock.patch("audit_music_batch.subprocess.Popen", side_effect=capture):
            with self.assertRaisesRegex(TimeoutError, "decoder stuck"):
                monitored_process([sys.executable, "-c", "import time; print('decoder stuck', flush=True); time.sleep(20)"], timeout=.5)
        self.assertIsNotNone(children[0].poll())

    def test_interrupt_reaps_child(self):
        children = []
        real_popen = subprocess.Popen
        def capture(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child
        def interrupt(elapsed, tail):
            raise KeyboardInterrupt()
        with mock.patch("audit_music_batch.subprocess.Popen", side_effect=capture):
            with self.assertRaises(KeyboardInterrupt):
                monitored_process([sys.executable, "-c", "import time; time.sleep(20)"], on_tick=interrupt)
        self.assertIsNotNone(children[0].poll())

    def test_nested_pending_paths_follow_staging_and_final_rename(self):
        source = self.root / "old.flac"
        staged = self.root / "temporary.tmp"
        target = self.root / "new.flac"
        other = self.root / "elsewhere" / "old.flac"
        findings = [{"path": "old.flac", "details": {"renames": [{"source": str(source)}], "unrelated": str(other)}}]
        audit.refresh_pending_paths(findings, self.root, [(source, staged), (staged, target)])
        self.assertEqual(findings[0]["path"], "new.flac")
        self.assertEqual(findings[0]["details"]["renames"][0]["source"], str(target))
        self.assertEqual(findings[0]["details"]["unrelated"], str(other))

    def test_backup_and_rename_have_recovery_mappings(self):
        audit._BATCH_SESSION = BatchSession(self.root, self.database)
        source = self.root / "song.txt"
        source.write_text("keep me")
        backup = audit.backup_before_inline_replacement(source)
        target = self.root / "renamed.txt"
        audit.tracked_rename(source, target)
        self.assertEqual(backup.read_text(), target.read_text())
        history = "\n".join(history_lines(self.root, self.database))
        self.assertIn("backup_complete", history)
        self.assertIn("rename_complete", history)
        self.assertIn("renamed.txt", history)

    def test_invalid_decode_rejects_source(self):
        source = self.root / "bad.flac"
        source.write_bytes(b"untouched")
        with mock.patch.object(audit, "supervised_audio_command", return_value=subprocess.CompletedProcess([], 1, b"CRC error")):
            with self.assertRaisesRegex(RuntimeError, "CRC error"):
                audit.validate_audio_decode(source, "ffmpeg", visible=False)
        self.assertEqual(source.read_bytes(), b"untouched")


if __name__ == "__main__":
    unittest.main()

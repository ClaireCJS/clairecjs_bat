"""Real OS contention and family-recovery tests using disposable fixtures."""
import ctypes
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from collections import namedtuple

import audit_music_batch as audit
from audit_music_batch import BatchFolderLock, preflight_audio_replacement


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="audit-safety-"))

    def child_lock(self):
        return subprocess.run([sys.executable, "-B", "-c",
            "from audit_music_batch import BatchFolderLock; import sys; lock=BatchFolderLock(sys.argv[1]); lock.close()",
            str(self.root)], capture_output=True, timeout=10, cwd=Path(audit.__file__).parent)

    def test_other_process_is_blocked_then_can_acquire(self):
        lock = BatchFolderLock(self.root)
        try:
            result = self.child_lock()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"already modifying", result.stderr)
        finally:
            lock.close()
        self.assertEqual(self.child_lock().returncode, 0)

    def test_crashed_owner_does_not_leave_stale_lock(self):
        result = subprocess.run([sys.executable, "-B", "-c",
            "from audit_music_batch import BatchFolderLock; import sys,os; lock=BatchFolderLock(sys.argv[1]); os._exit(9)",
            str(self.root)], capture_output=True, timeout=10, cwd=Path(audit.__file__).parent)
        self.assertEqual(result.returncode, 9)
        self.assertEqual(self.child_lock().returncode, 0)

    def test_disk_shortage_preserves_source(self):
        source = self.root / "song.flac"
        source.write_bytes(b"original")
        usage = namedtuple("usage", "total used free")
        with mock.patch("audit_music_batch.shutil.disk_usage", return_value=usage(100, 99, 1)):
            with self.assertRaisesRegex(RuntimeError, "Insufficient"):
                preflight_audio_replacement(source)
        self.assertEqual(source.read_bytes(), b"original")

    def test_real_windows_exclusive_lock_is_detected(self):
        source = self.root / "song.flac"
        source.write_bytes(b"original")
        from ctypes import wintypes
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        api.CreateFileW.restype = wintypes.HANDLE
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = api.CreateFileW(str(source), 0x80000000, 0, None, 3, 0, None)
        self.assertNotEqual(handle, ctypes.c_void_p(-1).value)
        try:
            with self.assertRaisesRegex(RuntimeError, "locked"):
                preflight_audio_replacement(source)
        finally:
            api.CloseHandle(handle)
        preflight_audio_replacement(source)
        self.assertEqual(source.read_bytes(), b"original")

    def test_family_roundtrip_restores_sidecars_playlists_and_approval(self):
        source = self.root / "old.flac"
        contents = {"old.flac": b"audio", "old.lrc": b"lyrics", "old.srt": b"subtitles",
                    "old.flac.bak.202001010000.replaced-by-chatgpt.bak": b"backup"}
        for name, content in contents.items():
            (self.root / name).write_bytes(content)
        playlist = self.root / "album.m3u"
        playlist.write_bytes(b"old.flac\n")
        store = audit.WaveformApprovalStore(self.root / "approvals.sqlite3")
        store.approve(source)
        def cache(path):
            return (self.root / (path.stem + ".before.jpg"), self.root / (path.stem + ".after.jpg"))
        for path in cache(source):
            path.write_bytes(b"preview")
        with mock.patch.object(audit, "WaveformApprovalStore", return_value=store), mock.patch.object(audit, "replaygain_bake_waveform_cache_paths", side_effect=cache):
            renamed, _, backups = audit.rename_waveform_problem_family(source, "new.flac")
            self.assertTrue(store.is_approved(renamed))
            self.assertIn(b"new.flac", playlist.read_bytes())
            self.assertTrue(backups)
            restored, _, _ = audit.rename_waveform_problem_family(renamed, "old.flac")
        self.assertTrue(store.is_approved(restored))
        self.assertEqual(playlist.read_bytes(), b"old.flac\n")
        for name, content in contents.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        for path in cache(source):
            self.assertEqual(path.read_bytes(), b"preview")

    def test_mid_rename_failure_rolls_back_without_losing_family(self):
        source = self.root / "old.flac"
        source.write_bytes(b"audio")
        (self.root / "old.lrc").write_bytes(b"lyrics")
        real = audit.tracked_rename
        calls = [0]
        def fail_once(src, dst):
            calls[0] += 1
            if calls[0] == 3:
                raise OSError("injected interruption")
            return real(src, dst)
        with mock.patch.object(audit, "tracked_rename", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                audit.rename_waveform_problem_family(source, "new.flac")
        self.assertEqual(source.read_bytes(), b"audio")
        self.assertEqual((self.root / "old.lrc").read_bytes(), b"lyrics")
        self.assertFalse((self.root / "new.flac").exists())


if __name__ == "__main__":
    unittest.main()

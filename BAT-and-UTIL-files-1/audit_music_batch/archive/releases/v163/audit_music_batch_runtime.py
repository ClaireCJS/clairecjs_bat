"""Persistent run history and subprocess supervision for audit_music_batch."""
from __future__ import annotations

from collections import deque
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid
import os
import hashlib
import shutil
from contextlib import contextmanager


@contextmanager
def closing_database(*args, **kwargs):
    connection = sqlite3.connect(*args, **kwargs)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


class BatchFolderLock:
    """OS-owned mutex: crashes release ownership, so stale lock files cannot block runs."""
    def __init__(self, root):
        self.handle = None
        key = hashlib.sha256(os.path.normcase(str(Path(root).resolve())).encode()).hexdigest()
        if os.name != "nt":
            raise RuntimeError("Batch folder locking currently requires Windows")
        import ctypes
        from ctypes import wintypes
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        self.api.CreateMutexW.restype = wintypes.HANDLE
        self.api.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.api.ReleaseMutex.argtypes = [wintypes.HANDLE]
        self.api.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = self.api.CreateMutexW(None, False, "Global\\ClaireAuditMusicBatch_" + key)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        result = self.api.WaitForSingleObject(handle, 0)
        if result not in (0, 0x80):  # acquired or abandoned by a crashed process
            self.api.CloseHandle(handle)
            raise RuntimeError(f"Another audit is already modifying this folder: {root}")
        self.handle = handle

    def close(self):
        if self.handle is not None:
            self.api.ReleaseMutex(self.handle)
            self.api.CloseHandle(self.handle)
            self.handle = None


def preflight_audio_replacement(source, *, copies=4):
    """Conservative space and exclusive-access probe; no audio bytes are written."""
    source = Path(source)
    required = source.stat().st_size * copies + 64 * 1024 * 1024
    free = shutil.disk_usage(source.parent).free
    if free < required:
        raise RuntimeError(f"Insufficient backup/staging space for {source.name}: "
                           f"need at least {required:,} bytes; {free:,} free. File skipped.")
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        api.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                   ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        api.CreateFileW.restype = wintypes.HANDLE
        api.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = api.CreateFileW(str(source.resolve()), 0xC0000000, 0, None, 3, 0, None)
        if handle == ctypes.c_void_p(-1).value:
            error = ctypes.get_last_error()
            raise RuntimeError(f"File locked, read-only, or inaccessible: {source} (Windows error {error}). File skipped.")
        api.CloseHandle(handle)
    return required


def fingerprint(path):
    try:
        stat = Path(path).stat()
        return [stat.st_size, stat.st_mtime_ns, stat.st_ino]
    except FileNotFoundError:
        return None


class BatchSession:
    def __init__(self, root, database=None, run_id=None):
        self.root = str(Path(root).resolve())
        self.database = Path(database or Path(tempfile.gettempdir()) / "audit_music_batch" / "batch_history.sqlite3")
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or uuid.uuid4().hex
        self.resuming = run_id is not None
        self.has_failures = False
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, root TEXT, status TEXT, started REAL);
                CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, run TEXT, time REAL, kind TEXT, data TEXT);
                CREATE TABLE IF NOT EXISTS checkpoints(run TEXT, category TEXT, path TEXT, fingerprint TEXT,
                    outcome TEXT, PRIMARY KEY(run, category, path));
            ''')
            db.execute("INSERT OR IGNORE INTO runs VALUES(?,?,?,?)", (self.run_id, self.root, "running", time.time()))
            db.execute("UPDATE runs SET status='running' WHERE id=?", (self.run_id,))

    def connect(self):
        return closing_database(self.database, timeout=30)

    @staticmethod
    def unfinished(root, database=None):
        database = Path(database or Path(tempfile.gettempdir()) / "audit_music_batch" / "batch_history.sqlite3")
        if not database.exists():
            return None
        with closing_database(database) as db:
            return db.execute("SELECT id FROM runs WHERE root=? AND status IN ('running','interrupted') ORDER BY started DESC LIMIT 1",
                              (str(Path(root).resolve()),)).fetchone()

    def event(self, kind, **data):
        with self.connect() as db:
            db.execute("INSERT INTO events(run,time,kind,data) VALUES(?,?,?,?)",
                       (self.run_id, time.time(), kind, json.dumps(data, ensure_ascii=False, default=str)))
        if kind == "failure":
            self.has_failures = True

    def remember(self, category, path, outcome):
        path = str(Path(path).resolve())
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO checkpoints VALUES(?,?,?,?,?)",
                       (self.run_id, category, path, json.dumps(fingerprint(path)), outcome))

    def previous(self, category, path):
        if not self.resuming:
            return None
        path = str(Path(path).resolve())
        with self.connect() as db:
            row = db.execute("SELECT fingerprint,outcome FROM checkpoints WHERE run=? AND category=? AND path=?",
                             (self.run_id, category, path)).fetchone()
        if row is None:
            return None
        current = fingerprint(path)
        return row[1] if current is not None and json.loads(row[0]) == current else "file changed since checkpoint"

    def finish(self, completed):
        with self.connect() as db:
            db.execute("UPDATE runs SET status=? WHERE id=?",
                       ("complete" if completed and not self.has_failures else "interrupted", self.run_id))


def history_lines(root, database=None):
    database = Path(database or Path(tempfile.gettempdir()) / "audit_music_batch" / "batch_history.sqlite3")
    if not database.exists():
        return ["No batch history has been recorded."]
    with closing_database(database) as db:
        rows = db.execute("SELECT e.time,e.kind,e.data FROM events e JOIN runs r ON e.run=r.id WHERE r.root=? ORDER BY e.id",
                          (str(Path(root).resolve()),)).fetchall()
    lines = [f"Batch journal: {database}",
             "Recovery: rename destinations back to their recorded sources only when the source is free.",
             "Replacement backups contain prior content; back up the current file before restoring one.",
             "Recycled items must be restored through Windows Recycle Bin; restoration is not automatic.",
             "An intent without a completion means interruption: inspect both paths before recovery."]
    lines.extend(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stamp))} {kind}: {data}" for stamp, kind, data in rows)
    return lines


def monitored_process(command, *, cwd=None, timeout=300, cancel_event=None, on_tick=None):
    """Drain child output continuously; stop the child on timeout or interruption."""
    started = time.monotonic()
    recent = deque(maxlen=8)
    lock = threading.Lock()
    with tempfile.TemporaryFile() as captured:
        process = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        def drain():
            try:
                while True:
                    chunk = process.stdout.read1(4096)
                    if not chunk:
                        break
                    captured.write(chunk)
                    with lock:
                        recent.append(chunk)
            finally:
                process.stdout.close()

        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - started
                with lock:
                    tail = b"".join(recent).decode("utf-8", errors="replace")
                if on_tick:
                    on_tick(elapsed, tail)
                if cancel_event is not None and cancel_event.is_set():
                    raise RuntimeError("Operation cancelled")
                if timeout is not None and elapsed >= timeout:
                    raise TimeoutError(f"Command timed out after {timeout:g}s\n{tail[-3000:]}")
                time.sleep(0.1)
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
        finally:
            reader.join(timeout=5)
        if reader.is_alive():
            raise RuntimeError("Child exited but its output pipe remains open")
        captured.seek(0)
        return subprocess.CompletedProcess(command, process.returncode, captured.read(), None)

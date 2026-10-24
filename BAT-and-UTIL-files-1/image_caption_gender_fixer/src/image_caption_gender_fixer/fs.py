"""Windows file leases, non-overwriting moves, recycling and owned state."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import uuid

from .errors import IntegrityError, UnsafeFilesystem


def windows_path(path):
    value=str(Path(path).absolute())
    if os.name!="nt" or value.startswith("\\\\?\\"): return value
    return "\\\\?\\UNC\\"+value[2:] if value.startswith("\\\\") else "\\\\?\\"+value


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    h = hashlib.sha256()
    if os.name == "nt":
        import msvcrt
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        kernel.CreateFileW.restype = wintypes.HANDLE
        handle = kernel.CreateFileW(windows_path(path), 0x80000000, 7, None, 3, 0, None)
        if handle == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        source_file = os.fdopen(msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY), "rb")
    else:
        source_file = open(path, "rb")
    with source_file as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical(data):
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def numbered(path, number):
    path = Path(path)
    return path.with_name(path.stem + f" ({number})" + path.suffix)


def available(path):
    original = path = Path(path)
    n = 0
    while path.exists():
        n += 1
        path = numbered(original, n)
    return path


def backup_name(path):
    return Path(str(path) + ".bak." + datetime.now().astimezone().strftime("%Y%m%d%H%M") + ".replaced-by-chatgpt.bak")


def archive_name(path):
    return Path(str(path) + ".bak." + datetime.now().astimezone().strftime("%Y%m%d%H%M") + ".undone-by-image-caption-gender-fixer.bak")


def identity(path):
    s = Path(path).stat(follow_symlinks=False)
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def reparse(path):
    s = Path(path).lstat()
    return bool(getattr(s, "st_file_attributes", 0) & 0x400) or stat.S_ISLNK(s.st_mode)


def validate_path(path, root=None):
    path = Path(os.path.abspath(path))
    for part in [path, *path.parents]:
        if part.exists() and reparse(part):
            raise UnsafeFilesystem(f"Reparse-point path refused: {part}")
    if root is not None and path.is_relative_to(Path(root).resolve()):
        raise UnsafeFilesystem("The tool's installation directory is not an image target.")
    return path


def is_network(path):
    path = Path(path)
    if str(path).startswith("\\\\"):
        return True
    if os.name == "nt":
        return ctypes.windll.kernel32.GetDriveTypeW(str(path.anchor)) == 4
    return False


def relative_file(folder, name):
    if not isinstance(name, str) or not name or Path(name).name != name or "/" in name or "\\" in name or ":" in name or name in (".", "..") or name.endswith((" ",".")) or any(ord(c)<32 for c in name):
        raise IntegrityError("Unsafe filename in history/journal.")
    result = Path(folder) / name
    if result.exists() and reparse(result):
        raise UnsafeFilesystem("History reference is a reparse point.")
    return result


def hide(path, enabled=True):
    if os.name != "nt":
        return
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
    kernel.GetFileAttributesW.restype = wintypes.DWORD
    kernel.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
    attributes = kernel.GetFileAttributesW(windows_path(path))
    if attributes == 0xffffffff or not kernel.SetFileAttributesW(windows_path(path), (attributes | 2) if enabled else (attributes & ~2)):
        raise UnsafeFilesystem("Could not set required Windows Hidden attribute.")


def move(source, destination):
    source, destination = Path(source), Path(destination)
    expected = sha256(source)
    if destination.exists():
        raise UnsafeFilesystem(f"Destination is occupied: {destination}")
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.MoveFileExW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
        if not kernel.MoveFileExW(windows_path(source), windows_path(destination), 8):
            raise ctypes.WinError(ctypes.get_last_error())
    else:
        # Windows is the supported production platform. Never use POSIX rename
        # where it could silently replace a file created after the check.
        raise UnsafeFilesystem("Non-overwriting image moves require Windows.")
    if source.exists() or not destination.is_file() or sha256(destination) != expected:
        raise IntegrityError("Move verification failed; retain files for recovery.")
    return destination


def recycle(path):
    path = Path(path).absolute()
    if not path.exists():
        return True
    if os.name != "nt":
        raise UnsafeFilesystem("Windows Recycle Bin is unavailable; item retained.")
    # IFileOperation's RECYCLEONDELETE flag explicitly requests recycling.
    # Do not use SHFileOperation/FOF_ALLOWUNDO, which can silently delete.
    if is_network(path) or ctypes.windll.kernel32.GetDriveTypeW(str(path.anchor)) != 3:
        raise UnsafeFilesystem("Recycle Bin support is not established; item retained.")
    class GUID(ctypes.Structure):
        _fields_ = [("bytes", ctypes.c_ubyte * 16)]
        def __init__(self, text):
            super().__init__()
            self.bytes[:] = uuid.UUID(text).bytes_le
    def method(pointer, index, result, *arguments):
        address = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents[index]
        return ctypes.WINFUNCTYPE(result, ctypes.c_void_p, *arguments)(address)
    def check(code):
        if code < 0:
            raise UnsafeFilesystem(f"Recycle operation failed (HRESULT {code & 0xffffffff:08x}); no delete fallback.")
    ole = ctypes.OleDLL("ole32")
    initialized = ole.CoInitializeEx(None, 2)
    operation, item = ctypes.c_void_p(), ctypes.c_void_p()
    try:
        check(ole.CoCreateInstance(ctypes.byref(GUID("3ad05575-8857-4850-9277-11b85bdb8e09")), None, 1,
                                  ctypes.byref(GUID("947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8")), ctypes.byref(operation)))
        shell = ctypes.WinDLL("shell32")
        shell.SHCreateItemFromParsingName.argtypes = [wintypes.LPCWSTR, ctypes.c_void_p, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p)]
        check(shell.SHCreateItemFromParsingName(str(path), None, ctypes.byref(GUID("43826d1e-e718-42ee-bc55-a1e261c37bfe")), ctypes.byref(item)))
        flags = 0x00080000 | 0x00100000 | 0x20000000 | 0x40 | 0x10 | 0x4 | 0x400
        check(method(operation, 5, ctypes.c_long, wintypes.DWORD)(operation, flags))
        check(method(operation, 18, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p)(operation, item, None))
        check(method(operation, 21, ctypes.c_long)(operation))
        aborted = wintypes.BOOL()
        check(method(operation, 22, ctypes.c_long, ctypes.POINTER(wintypes.BOOL))(operation, ctypes.byref(aborted)))
        if aborted.value or path.exists():
            raise UnsafeFilesystem("Recycling was aborted or incomplete; file retained.")
        return True
    finally:
        if item:
            method(item, 2, wintypes.ULONG)(item)
        if operation:
            method(operation, 2, wintypes.ULONG)(operation)
        if initialized in (0, 1):
            ole.CoUninitialize()


def state_write(path, value):
    """Replace only a validated application-owned state file, never an image."""
    path = Path(path)
    validate_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(old,dict) or old.get("application") != "icgf" or old.get("schema")!=1:
            raise IntegrityError("Refusing to overwrite unrelated state.")
    value = dict(value, application="icgf", schema=1)
    stage = path.with_name(".icgf-state-" + uuid.uuid4().hex + ".json")
    with stage.open("x", encoding="utf-8", newline="\n") as f:
        f.write(canonical(value) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(stage, path)


def state_read(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict) or value.get("application") != "icgf" or value.get("schema") != 1:
        raise IntegrityError("Unrecognized state schema.")
    return value


@contextmanager
def source_lease(path):
    if os.name != "nt":
        raise UnsafeFilesystem("Windows file leasing is required.")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    # Read and delete access; share read/delete, but exclude concurrent writers.
    handle = kernel.CreateFileW(windows_path(path), 0x80000000 | 0x10000, 1 | 4, None, 3, 0, None)
    if handle == wintypes.HANDLE(-1).value:
        raise UnsafeFilesystem(f"Cannot exclusively protect source from writes: {ctypes.WinError(ctypes.get_last_error())}")
    try:
        yield
    finally:
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle(handle)


@contextmanager
def folder_lock(folder):
    """OS-released byte-range lock; no stale PID files need deleting."""
    import msvcrt
    path = Path(folder) / ".icgf.lock"
    signature = b"ICGF LOCK v1\n"
    try:
        with path.open("xb") as created:
            created.write(signature)
            created.flush()
            os.fsync(created.fileno())
        hide(path)
    except FileExistsError:
        pass
    with path.open("r+b") as handle:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise UnsafeFilesystem("Another instance holds the folder lock.") from error
        try:
            if handle.read() != signature:
                raise IntegrityError("Unrelated file occupies the folder lock name.")
            yield
        finally:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def capacity(folder, bytes_needed):
    if shutil.disk_usage(folder).free < bytes_needed + 1024 * 1024:
        raise UnsafeFilesystem("Insufficient space for staging and recoverable commit.")

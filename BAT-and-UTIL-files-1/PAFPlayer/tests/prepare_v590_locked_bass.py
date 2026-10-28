"""Apply the reviewed locked-bass repair with verified replacement backups."""
from pathlib import Path
import hashlib
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'monkeymote/research'))
from edit_v568 import write

path = root / 'PAFPlayer.py'
assert hashlib.sha256(path.read_bytes()).hexdigest() == '1cf296273e10a999c30fc885e96968ec53cfd66ae014550d38a4741137063fd8', 'Source changed; re-inspect before editing'
source = path.read_text(encoding='utf-8')
start = source.index('def windows_session_is_locked()')
end = source.index('\ndef bass_adjustment_db(', start)
replacement = '''def _windows_wts_session_is_locked() -> bool | None:
    """Read the calling session's documented lock flag; never switch desktops."""
    from ctypes import wintypes

    class Level1(ctypes.Structure):
        _fields_ = [
            ("SessionId", wintypes.ULONG), ("SessionState", ctypes.c_int),
            ("SessionFlags", wintypes.LONG),
            ("WinStationName", wintypes.WCHAR * 33),
            ("UserName", wintypes.WCHAR * 21), ("DomainName", wintypes.WCHAR * 18),
            *[(name, ctypes.c_longlong) for name in
              ("LogonTime", "ConnectTime", "DisconnectTime", "LastInputTime", "CurrentTime")],
            *[(name, wintypes.DWORD) for name in
              ("IncomingBytes", "OutgoingBytes", "IncomingFrames", "OutgoingFrames",
               "IncomingCompressedBytes", "OutgoingCompressedBytes")],
        ]

    class Data(ctypes.Union):
        _fields_ = [("Level1", Level1)]

    class Info(ctypes.Structure):
        _fields_ = [("Level", wintypes.DWORD), ("Data", Data)]

    # Private wrappers keep pointer widths and error capture independent of the
    # tray, Tk, and other libraries that also call these Windows APIs.
    wts = ctypes.WinDLL("wtsapi32", use_last_error=True)
    query = wts.WTSQuerySessionInformationW
    query.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_int,
                     ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
    query.restype = wintypes.BOOL
    wts.WTSFreeMemory.argtypes = [ctypes.c_void_p]
    wts.WTSFreeMemory.restype = None
    buffer = ctypes.c_void_p()
    count = wintypes.DWORD()
    try:
        # Local server, this process's session, WTSSessionInfoEx (25).
        if not query(None, 0xffffffff, 25, ctypes.byref(buffer), ctypes.byref(count)):
            return None
        if not buffer.value or count.value < ctypes.sizeof(Info):
            return None
        info = ctypes.cast(buffer, ctypes.POINTER(Info)).contents
        if info.Level != 1 or info.Data.Level1.SessionFlags not in (0, 1):
            return None
        locked = info.Data.Level1.SessionFlags == 0
        version = sys.getwindowsversion()
        # Microsoft documents reversed flags on Windows 7 / Server 2008 R2.
        return not locked if (version.major, version.minor) == (6, 1) else locked
    finally:
        if buffer.value:
            wts.WTSFreeMemory(buffer)


def _windows_input_desktop_is_locked() -> bool:
    """Fallback when session services are unavailable; query the desktop only."""
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user32.OpenInputDesktop.restype = wintypes.HANDLE
    user32.GetUserObjectInformationW.argtypes = [
        wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetUserObjectInformationW.restype = wintypes.BOOL
    user32.CloseDesktop.argtypes = [wintypes.HANDLE]
    user32.CloseDesktop.restype = wintypes.BOOL
    ctypes.set_last_error(0)
    desktop = user32.OpenInputDesktop(0, False, 0x0001)  # DESKTOP_READOBJECTS
    if not desktop:
        return ctypes.get_last_error() == 5  # ERROR_ACCESS_DENIED on secure input desktop
    try:
        name = ctypes.create_unicode_buffer(256)
        needed = wintypes.DWORD()
        if not user32.GetUserObjectInformationW(desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed)):
            return False
        return name.value.casefold() == "winlogon"
    finally:
        user32.CloseDesktop(desktop)


def windows_session_is_locked() -> bool:
    """Best-effort, read-only Windows session check; failures never block audio."""
    if os.name != "nt":
        return False
    try:
        locked = _windows_wts_session_is_locked()
        if locked is not None:
            return locked
    except Exception:
        pass
    try:
        return _windows_input_desktop_is_locked()
    except Exception:
        return False


'''
source = source[:start] + replacement + source[end + 1:]
before = '''                        position = displayed_position
                        stop_process(process)
                        continue
                    last_bass_lock_state = locked_now'''
after = '''                        position = displayed_position
                        stop_process(process)
                        # Leave the inner polling loop to rebuild this segment.
                        # Continuing it would fall into its natural-EOF else and
                        # incorrectly advance to the next song.
                        break
                    last_bass_lock_state = locked_now'''
assert source.count(before) == 1
source = source.replace(before, after, 1)
before = '''                    bass_filter_changed = last_bass_filter_signature is not None and bass_filter_signature != last_bass_filter_signature
                    last_bass_filter_signature = bass_filter_signature'''
after = '''                    bass_filter_changed = last_bass_filter_signature is not None and bass_filter_signature != last_bass_filter_signature
                    if web_server is not None and (locked_now != last_bass_lock_state or bass_filter_signature != last_bass_filter_signature):
                        web_server.update_fields(session_locked=locked_now, bass_effective_db=bass_filter_signature)
                    last_bass_filter_signature = bass_filter_signature'''
assert source.count(before) == 1
source = source.replace(before, after, 1)
source = source.replace('"locked_bass_reduction_percent": 50,', '"locked_bass_reduction_percent": 50,\n            "session_locked": None,\n            "bass_effective_db": None,', 1)
assert "PROGRAM_VERSION                = 'V589'" in source
source = source.replace("PROGRAM_VERSION                = 'V589'", "PROGRAM_VERSION                = 'V590'", 1)
source = source.replace("PROGRAM_RELEASE_LABEL          = 'V589'", "PROGRAM_RELEASE_LABEL          = 'V590'", 1)
lines = source.splitlines(keepends=True)
for i, line in enumerate(lines):
    if line.startswith('PLAYER_BUILD_ID '):
        lines[i] = "PLAYER_BUILD_ID                = '2026-10-20-v590-locked-bass-session-detection'\n"
source = ''.join(lines)
compile(source, str(path), 'exec')
write('PAFPlayer.py', source)

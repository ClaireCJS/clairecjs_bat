"""Console-local artwork shortcuts; no global hotkeys or keyboard hook."""
from collections import deque
from functools import lru_cache
import os

SHOW_ART='\x1b[icgf-art]'
FRONT_ART='\x1b[icgf-front]'
_pending=deque()


def decode_key(down,key,character,modifiers):
    if not down:return None
    if key==0x41 and modifiers&0x0c:
        return FRONT_ART if modifiers&3 else SHOW_ART
    return character if character and character!='\x00' else None


@lru_cache(maxsize=1)
def native_console():
    import ctypes
    from ctypes import wintypes as w
    class Character(ctypes.Union):_fields_=[('UnicodeChar',w.WCHAR),('AsciiChar',ctypes.c_char)]
    class Key(ctypes.Structure):
        _fields_=[('down',w.BOOL),('repeat',w.WORD),('key',w.WORD),('scan',w.WORD),('char',Character),('modifiers',w.DWORD)]
    class Event(ctypes.Union):_fields_=[('key',Key),('padding',ctypes.c_byte*16)]
    class Record(ctypes.Structure):_fields_=[('kind',w.WORD),('event',Event)]
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    api.GetStdHandle.argtypes=[w.DWORD];api.GetStdHandle.restype=w.HANDLE
    api.GetConsoleMode.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];api.GetConsoleMode.restype=w.BOOL
    api.GetNumberOfConsoleInputEvents.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)];api.GetNumberOfConsoleInputEvents.restype=w.BOOL
    api.ReadConsoleInputW.argtypes=[w.HANDLE,ctypes.POINTER(Record),w.DWORD,ctypes.POINTER(w.DWORD)];api.ReadConsoleInputW.restype=w.BOOL
    handle=api.GetStdHandle(-10);mode=w.DWORD()
    if not api.GetConsoleMode(handle,ctypes.byref(mode)):return None
    return api,handle,Record


def read_key():
    if _pending:return _pending.popleft()
    if os.name!='nt':return None
    import ctypes,msvcrt
    from ctypes import wintypes
    native=native_console()
    if native:
        api,handle,Record=native
        for _ in range(32):
            count=wintypes.DWORD()
            if not api.GetNumberOfConsoleInputEvents(handle,ctypes.byref(count)) or not count.value:return None
            record=Record();read=wintypes.DWORD()
            if not api.ReadConsoleInputW(handle,ctypes.byref(record),1,ctypes.byref(read)):break
            if record.kind!=1:continue
            event=record.event.key
            value=decode_key(event.down,event.key,event.char.UnicodeChar,event.modifiers)
            if value is not None:
                _pending.extend([value]*max(0,min(100,event.repeat)-1));return value
        return None
    if not msvcrt.kbhit():return None
    key=msvcrt.getwch()
    api=ctypes.windll.user32;ctrl=api.GetKeyState(0x11)&0x8000;alt=api.GetKeyState(0x12)&0x8000
    if key in ('\x00','\xe0'):
        scan=msvcrt.getwch()
        return FRONT_ART if scan=='\x1e' and ctrl and alt else None
    if key=='\x01' or ctrl and key in ('a','A'):return FRONT_ART if alt else SHOW_ART
    return key


def artwork_shortcut(app,key):
    if key not in (SHOW_ART,FRONT_ART):return False
    app.reopen_artwork(activate=key==FRONT_ART)
    return True

"""Read-only, bounded Windows lock/unlock trace. Never locks or changes settings."""
import ast
import ctypes
from functools import lru_cache
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[1]
names = {'_windows_wts_lock_api', '_windows_desktop_lock_api', '_windows_wts_session_is_locked', '_windows_input_desktop_is_locked', 'windows_session_is_locked'}
tree = ast.parse((root / 'PAFPlayer.py').read_text(encoding='utf-8'))
ns = dict(ctypes=ctypes, sys=sys, os=os, lru_cache=lru_cache)
exec(compile(ast.Module([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[]), '<lock-check-only>', 'exec'), ns)
report = root / 'tests/reports' / ('v590-native-lock-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.jsonl')
duration = float(sys.argv[1]) if len(sys.argv) > 1 else 240
print('TRACE READY', report, flush=True)
with report.open('x', encoding='utf-8') as output:
    end = time.monotonic() + duration
    previous = None
    while time.monotonic() < end:
        # Reproduce the old error capture, without its desktop-switch call.
        old = ctypes.WinDLL('user32')
        old.OpenInputDesktop.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        old.OpenInputDesktop.restype = ctypes.c_void_p
        old.CloseDesktop.argtypes = [ctypes.c_void_p]
        ctypes.set_last_error(0)
        desktop = old.OpenInputDesktop(0, False, 0x0100)
        stale_error = ctypes.get_last_error()
        os_error = ctypes.GetLastError()
        if desktop:
            old.CloseDesktop(desktop)
        wts = ns['_windows_wts_session_is_locked']()
        result = {'at': datetime.now().astimezone().isoformat(), 'wts_locked': wts,
                  'detected_locked': ns['windows_session_is_locked'](),
                  'fallback_locked': ns['_windows_input_desktop_is_locked'](),
                  'old_open_succeeded': bool(desktop), 'old_ctypes_error': stale_error,
                  'old_actual_windows_error': os_error if not desktop else None}
        output.write(json.dumps(result) + '\n'); output.flush()
        signature = tuple(result[k] for k in result if k != 'at')
        if signature != previous:
            print(json.dumps(result), flush=True)
            previous = signature
        time.sleep(.5)
print('TRACE COMPLETE', report, flush=True)

"""Bounded, read-only renderer observation; never locks/unlocks Windows.

Collects public WTS lock state, renderer process presence and Windows ETW.
The caller/user performs the lock cycle. No notification/settings/cache writes.
"""
import argparse
import ctypes
from ctypes import wintypes as w
import datetime as dt
import json
from pathlib import Path
import subprocess
import time
import uuid
import psutil

ROOT = Path(__file__).resolve().parents[1]
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
wts = ctypes.WinDLL('wtsapi32', use_last_error=True)
kernel.WTSGetActiveConsoleSessionId.restype = w.DWORD
wts.WTSQuerySessionInformationW.argtypes = [w.HANDLE, w.DWORD, ctypes.c_int,
    ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(w.DWORD)]
wts.WTSQuerySessionInformationW.restype = w.BOOL
wts.WTSFreeMemory.argtypes = [ctypes.c_void_p]
session = kernel.WTSGetActiveConsoleSessionId()

def lock_state():
    pointer, length = ctypes.c_void_p(), w.DWORD()
    if not wts.WTSQuerySessionInformationW(None, session, 25,
            ctypes.byref(pointer), ctypes.byref(length)):
        return {'error': ctypes.get_last_error()}
    try:
        # WTSINFOEXW: DWORD Level, aligned WTSINFOEX_LEVEL1_W union.
        if length.value < 20:
            return {'error': 'short WTSINFOEX', 'length': length.value}
        data = ctypes.string_at(pointer, 20)
        level = int.from_bytes(data[:4], 'little')
        return {'level': level, 'session': int.from_bytes(data[8:12], 'little'),
            'connection_state': int.from_bytes(data[12:16], 'little'),
            'flags': int.from_bytes(data[16:20], 'little')}
    finally:
        wts.WTSFreeMemory(pointer)

def processes():
    selected = []
    for process in psutil.process_iter(['pid', 'name']):
        if (process.info['name'] or '').lower() in (
                'lockapp.exe', 'logonui.exe', 'pafplayerlockscreen.exe'):
            sid = w.DWORD()
            kernel.ProcessIdToSessionId(process.pid, ctypes.byref(sid))
            selected.append(dict(process.info, session=sid.value))
    return sorted(selected, key=lambda item: item['pid'])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait-hours', type=float, default=0.25,
        help='Maximum time to wait for a user lock/unlock cycle (up to 24 hours).')
    options = parser.parse_args()
    if not 0 < options.wait_hours <= 24:
        parser.error('--wait-hours must be greater than zero and at most 24')
    suffix = dt.datetime.now().strftime('%Y%m%d%H%M%S') + '-' + uuid.uuid4().hex[:6]
    base = ROOT / 'tests' / 'reports' / ('lock-renderer-' + suffix)
    trace = 'PAFLockRenderer-' + suffix
    logman = str(Path(r'C:\Windows\System32\logman.exe'))
    command = [logman, 'create', 'trace', trace, '-ow', '-o', str(base) + '.etl',
        '-f', 'bincirc', '-max', '32', '-bs', '64', '-nb', '16', '64']
    providers = ('Microsoft-Windows-Shell-LockScreenContent',
            '{3D14CA27-6EB2-4789-9B52-33EC88ECF5B0}',
            # TraceLogging provider GUIDs from the installed Microsoft binaries:
            # LockController, LockHostingFramework and LogonController.
            '{2D710779-B24B-4ADB-81EF-CD6DED5A9B2A}',
            '{74CC4A0B-F577-5929-ABCB-AA4BEA374CB3}',
            '{4F7C073A-65BF-5045-7651-CC53BB272DB5}',
            '{75816B5C-ECD1-4DBC-B38A-47A9646E60BE}',
            'Microsoft-Windows-PushNotifications-Platform',
            'Microsoft-Windows-Winlogon', 'Microsoft-Windows-Immersive-Shell')
    command += ['-p', providers[0], '0xffffffffffffffff', '5', '-ets']
    result = subprocess.run(command, capture_output=True, text=True)
    with base.with_suffix('.jsonl').open('x', encoding='utf-8') as report:
        def write(value):
            report.write(json.dumps(dict(time=dt.datetime.now().astimezone().isoformat(), **value)) + '\n')
            report.flush()
        write({'event': 'start', 'trace': trace, 'etl_started': result.returncode == 0,
            'logman': result.stdout + result.stderr, 'session': session})
        if result.returncode == 0:
            for provider in providers[1:]:
                added = subprocess.run([logman, 'update', 'trace', trace, '-p', provider,
                    '0xffffffffffffffff', '5', '-ets'], capture_output=True, text=True)
                write({'event': 'provider', 'provider': provider, 'code': added.returncode,
                    'logman': added.stdout + added.stderr})
        print(json.dumps({'report': str(base.with_suffix('.jsonl')),
            'etl_started': result.returncode == 0, 'initial': lock_state(),
            'wait_hours': options.wait_hours}), flush=True)
        previous = None
        previous_state = None
        selected_processes = []
        saw_lock = False
        end_after = None
        deadline = time.monotonic() + options.wait_hours * 3600
        try:
            while time.monotonic() < deadline:
                state = lock_state()
                # Waiting for the user should be cheap: enumerate processes only
                # on a state transition or while locked. ETW's bounded circular
                # buffer remains active so it includes activation BEFORE WTS
                # reports the lock, rather than missing that important interval.
                if state != previous_state or state.get('flags') == 0:
                    selected_processes = processes()
                previous_state = state
                snapshot = {'wts': state, 'processes': selected_processes}
                if snapshot != previous:
                    write(snapshot)
                    print(json.dumps(snapshot), flush=True)
                    previous = snapshot
                if state.get('flags') == 0:
                    saw_lock = True
                elif saw_lock and state.get('flags') == 1 and end_after is None:
                    end_after = time.monotonic() + 5
                if end_after is not None and time.monotonic() >= end_after:
                    break
                time.sleep(1)
        finally:
            if result.returncode == 0:
                stopped = subprocess.run([logman, 'stop', trace, '-ets'], capture_output=True, text=True)
                write({'event': 'stop', 'saw_lock': saw_lock, 'stop_code': stopped.returncode,
                    'logman': stopped.stdout + stopped.stderr})
            print(str(base), flush=True)

if __name__ == '__main__':
    main()

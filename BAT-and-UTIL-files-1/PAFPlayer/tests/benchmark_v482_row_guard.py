"""Isolated A/B diagnostic; no audio, preferences, or player source changes.

Compare the pre-V482 row prefix with the V482 prefix using the same renderer.
Native replay uses a separate hidden legacy console, NOT Windows Terminal.
"""
import sys
sys.dont_write_bytecode = True
import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import time
from unittest import mock
import probe_v482_track_renderer as probe


def frames(guard):
    local, namespace = probe.capture_renderer(170, 45)
    show = local['show_status']
    cells = dict(zip(show.__code__.co_freevars, show.__closure__))
    cells['drcs_timeline'].cell_contents = (bytes((i * 17 % 255 for i in range(12*40*50))), 12, 40)
    cells['spectrum_analysis_columns'].cell_contents = 12
    for cell in cells.values():
        try:
            cell.cell_contents
        except ValueError:
            cell.cell_contents = False
    original = namespace['fixed_console_row_sequence']
    if not guard:
        def old_sequence(origin, row, *, line_rendition=True):
            return '\x1b(B' + namespace['absolute_viewport_cursor_sequence'](origin, row) + (namespace['BIG_OFF'] if line_rendition else '')
        namespace['fixed_console_row_sequence'] = old_sequence
    writes = []
    namespace['write_console'] = writes.append
    output = []
    timings = []
    with mock.patch.object(probe.app.shutil, 'get_terminal_size', return_value=os.terminal_size((170,45))):
        for tick in range(25*30, 33*30):
            writes.clear()
            start = time.perf_counter()
            show(tick/30, '▶️')
            local['render_metadata_rows'](tick/30)
            timings.append((time.perf_counter()-start)*1000)
            output.append(''.join(writes))
    return output, timings


def native():
    import msvcrt
    payloads = json.loads(sys.stdin.read())
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    stream = open('CONOUT$', 'w', encoding='utf-8')
    assert kernel.SetConsoleMode(msvcrt.get_osfhandle(stream.fileno()), 7)
    results = []
    with mock.patch.object(probe.app.sys, 'stdout', stream):
        for trial in range(8):
            guard = (trial % 4 in (1,2))
            data = payloads['new' if guard else 'old'][20:44]
            probe.app.write_console('\x1b[0m\x1b[?7h\x1b[2J\x1b[H')
            start = time.perf_counter()
            for text in data:
                probe.app.write_console(text)
            results.append({'guard':guard, 'ms_per_frame':(time.perf_counter()-start)*1000/len(data)})
    stream.close()
    print(json.dumps(results))


def main():
    results = []
    payloads = {}
    for guard in (False, True, True, False):
        output, times = frames(guard)
        payloads['new' if guard else 'old'] = output
        results.append(dict(guard=guard, mean_ms=statistics.mean(times[20:]),
                            median_ms=statistics.median(times[20:]),
                            chars=sum(map(len,output)), frames=len(output),
                            guards=sum(s.count('\x1b[?7l') for s in output)))
    print(json.dumps({'generation':results}), flush=True)
    # Removing JUST the new row prefix reproduces exactly the old bytes.
    old, new = payloads['old'], payloads['new']
    print(json.dumps({'median_frame_chars':statistics.median(map(len,new))}), flush=True)
    # Native transport test uses identical captured new frames, differing only
    # in the row guard; unrelated pre-existing no-wrap sequences stay intact.
    payloads['old'] = [s.replace('\x1b[?7l\x1b(B', '\x1b(B') for s in new]
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    completed = subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--native'],
        input=json.dumps(payloads), capture_output=True, text=True, timeout=90,
        startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE)
    print(json.dumps({'native_exit':completed.returncode,'native':completed.stdout,'stderr':completed.stderr}), flush=True)


if __name__ == '__main__':
    if '--native' in sys.argv:
        native()
    else:
        main()

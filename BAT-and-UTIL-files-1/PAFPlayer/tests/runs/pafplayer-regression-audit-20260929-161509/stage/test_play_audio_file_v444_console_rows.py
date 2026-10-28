"""Verify the isolated V427 console-row repair; no playback or settings writes."""
import ast
import ctypes
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

import play_audio_file as p

BASELINE = Path(__file__).with_name('play_audio_file_v427_attribute_trailing_alternation.py')


class _WindowsConsoleIO:
    pass


class ConsoleStream:
    def __init__(self):
        self.buffer = type('Buffer', (), {'raw': _WindowsConsoleIO()})()
        self.writes = []
        self.flushes = 0

    def fileno(self):
        return 1

    def write(self, text):
        self.writes.append(text)
        return len(text)

    def flush(self):
        self.flushes += 1


class ConsoleRowRepair(unittest.TestCase):
    def test_entire_v427_program_is_unchanged_outside_console_writer_and_version(self):
        allowed_functions = {'write_console', '_windows_console_text_api', '_write_large_windows_console_text'}
        allowed_constants = {'PLAYER_BUILD_ID', 'PROGRAM_VERSION', 'PROGRAM_RELEASE_LABEL'}

        def unchanged_program(path):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            tree.body = [node for node in tree.body if not (
                isinstance(node, ast.FunctionDef) and node.name in allowed_functions
                or isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in allowed_constants for t in node.targets)
            )]
            return ast.dump(tree)
        self.assertEqual(unchanged_program(BASELINE), unchanged_program(Path(p.__file__)))

    def test_short_and_ascii_payloads_keep_v427_write_path(self):
        for text in ('small ▌ frame', 'A' * 30000):
            stream = ConsoleStream()
            with mock.patch.object(p.sys, 'stdout', stream), mock.patch.object(p, '_write_large_windows_console_text') as native:
                p.write_console(text)
            native.assert_not_called()
            self.assertEqual([text], stream.writes)
            self.assertEqual(1, stream.flushes)

    def test_redirected_unicode_stays_in_the_supplied_stream(self):
        stream = io.StringIO()
        text = 'A' * 15000 + '▌' + 'B' * 14999
        with mock.patch.object(p.sys, 'stdout', stream):
            p.write_console(text)
        self.assertEqual(text, stream.getvalue())

    def test_native_payload_keeps_all_vt_sequences_and_cursor_marker_under_lock(self):
        text = '\x1b[?2026h\x1bP' + 'q' * 4159 + '\x1b\\\x1b( @' + '▌' * 6000 + '\x1b(B\x1b[?2026l'
        stream = ConsoleStream()
        captured = []
        def native(output, payload):
            self.assertTrue(p._CONSOLE_WRITE_LOCK._is_owned())
            self.assertIs(output, stream)
            captured.append(payload)
            return True
        with mock.patch.object(p.sys, 'stdout', stream), mock.patch.object(p, '_write_large_windows_console_text', side_effect=native), mock.patch.object(p, '_CURSOR_SUPPRESSION_ACTIVE', True), mock.patch.object(p, '_CURSOR_HIDE_APPEND_ENABLED', True):
            p.write_console(text)
        self.assertEqual([text + '\x1b[?25l'], captured)
        self.assertEqual([], stream.writes)

    @unittest.skipUnless(os.name == 'nt', 'Windows UTF-16 API')
    def test_native_partial_writes_count_utf16_units(self):
        captured = bytearray()
        class Kernel:
            def GetConsoleMode(self, handle, mode):
                return True
            def WriteConsoleW(self, handle, pointer, units, written, reserved):
                count = min(17, units)
                captured.extend(ctypes.string_at(pointer, count * 2))
                written._obj.value = count
                return True
        text = '▌😀abc' * 1500
        stream = ConsoleStream()
        with mock.patch('msvcrt.get_osfhandle', return_value=123), mock.patch.object(p, '_windows_console_text_api', return_value=Kernel()):
            self.assertTrue(p._write_large_windows_console_text(stream, text))
        self.assertEqual(text.encode('utf-16-le'), captured)
        self.assertEqual(1, stream.flushes)

    @unittest.skipUnless(os.name == 'nt', 'Windows UTF-16 API')
    def test_native_failure_does_not_replay_a_prefix(self):
        class Kernel:
            calls = 0
            def GetConsoleMode(self, handle, mode):
                return True
            def WriteConsoleW(self, handle, pointer, units, written, reserved):
                self.calls += 1
                if self.calls == 1:
                    written._obj.value = 3
                    return True
                return False
        stream = ConsoleStream()
        with mock.patch.object(p.sys, 'stdout', stream), mock.patch('msvcrt.get_osfhandle', return_value=123), mock.patch.object(p, '_windows_console_text_api', return_value=Kernel()):
            with self.assertRaises(OSError):
                p.write_console('▌' * 5000)
        self.assertEqual([], stream.writes)

    @unittest.skipUnless(os.name == 'nt', 'Real Windows private console')
    def test_private_console_characters_cursor_and_ansi_rows(self):
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        result = subprocess.run(
            [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--native-child'],
            startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE,
            capture_output=True, text=True, timeout=25,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        results = json.loads(result.stdout)
        for check in results['fixed']:
            self.assertTrue(check['exact'], check)
            self.assertTrue(check['cursor_exact'], check)
            self.assertEqual(0, check['replacements'], check)
        self.assertTrue(results['ansi_rows_exact'])
        print(json.dumps(results))


def native_child():
    import msvcrt
    from ctypes import wintypes
    kernel = p._windows_console_text_api()
    class Coord(ctypes.Structure):
        _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]
    class Rect(ctypes.Structure):
        _fields_ = [(name, ctypes.c_short) for name in ('Left', 'Top', 'Right', 'Bottom')]
    class Info(ctypes.Structure):
        _fields_ = [('size', Coord), ('cursor', Coord), ('attributes', wintypes.WORD), ('window', Rect), ('maximum', Coord)]
    kernel.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, Coord]
    kernel.SetConsoleCursorPosition.argtypes = [wintypes.HANDLE, Coord]
    kernel.GetConsoleScreenBufferInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Info)]
    kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.ReadConsoleOutputCharacterW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, Coord, ctypes.POINTER(wintypes.DWORD)]
    stream = open('CONOUT$', 'w', encoding='utf-8')
    handle = msvcrt.get_osfhandle(stream.fileno())
    assert kernel.SetConsoleScreenBufferSize(handle, Coord(200, 1000))
    mode = wintypes.DWORD()
    assert kernel.GetConsoleMode(handle, ctypes.byref(mode))
    assert kernel.SetConsoleMode(handle, mode.value | 4)
    def read(count, x=0, y=0):
        buffer = ctypes.create_unicode_buffer(count + 1)
        written = wintypes.DWORD()
        assert kernel.ReadConsoleOutputCharacterW(handle, buffer, count, Coord(x, y), ctypes.byref(written))
        return buffer[:count]
    old_tree = ast.parse(BASELINE.read_text(encoding='utf-8'))
    old_write = next(node for node in old_tree.body if isinstance(node, ast.FunctionDef) and node.name == 'write_console')
    namespace = dict(vars(p))
    exec(compile(ast.Module(body=[old_write], type_ignores=[]), '<V427 writer>', 'exec'), namespace)
    text = 'A' * 15000 + '▌' + 'B' * 14999
    assert kernel.SetConsoleCursorPosition(handle, Coord(0, 0))
    with mock.patch.object(p.sys, 'stdout', stream):
        namespace['write_console'](text)
    original = read(len(text))
    results = dict(baseline=dict(exact=original == text, replacements=original.count('\ufffd')), fixed=[])
    for size in (30000, 40002, 120000):
        text = 'A' * 15000 + '▌' + 'B' * (size - 15001)
        assert kernel.SetConsoleCursorPosition(handle, Coord(0, 0))
        with mock.patch.object(p.sys, 'stdout', stream):
            p.write_console(text)
        actual = read(size)
        # Force any VT wrap-pending state to resolve. The following printable
        # cell must land immediately after the original payload, not shifted.
        with mock.patch.object(p.sys, 'stdout', stream):
            p.write_console('Z')
        info = Info()
        assert kernel.GetConsoleScreenBufferInfo(handle, ctypes.byref(info))
        aligned = (info.cursor.X, info.cursor.Y) == ((size + 1) % 200, (size + 1) // 200)
        aligned = aligned and read(1, size % 200, size // 200) == 'Z'
        results['fixed'].append(dict(size=size, exact=actual == text, replacements=actual.count('\ufffd'), cursor_exact=aligned))
    # CUP is viewport-relative: return the hidden viewport to the buffer top,
    # then use a dozen rows so the test never clips CUP at its bottom margin.
    assert kernel.SetConsoleCursorPosition(handle, Coord(0, 0))
    rows = [('▌▐█' * 46) + 'AB' for _ in range(12)]
    color = '\x1b[38;2;0;128;255;48;2;64;0;32m'
    text = '\x1b[?2026h' + ''.join(f'\x1b[{index + 1};1H' + ''.join(color + glyph for glyph in row) for index, row in enumerate(rows)) + '\x1b[0m\x1b[?2026l'
    with mock.patch.object(p.sys, 'stdout', stream):
        p.write_console(text)
    results['ansi_rows_exact'] = all(read(140, 0, index) == row for index, row in enumerate(rows))
    stream.close()
    print(json.dumps(results))


if __name__ == '__main__':
    if '--native-child' in sys.argv:
        native_child()
    else:
        unittest.main()

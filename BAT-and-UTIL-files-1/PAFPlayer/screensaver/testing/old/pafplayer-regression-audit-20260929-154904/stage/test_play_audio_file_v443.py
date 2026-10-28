"""V443 cell-equivalence, native console safety, and moving-frame benchmarks.

Run with python -B -X utf8 test_play_audio_file_v443.py [--benchmark].
The native check uses a separate hidden console; no playback/settings changes.
"""
import ctypes
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import re
import statistics
import subprocess
import sys
import time
import unittest
from unittest import mock

import play_audio_file as p


def reference():
    name = 'paf_v442_reference'
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name('play_audio_file_v442_scheduled_console_overlay_painting.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixture(width=24, rows=32):
    return dict(
        columns=width, rows=rows, granularity=2, truncate_top_lines=0,
        spectrum_levels=bytes((i * 37) % 256 for i in range(width * 2)),
        height_override=[.5 + .49 * math.sin(i * .07) for i in range(width * 2)],
        recent_energy=[((i * 17) % 100) / 100 for i in range(width * 2)],
        processing_style=62,
        artwork_color_grid=tuple(tuple(((x // 4 * 7 + y * 3) % 256, (x // 4 * 11 + y * 5) % 256, (x // 4 * 13 + y * 7) % 256) for x in range(width * 2)) for y in range(rows)),
        artwork_bar_strength=1., artwork_bar_blend_mode=1,
        artwork_bar_opacity=.64, artwork_background_strength=.3,
    )


def cells(row):
    """Decode SGR into visible cells, independently of renderer string layout."""
    fg = bg = None
    result = []
    for token in re.findall(r'\x1b\[[0-9;]*[mK]|[^\x1b]', row):
        if token.startswith('\x1b['):
            if token.endswith('K'):
                continue
            params = [int(x or 0) for x in token[2:-1].split(';')]
            index = 0
            while index < len(params):
                value = params[index]
                if value in (38, 48) and params[index + 1] == 2:
                    color = tuple(params[index + 2:index + 5])
                    if value == 38:
                        fg = color
                    else:
                        bg = color
                    index += 5
                else:
                    if value == 0:
                        fg = bg = None
                    elif value == 49:
                        bg = None
                    index += 1
        else:
            result.append((token, fg if token != ' ' else None, bg))
    return result


def rendered(module, options, capture=False):
    rows, rgb = [], []
    module.render_drcs_visualizer(**options, rows_out=rows, rgb_rows_out=rgb if capture else None)
    return [cells(row) for row in rows], rgb


class HalfCellArtwork(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = reference()

    def test_colors_geometry_and_captures_match_v442(self):
        rng = random.Random(443)
        for rows in (7, 24, 32):
            for blend in (0, 1, 2):
                for opacity in (0., .64, 1.):
                    options = fixture(12, rows)
                    options.update(
                        artwork_bar_blend_mode=blend, artwork_bar_opacity=opacity,
                        artwork_bar_strength=rng.choice((.0006, 1 / 3, 1.)),
                        feedback_brightness=rng.choice((.85, 1., 1.15)),
                        top_blank_by_logical_column=[0, 6] * 12,
                        height_override=[rng.uniform(-.1, 1.1) for _ in range(24)],
                    )
                    for capture in (False, True):
                        with self.subTest(rows=rows, blend=blend, opacity=opacity, capture=capture):
                            self.assertEqual(rendered(self.old, options, capture), rendered(p, options, capture))

    def test_halfcell_fill_rounding_ties(self):
        for rows in (1, 7, 32):
            options = fixture(12, rows)
            values = [-1., 0., 1., 2.]
            for subcell in range(rows * 8):
                height = (subcell + .5) / (rows * 8)
                values.extend((math.nextafter(height, 0.), height, math.nextafter(height, 1.)))
            for start in range(0, len(values), 24):
                heights = values[start:start + 24]
                options['height_override'] = heights + [0.] * (24 - len(heights))
                self.assertEqual(rendered(self.old, options), rendered(p, options))

    def test_fallbacks_cropping_and_layer_changes(self):
        for changes in (
            dict(processing_style=1), dict(processing_style=58), dict(force_monochrome=True),
            dict(artwork_bar_strength=0), dict(artwork_background_strength=0),
            dict(artwork_color_grid=None), dict(truncate_top_lines=2),
            dict(rows_only=True), dict(semantic_cells_only=True),
        ):
            options = dict(fixture(), **changes)
            with self.subTest(changes=changes):
                self.assertEqual(rendered(self.old, options), rendered(p, options))
        options = fixture()
        options.update(rows=34, truncate_top_lines=2)
        self.assertEqual(rendered(self.old, options), rendered(p, options))
        with mock.patch.object(p, '_visualizer_numpy', return_value=None):
            self.assertEqual(rendered(self.old, options), rendered(p, options))

    def test_uniform_art_reduces_color_commands(self):
        options = fixture()
        options.update(height_override=[0.] * 48, artwork_color_grid=tuple(((64, 128, 192),) * 48 for _ in range(32)))
        old = self.old.render_drcs_visualizer(**options)
        new = p.render_drcs_visualizer(**options)
        self.assertLess(len(new), len(old) / 4)
        self.assertEqual(rendered(self.old, options), rendered(p, options))

    def test_twin_drcs_path_is_unchanged(self):
        options = dict(fixture(), granularity=3)
        self.assertEqual(self.old.render_drcs_visualizer(**options), p.render_drcs_visualizer(**options))


class ConsoleSafety(unittest.TestCase):
    def test_overlay_survives_each_complete_frame_commit(self):
        # Decode the presentation boundary: no completed frame may expose the
        # background after the previous popup was overwritten.
        for frame in ('spectrum', '\x1b[?2026hspectrum\x1b[?2026l', '\x1b[?2026hfont\x1b[?2026l\x1b[?2026hspectrum\x1b[?2026l'):
            result = p._visualizer_frame_with_overlay(frame, 'popup')
            self.assertTrue(result.startswith('\x1b[?2026h'))
            self.assertTrue(result.endswith('spectrumpopup\x1b[?2026l'))
            self.assertEqual(1, result.count('\x1b[?2026l'))
            self.assertEqual(frame, p._visualizer_frame_with_overlay(frame, ''))

    @unittest.skipUnless(os.name == 'nt', 'Windows UTF-16 writer')
    def test_native_partial_writes_and_non_bmp_units(self):
        received = bytearray()
        class Kernel:
            def GetConsoleMode(self, handle, mode):
                return True
            def WriteConsoleW(self, handle, pointer, units, written, reserved):
                count = min(17, units)
                received.extend(ctypes.string_at(pointer, count * 2))
                written._obj.value = count
                return True
        stream = mock.Mock()
        text = '▌😀abc' * 1000
        with mock.patch('msvcrt.get_osfhandle', return_value=123), mock.patch.object(p, '_windows_wide_console_api', return_value=Kernel()):
            self.assertTrue(p._write_windows_console_wide(stream, text))
        self.assertEqual(text.encode('utf-16-le'), received)
        stream.flush.assert_called_once()

    @unittest.skipUnless(os.name == 'nt', 'Windows UTF-16 writer')
    def test_native_failure_never_replays_an_accepted_prefix(self):
        class Kernel:
            def __init__(self, accept_prefix):
                self.accept_prefix = accept_prefix
                self.calls = 0
            def GetConsoleMode(self, handle, mode):
                return True
            def WriteConsoleW(self, handle, pointer, units, written, reserved):
                self.calls += 1
                if self.calls == 1 and self.accept_prefix:
                    written._obj.value = 3
                    return True
                return False
        for prefix in (False, True):
            with mock.patch('msvcrt.get_osfhandle', return_value=123), mock.patch.object(p, '_windows_wide_console_api', return_value=Kernel(prefix)):
                if prefix:
                    with self.assertRaises(OSError):
                        p._write_windows_console_wide(mock.Mock(), 'abcdef')
                else:
                    self.assertFalse(p._write_windows_console_wide(mock.Mock(), 'abcdef'))

    def test_escape_final_byte_and_dcs_boundaries(self):
        sequence = '\x1b7\x1b[38;2;123;234;255m'
        self.assertEqual(2, p._terminal_escape_sequence_end(sequence, 0))
        dcs = '\x1bP' + 'q' * 4155 + '\x1b\\'
        payload = sequence * 700 + dcs + '\x1b8\x1b[0m'
        chunks = list(p._iter_windows_console_safe_chunks(payload))
        self.assertEqual(payload, ''.join(chunks))
        self.assertTrue(any(dcs in chunk for chunk in chunks))
        # Every boundary falls between complete escape tokens.
        tokens = re.findall(r'\x1bP.*?\x1b\\|\x1b\[[0-9;]*m|\x1b[78]', payload)
        boundaries = {0}
        for token in tokens:
            boundaries.add(max(boundaries) + len(token))
        end = 0
        for chunk in chunks:
            end += len(chunk)
            self.assertIn(end, boundaries)

    @unittest.skipUnless(os.name == 'nt', 'Windows private console check')
    def test_native_unicode_private_console(self):
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        result = subprocess.run(
            [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--native-child'],
            startupinfo=startup, creationflags=subprocess.CREATE_NEW_CONSOLE,
            capture_output=True, text=True, timeout=25,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        for check in json.loads(result.stdout):
            self.assertTrue(check['exact'], check)
            self.assertEqual(0, check['replacements'], check)


def native_child():
    import msvcrt
    from ctypes import wintypes
    kernel = p._windows_wide_console_api()
    class Coord(ctypes.Structure):
        _fields_ = [('X', ctypes.c_short), ('Y', ctypes.c_short)]
    kernel.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, Coord]
    kernel.SetConsoleCursorPosition.argtypes = [wintypes.HANDLE, Coord]
    kernel.ReadConsoleOutputCharacterW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, Coord, ctypes.POINTER(wintypes.DWORD)]
    stream = open('CONOUT$', 'w', encoding='utf-8')
    handle = msvcrt.get_osfhandle(stream.fileno())
    assert kernel.SetConsoleScreenBufferSize(handle, Coord(200, 1000))
    checks = []
    for size in (30000, 120000):
        assert kernel.SetConsoleCursorPosition(handle, Coord(0, 0))
        text = 'A' * 15000 + '▌' + 'B' * (size - 15001)
        with mock.patch.object(p.sys, 'stdout', stream):
            p.write_console(text)
        buffer = ctypes.create_unicode_buffer(size + 1)
        count = wintypes.DWORD()
        assert kernel.ReadConsoleOutputCharacterW(handle, buffer, size, Coord(0, 0), ctypes.byref(count))
        checks.append(dict(size=size, exact=buffer[:size] == text, replacements=buffer[:size].count('\ufffd')))
    # Count UTF-16 units, not Python code points, for non-BMP lyrics/emoji.
    assert p._write_windows_console_wide(stream, '😀' * 6000 + '▌')
    stream.close()
    print(json.dumps(checks))


def benchmark():
    old = reference()
    options = fixture(200)
    frames = [dict(
        height_override=[.5 + .49 * math.sin(i * .07 + frame * .08) for i in range(400)],
        recent_energy=[.5 + .49 * math.sin(i * .041 + frame * .023) for i in range(400)],
    ) for frame in range(16)]
    results = {}
    for name, module in (('V442', old), ('V443', p)):
        module.render_drcs_visualizer(**options)
        times, sizes = [], []
        for frame in frames:
            started = time.perf_counter()
            output = module.render_drcs_visualizer(**dict(options, **frame))
            times.append((time.perf_counter() - started) * 1000)
            sizes.append(len(output.encode('utf-8')))
        results[name] = dict(median_ms=round(statistics.median(times), 3), mean_bytes=round(statistics.mean(sizes)))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    if '--native-child' in sys.argv:
        native_child()
    elif '--benchmark' in sys.argv:
        benchmark()
    else:
        unittest.main()

"""Lock API errors/ABI, same-track restart, and actual decoded bass attenuation."""
import ast
import ctypes
import inspect
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest import mock
import wave

import PAFPlayer as app


@unittest.skipUnless(os.name == 'nt', 'Windows session API')
class LockDetectionTests(unittest.TestCase):
    def query(self, flag, *, level=1, size=232, success=True, windows=(10, 0)):
        # Native WTSINFOEXW is 232 bytes; its 8-byte-aligned union begins at 8.
        data = ctypes.create_string_buffer(232)
        struct.pack_into('<I', data, 0, level)
        struct.pack_into('<IIi', data, 8, 3, 0, flag)
        def query(server, session, kind, pointer, count):
            self.assertEqual((None, 0xffffffff, 25), (server, session, kind))
            pointer._obj.value = ctypes.addressof(data)
            count._obj.value = size
            return success
        dll = NS(WTSQuerySessionInformationW=mock.Mock(side_effect=query), WTSFreeMemory=mock.Mock())
        with mock.patch.object(app.ctypes, 'WinDLL', return_value=dll) as load, \
             mock.patch.object(app.sys, 'getwindowsversion', return_value=NS(major=windows[0], minor=windows[1])):
            value = app._windows_wts_session_is_locked()
        load.assert_called_once_with('wtsapi32', use_last_error=True)
        dll.WTSFreeMemory.assert_called_once()
        self.assertEqual(ctypes.addressof(data), dll.WTSFreeMemory.call_args.args[0].value)
        self.assertEqual(ctypes.POINTER(ctypes.c_void_p), dll.WTSQuerySessionInformationW.argtypes[3])
        return value

    def test_native_layout_locked_and_unlocked(self):
        self.assertIs(self.query(0), True)
        self.assertIs(self.query(1), False)

    def test_unknown_flag_level_truncated_buffer_and_failure_are_not_unlocked(self):
        for kwargs in ({'flag': -1}, {'flag': 2}, {'flag': 0, 'level': 2},
                       {'flag': 0, 'size': 16}, {'flag': 0, 'success': False}):
            with self.subTest(kwargs=kwargs):
                self.assertIsNone(self.query(**kwargs))

    def test_documented_windows_7_flag_reversal(self):
        self.assertFalse(self.query(0, windows=(6, 1)))
        self.assertTrue(self.query(1, windows=(6, 1)))

    def test_authoritative_session_flag_wins_over_accessible_input_desktop(self):
        for locked in (True, False):
            with mock.patch.object(app, '_windows_wts_session_is_locked', return_value=locked), \
                 mock.patch.object(app, '_windows_input_desktop_is_locked') as fallback:
                self.assertIs(app.windows_session_is_locked(), locked)
                fallback.assert_not_called()

    def test_unknown_or_failed_session_query_uses_read_only_fallback(self):
        for outcome in (None, OSError('unavailable')):
            with mock.patch.object(app, '_windows_wts_session_is_locked', side_effect=[outcome]), \
                 mock.patch.object(app, '_windows_input_desktop_is_locked', return_value=True):
                self.assertTrue(app.windows_session_is_locked())
        with mock.patch.object(app, '_windows_wts_session_is_locked', side_effect=OSError), \
             mock.patch.object(app, '_windows_input_desktop_is_locked', side_effect=OSError):
            self.assertFalse(app.windows_session_is_locked())

    def test_access_denied_uses_captured_error_and_does_not_leak_stale_error(self):
        for error, expected in ((5, True), (6, False), (0, False)):
            def open_desktop(*args):
                ctypes.set_last_error(error)
                return None
            dll = NS(OpenInputDesktop=mock.Mock(side_effect=open_desktop),
                     GetUserObjectInformationW=mock.Mock(), CloseDesktop=mock.Mock())
            ctypes.set_last_error(5)
            with mock.patch.object(app.ctypes, 'WinDLL', return_value=dll) as load:
                self.assertIs(app._windows_input_desktop_is_locked(), expected)
            load.assert_called_once_with('user32', use_last_error=True)
            dll.CloseDesktop.assert_not_called()
            dll.OpenInputDesktop.assert_called_once_with(0, False, 1)

    def test_fallback_names_and_pointer_width_preserved_handles_always_closed(self):
        handle = 0x12345678ABCDEF
        for name, success, expected in (('Default', True, False), ('Winlogon', True, True),
                                         ('Other', True, False), ('', False, False)):
            def info(h, kind, buffer, size, needed):
                self.assertEqual((handle, 2), (h, kind))
                buffer.value = name
                return success
            dll = NS(OpenInputDesktop=mock.Mock(return_value=handle),
                     GetUserObjectInformationW=mock.Mock(side_effect=info), CloseDesktop=mock.Mock())
            with mock.patch.object(app.ctypes, 'WinDLL', return_value=dll):
                self.assertIs(app._windows_input_desktop_is_locked(), expected)
            self.assertEqual(ctypes.c_void_p, dll.OpenInputDesktop.restype)
            dll.CloseDesktop.assert_called_once_with(handle)
            self.assertNotIn('SwitchDesktop', vars(dll))


class BassTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(inspect.getsource(app.play_audio_file))
        block = next(n for n in ast.walk(tree) if isinstance(n, ast.If)
                     and ast.unparse(n.test) == 'now - last_bass_lock_check_at >= 1.0')
        # Execute the actual production block inside a while/else, retaining its
        # original break/continue semantics. The old continue enters natural EOF.
        wrapper = ast.parse('while process.poll() is None:\n pass\n break\nelse:\n natural_eof = True')
        wrapper.body[0].body[0] = block
        cls.code = compile(ast.fix_missing_locations(wrapper), '<real bass monitor>', 'exec')

    def setUp(self):
        self.locked = False
        self.settings = dict(ReduceBassWhenLocked=1, LockedBassReductionPercent=70,
                             BassBoostEnabled=0, BassBoostPercent=100)
        self.process = NS(ended=False)
        self.process.poll = lambda: 0 if self.process.ended else None
        self.stop = mock.Mock(side_effect=lambda p: setattr(p, 'ended', True))
        self.ns = dict(now=100, last_bass_lock_check_at=-1e9, last_bass_lock_state=False,
                       last_bass_filter_signature=None, load_bass_settings=lambda: self.settings,
                       windows_session_is_locked=lambda: self.locked,
                       bass_settings_effective_db=app.bass_settings_effective_db,
                       process=self.process, stop_process=self.stop, record_segment=mock.Mock(),
                       displayed_position=12.34, position=0, web_server=mock.Mock(), natural_eof=False)

    def poll(self, at):
        self.ns['now'] = at
        exec(self.code, self.ns)

    def test_lock_and_unlock_restart_same_song_without_natural_eof(self):
        self.poll(100)
        self.stop.assert_not_called()
        self.locked = True
        self.poll(101)
        self.stop.assert_called_once_with(self.process)
        self.assertFalse(self.ns['natural_eof'])
        self.assertEqual(12.34, self.ns['position'])
        self.assertTrue(self.ns['resume_after_pause'])
        self.assertEqual(-14, self.ns['last_bass_filter_signature'])
        self.ns['web_server'].update_fields.assert_called_with(session_locked=True, bass_effective_db=-14)
        self.process.ended = False
        self.poll(102)
        self.assertEqual(1, self.stop.call_count)
        self.locked = False
        self.poll(103)
        self.assertEqual(2, self.stop.call_count)
        self.assertFalse(self.ns['natural_eof'])
        self.assertEqual(0, self.ns['last_bass_filter_signature'])
        self.ns['web_server'].update_fields.assert_called_with(session_locked=False, bass_effective_db=0)

    def test_disabled_reduction_and_zero_amount_do_not_restart_on_lock(self):
        for changes in ({'ReduceBassWhenLocked': 0}, {'LockedBassReductionPercent': 0}):
            self.setUp()
            self.settings.update(changes)
            self.poll(100)
            self.locked = True
            self.poll(101)
            self.stop.assert_not_called()

    def test_poll_is_one_hertz_not_each_visualizer_frame(self):
        self.ns['load_bass_settings'] = mock.Mock(return_value=self.settings)
        for n in range(60):
            self.poll(100 + n / 60)
        self.ns['load_bass_settings'].assert_called_once()
        self.poll(101)
        self.assertEqual(2, self.ns['load_bass_settings'].call_count)

    def test_both_command_builders_use_detected_lock_and_keep_single_filter_chain(self):
        for builder in (app.ffplay_command, app.matrixmixer_inspired_ffmpeg_command):
            with self.subTest(builder=builder.__name__), \
                 mock.patch.object(app, 'load_bass_settings', return_value=self.settings), \
                 mock.patch.object(app, 'probe_audio_stream_layout', return_value=(2, 'stereo')):
                for locked in (False, True, False):
                    with mock.patch.object(app, 'windows_session_is_locked', return_value=locked):
                        command = builder(Path('ffmpeg.exe'), Path('track.wav'), 12.34, 100, 1., 5, 0)
                    self.assertEqual(1, command.count('-af'))
                    filters = command[command.index('-af') + 1]
                    self.assertEqual(locked, 'bass=g=-14:' in filters)
                    if locked:
                        self.assertLess(filters.index('bass='), filters.index('pan='))

    def test_actual_pcm_loses_low_bass_and_keeps_treble_then_restores(self):
        import numpy as np
        executable = shutil.which('ffmpeg')
        self.assertTrue(executable, 'FFmpeg is required for the decoded-audio verification')
        folder = Path(tempfile.mkdtemp(prefix='v590-pcm-'))
        audio = folder / 'bass-and-treble.wav'
        rate = 48000
        t = np.arange(rate * 2) / rate
        samples = .08 * np.sin(2 * np.pi * 40 * t) + .08 * np.sin(2 * np.pi * 1000 * t)
        pcm = np.repeat((samples * 32767).astype('<i2')[:, None], 2, axis=1)
        with wave.open(str(audio), 'wb') as stream:
            stream.setnchannels(2); stream.setsampwidth(2); stream.setframerate(rate)
            stream.writeframes(pcm.tobytes())
        output = []
        with mock.patch.object(app, 'load_bass_settings', return_value=self.settings), \
             mock.patch.object(app, 'probe_audio_stream_layout', return_value=(2, 'stereo')):
            for locked in (False, True, False):
                with mock.patch.object(app, 'windows_session_is_locked', return_value=locked):
                    command = app.matrixmixer_inspired_ffmpeg_command(
                        Path(executable), audio, 0, 100, 1., 2, 0, rate, 16)
                result = subprocess.run(command, capture_output=True, timeout=15)
                self.assertEqual(0, result.returncode, result.stderr.decode(errors='replace'))
                output.append(np.frombuffer(result.stdout, dtype='<i2').reshape(-1, 2)[rate // 2:rate * 3 // 2, 0].astype(float))
        def magnitude(values, frequency):
            return abs(np.dot(values, np.exp(-2j * np.pi * frequency * np.arange(len(values)) / rate)))
        bass_db = 20 * math.log10(magnitude(output[1], 40) / magnitude(output[0], 40))
        treble_db = 20 * math.log10(magnitude(output[1], 1000) / magnitude(output[0], 1000))
        self.assertLess(bass_db, -10)
        self.assertGreater(treble_db, -1)
        np.testing.assert_array_equal(output[0], output[2])
        print(f'V590 decoded audio: 40 Hz {bass_db:.2f} dB; 1 kHz {treble_db:.2f} dB; unlock restores identical PCM')


if __name__ == '__main__':
    unittest.main()

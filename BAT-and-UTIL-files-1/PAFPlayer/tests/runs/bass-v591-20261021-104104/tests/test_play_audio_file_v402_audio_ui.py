"""V402 audio isolation, opacity, and window-recovery regression checks.

The default suite uses fakes and does not play audio or write registry settings.
--audio-stress sends a MUTED excerpt of the reported FLAC to the current default
WaveOut device at 7.1 / 96 kHz / 24-bit, while blocking the owner's Python GIL.
--audio-lifecycle checks short-track EOF, stop, restart/seek, and owner-pipe EOF
using muted excerpts on the default WaveOut device.
"""
from __future__ import annotations
import argparse
import ctypes
import inspect
import io
import json
from pathlib import Path
import queue
import sys
import threading
import time
import unittest
from unittest import mock

import play_audio_file as p


class WorkerTests(unittest.TestCase):
    config = dict(command=["ffmpeg"], output_channels=7, sample_rate=96000,
                  bit_depth=24, buffer_ms=250,
                  outputs=[dict(device=0, delay_ms=0), dict(device=2, delay_ms=12)])

    class OwnerInput:
        def __init__(self, lines):
            self.lines = iter(lines)
        def __iter__(self):
            return self
        def __next__(self):
            try:
                return next(self.lines)
            except StopIteration:
                time.sleep(.1)
                raise

    def test_worker_owns_outputs_and_preserves_common_barrier(self):
        processes = []
        def factory(*args, **kwargs):
            proc = mock.Mock(_last_error="", playback_started_at=123., queued_audio_ms=250., underruns=0)
            proc.poll.return_value = None
            proc.args, proc.kwargs = args, kwargs
            processes.append(proc)
            return proc
        out = io.StringIO()
        with mock.patch.object(p, "matrix_output_levels_snapshot", return_value={}):
            rc = p.run_isolated_audio_worker(self.config, self.OwnerInput([]), out, process_factory=factory)
        self.assertEqual(rc, 0)
        self.assertEqual(len(processes), 2)
        self.assertIs(processes[0].kwargs["start_barrier"], processes[1].kwargs["start_barrier"])
        self.assertEqual(processes[1].kwargs["initial_delay_ms"], 12)
        self.assertEqual(processes[1].args[1:3], (7, 96000))
        self.assertIn('"started_at": 123.0', out.getvalue())
        for proc in processes:
            proc.kill.assert_called_once()
            proc.wait.assert_called_once()

    def test_worker_failure_closes_already_open_devices(self):
        proc = mock.Mock(_last_error="", playback_started_at=None)
        proc.poll.return_value = None
        out = io.StringIO()
        factory = mock.Mock(side_effect=[proc, RuntimeError("second endpoint unavailable")])
        rc = p.run_isolated_audio_worker(self.config, self.OwnerInput([]), out, process_factory=factory)
        self.assertEqual(rc, 1)
        proc.kill.assert_called_once()
        self.assertIn("second endpoint unavailable", out.getvalue())

    def test_launch_routes_matrix_and_device_delays_to_isolated_worker(self):
        with mock.patch.object(p, "direct_ffmpeg_executable", return_value=Path("ffmpeg.exe")), \
             mock.patch.object(p, "matrixmixer_inspired_ffmpeg_command", return_value=["ffmpeg.exe", "-matrix", "test"]), \
             mock.patch.object(p, "waveout_output_devices", return_value=[{"value": 0}, {"value": 2}]), \
             mock.patch.object(p, "load_multi_output_latencies_ms", return_value={}), \
             mock.patch.object(p, "effective_multi_output_delays_ms", return_value={0: 0, 2: 30}), \
             mock.patch.object(p, "IsolatedWaveOutProcess") as worker:
            result, command = p.launch_matrixmixer_inspired_renderer(
                Path("song.flac"), 5., 100, 1., 7, 0, 96000, 0, 24, [0, 2],
                end_seconds=None, replaygain_info=None,
            )
        config = worker.call_args.args[0]
        self.assertIs(result, worker.return_value)
        self.assertEqual(config["command"], command)
        self.assertEqual(config["outputs"], [dict(device=0, delay_ms=0), dict(device=2, delay_ms=30)])

    def test_buffer_duration_survives_high_rates_and_large_requests(self):
        for rate, milliseconds in ((96000, 250), (192000, 250), (192000, 1000)):
            process = object.__new__(p.MatrixMixerInspiredWaveOutProcess)
            # Stop at DLL loading, before acquiring any native handles/devices.
            with mock.patch.object(p.ctypes, "WinDLL", side_effect=RuntimeError("no native device")):
                with self.assertRaisesRegex(RuntimeError, "no native device"):
                    process.__init__(["ffmpeg"], 7, rate, -1, 24, target_buffer_ms=milliseconds)
            self.assertGreaterEqual(process.preroll_buffers * p.MM_INSPIRED_BUFFER_FRAMES * 1000 / rate, milliseconds)
            self.assertGreaterEqual(process.pending_buffer_limit, process.preroll_buffers + 2)

    def test_device_stop_releases_other_outputs_from_start_barrier(self):
        for action in ("terminate", "kill"):
            process = object.__new__(p.MatrixMixerInspiredWaveOutProcess)
            process._stop = threading.Event()
            process.start_barrier = threading.Barrier(2)
            process._done_event = None
            process._winmm, process._ffmpeg, process._wave_handle = mock.Mock(), mock.Mock(), None
            getattr(process, action)()
            self.assertTrue(process.start_barrier.broken)
            self.assertTrue(process._stop.is_set())
            getattr(process._ffmpeg, action).assert_called_once()


class ControlsTests(unittest.TestCase):
    def test_labels_controls_and_recovery_actions(self):
        schema = p.paf_web_control_schema()
        blend = next(x for x in schema["selects"] if x["key"] == "art_color_bar_blend_mode")
        self.assertFalse(blend.get("experimental", False))
        cursive = next(x for x in schema["toggles"] if x["key"] == "cursive_fix")
        self.assertEqual(cursive["label"], "Cursive fix (broken)")
        slider = next(x for x in schema["sliders"] if x["key"] == "art_color_bar_opacity")
        self.assertEqual((slider["min"], slider["max"], slider["step"]), (0, 100, 1))
        html = p._paf_web_html()
        self.assertIn("<h3>Artwork Pop-Up</h3>", html)
        self.assertNotIn("Artwork Pop-Up + Karaoke", html)
        self.assertIn("background:#3c1218;border-color:#c64652", html)
        self.assertIn("top.insertAdjacentElement('afterend',center)", html)
        for action in (p.EXTERNAL_ALBUM_ART_CENTER, p.EXTERNAL_FLOATING_LYRICS_CENTER):
            self.assertTrue(p.paf_web_action_is_allowed(action))

    def test_centering_uses_active_monitor_and_keeps_large_window_visible(self):
        monitors = [(-1920, 0, 0, 1080, False, "left"), (0, 0, 1920, 1040, True, "main")]
        self.assertEqual(p.centered_popup_geometry(800, 400, monitors, (-900, 100, -300, 800)), "800x400-1360+340")
        self.assertEqual(p.centered_popup_geometry(800, 400, monitors), "800x400+560+320")
        width, height, x, y = p._parse_external_album_art_geometry(p.centered_popup_geometry(9000, 8000, monitors))
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(x + width, 1920)
        self.assertLessEqual(y + height, 1040)

    def test_recovery_is_queued_to_the_tk_owner(self):
        window = object.__new__(p.ExternalAlbumArtWindow)
        window._lock, window._closed, window._enabled = threading.RLock(), False, False
        window._commands = queue.Queue()
        window._player_window_rect = (0, 0, 800, 600)
        window._ensure_started = mock.Mock()
        with mock.patch.object(p, "windows_foreground_window_rect", return_value=(900, 0, 1500, 500)):
            self.assertTrue(window.bring_to_center(floating=True))
        self.assertEqual(window._commands.get_nowait(), ("center-window", True, (900, 0, 1500, 500)))

    def test_native_centering_uses_signed_outer_bounds_instead_of_tk_edge_offsets(self):
        monitors = [(-1920, 0, 0, 1080, False, "left"), (0, 0, 1920, 1040, True, "main")]
        window = mock.Mock()
        with mock.patch.object(p, "windows_window_rect", return_value=(8000, 5000, 8800, 5400)), \
             mock.patch.object(p, "windows_set_window_rect", return_value=True) as position:
            geometry = p.center_popup_window(window, 321, monitors, (-900, 100, -300, 800))
        self.assertEqual(geometry, "800x400-1360+340")
        position.assert_called_once_with(321, (-1360, 340, -560, 740))
        window.geometry.assert_not_called()

    def test_centering_has_tk_fallback_when_no_native_window_is_available(self):
        window = mock.Mock()
        window.winfo_width.return_value = 800
        window.winfo_height.return_value = 400
        with mock.patch.object(p, "windows_window_rect", return_value=None), \
             mock.patch.object(p, "windows_set_window_rect", return_value=False):
            geometry = p.center_popup_window(window, 0, [(0, 0, 1920, 1040, True, "main")])
        window.geometry.assert_called_once_with("800x400+560+320")
        self.assertEqual(geometry, "800x400+560+320")


class OpacityTests(unittest.TestCase):
    def test_full_cell_opacity_endpoints_and_linear_midpoint(self):
        grid = (((((10, 200, 30)), ((210, 10, 160)), "A"),),)
        base = [(100, 80, 240)]
        for mode in (0, 1, 2):
            art = p._visualizer_bar_art_colors(grid, base, 700, mode, 1., 0)[0]
            opaque = p._visualizer_bar_art_colors(grid, base, 700, mode, 1., 1000)[0]
            middle = p._visualizer_bar_art_colors(grid, base, 700, mode, 1., 500)[0]
            self.assertEqual(opaque, bytes(base[0] * 2))
            self.assertEqual(middle, bytes(round((a + b) / 2) for a, b in zip(art, opaque)))

    def test_renderer_numpy_and_scalar_opacity_match(self):
        import test_play_audio_file_v401_bar_art as previous
        for mode in (0, 1, 2):
            for opacity in (.0, .25, .7, 1.):
                options = previous.fixture(18, 32, 9)
                options.update(artwork_bar_opacity=opacity, artwork_bar_blend_mode=mode, feedback_brightness=1.15)
                def draw():
                    rows, rgb = [], []
                    output = p.render_drcs_visualizer(**options, rows_out=rows, rgb_rows_out=rgb)
                    return output, rows, rgb
                native = draw()
                with mock.patch.object(p, "_visualizer_numpy", return_value=None):
                    scalar = draw()
                self.assertEqual(native, scalar)


def muted_audio_config(duration=8, start=0, rate=96000, channels=7, bits=24):
    path = Path(r"T:\mp3\Voiid\2019 - Drool (EP)\4_Durry Mouth.flac")
    # Muting occurs in FFmpeg before PCM reaches any physical output.
    command = [str(p.direct_ffmpeg_executable()), "-v", "error", "-nostdin", "-ss", str(start), "-i", str(path),
               "-t", str(duration), "-map", "0:a:0", "-vn", "-af", "volume=0", "-ar", str(rate),
               "-ac", str(p.MM_CHANNEL_COUNTS[channels]), "-c:a", f"pcm_s{bits}le", "-f", f"s{bits}le", "pipe:1"]
    return dict(command=command, output_channels=channels, sample_rate=rate, bit_depth=bits,
                buffer_ms=250, outputs=[dict(device=-1, delay_ms=0)])


def audio_stress():
    process = p.IsolatedWaveOutProcess(muted_audio_config())
    health = []
    try:
        deadline = time.monotonic() + 6
        while process.playback_started_at is None and process.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        if process.playback_started_at is None:
            raise AssertionError("Worker did not start audio: " + process._last_error)
        # PyDLL deliberately holds this interpreter's GIL during Sleep, like
        # a non-cooperative native artwork call. The worker must refill anyway.
        sleep_holding_gil = ctypes.PyDLL("kernel32").Sleep
        sleep_holding_gil.argtypes = [ctypes.c_uint32]
        for _ in range(4):
            sleep_holding_gil(900)
            time.sleep(.15)
            health.append(process.audio_health)
        code = process.wait(timeout=8)
        health.append(process.audio_health)
        print(json.dumps({"exit_code": code, "owner_gil_stalls_ms": [900] * 4, "audio_health": health}, indent=2))
        assert code == 0, process._last_error
        assert all(sample["underruns"] == 0 for sample in health), health
    finally:
        if process.poll() is None:
            process.kill()


def audio_lifecycle():
    results = []
    for name, config, action in (
        ("short_track", muted_audio_config(.08, rate=44100, channels=2, bits=16), None),
        ("stop", muted_audio_config(12), "stop"),
        ("restart_at_60_seconds", muted_audio_config(.5, start=60), None),
        ("owner_eof", muted_audio_config(12), "eof"),
    ):
        process = p.IsolatedWaveOutProcess(config)
        try:
            if action:
                deadline = time.monotonic() + 5
                while process.playback_started_at is None and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.02)
                assert process.playback_started_at is not None, process._last_error
                if action == "stop":
                    process.terminate()
                else:
                    process._process.stdin.close()
            before = time.monotonic()
            code = process.wait(timeout=5)
            process._reader.join(timeout=1)
            assert code == 0, process._last_error
            assert process._process.stdin.closed and process._process.stdout.closed
            assert process.playback_started_at is not None
            results.append(dict(case=name, exit_code=code, wait_ms=round((time.monotonic()-before)*1000), **process.audio_health))
        finally:
            if process.poll() is None:
                process.kill()
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio-stress", action="store_true")
    parser.add_argument("--audio-lifecycle", action="store_true")
    args = parser.parse_args()
    if args.audio_stress:
        audio_stress()
    elif args.audio_lifecycle:
        audio_lifecycle()
    else:
        unittest.main(argv=[sys.argv[0]])

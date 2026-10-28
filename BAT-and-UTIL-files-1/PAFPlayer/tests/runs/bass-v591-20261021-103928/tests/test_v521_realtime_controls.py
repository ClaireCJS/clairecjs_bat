"""Focused regression tests for the V521 live WaveOut controls."""
import io
import json
import queue
import threading
import time
import unittest
from unittest import mock

import PAFPlayer as app


class LiveAudioControlsTests(unittest.TestCase):
    def test_final_pcm_gain_supports_mute_unity_attenuation_and_clipping(self):
        samples = (10000).to_bytes(2, "little", signed=True) + (-10000).to_bytes(2, "little", signed=True)
        self.assertEqual(samples, app.scale_waveout_pcm(samples, 16, 100))
        self.assertEqual(b"\x00" * len(samples), app.scale_waveout_pcm(samples, 16, 0))
        half = app.scale_waveout_pcm(samples, 16, 50)
        self.assertAlmostEqual(5000, int.from_bytes(half[:2], "little", signed=True), delta=1)
        self.assertAlmostEqual(-5000, int.from_bytes(half[2:], "little", signed=True), delta=1)
        loud = app.scale_waveout_pcm(samples, 16, 400)
        self.assertEqual(32767, int.from_bytes(loud[:2], "little", signed=True))
        self.assertEqual(-32768, int.from_bytes(loud[2:], "little", signed=True))

    def test_pause_during_initial_preroll_does_not_start_output_early(self):
        process = app.MatrixMixerInspiredWaveOutProcess.__new__(app.MatrixMixerInspiredWaveOutProcess)
        process._wave_handle_lock = threading.RLock()
        process._wave_handle = object()
        process._stop = threading.Event()
        process._user_paused = threading.Event()
        process._playback_started_at = None
        driver = mock.Mock()
        driver.waveOutPause.return_value = app.MM_MMSYSERR_NOERROR
        driver.waveOutRestart.return_value = app.MM_MMSYSERR_NOERROR
        process._winmm = driver
        self.assertTrue(process.set_paused(True))
        self.assertTrue(process._user_paused.is_set())
        self.assertTrue(process.set_paused(False))
        self.assertFalse(process._user_paused.is_set())
        driver.waveOutRestart.assert_not_called()
        process._playback_started_at = time.monotonic()
        self.assertTrue(process.set_paused(False))
        driver.waveOutRestart.assert_called_once()

    def test_owner_sends_live_volume_and_pause_commands(self):
        process = app.IsolatedWaveOutProcess.__new__(app.IsolatedWaveOutProcess)
        process._process = mock.Mock()
        process._process.stdin = io.StringIO()
        process._process.poll.return_value = None
        process._stop_sent = False
        process._clock_sample = {"seconds": 12.5, "at": time.monotonic(), "queued_seconds": .05}
        process._started_at = 1.0
        process._resume_started_at = None
        process._clock_origin = 0.0
        self.assertTrue(process.set_volume(135))
        self.assertTrue(process.set_paused(True))
        self.assertTrue(process.set_paused(False))
        messages = [json.loads(line) for line in process._process.stdin.getvalue().splitlines()]
        self.assertEqual([{"volume": 135}, {"paused": True}, {"paused": False}], messages)
        self.assertAlmostEqual(0.0, process.playback_clock["seconds"])
        self.assertIsNotNone(process.playback_started_at)
        process._stop_sent = True
        self.assertFalse(process.set_volume(150))

    def test_worker_routes_live_commands_to_active_outputs(self):
        class Input:
            def __init__(self): self.lines = queue.Queue()
            def __iter__(self): return self
            def __next__(self):
                value = self.lines.get(timeout=3)
                if value is None: raise StopIteration
                return value

        class FakeOutput:
            instances = []
            def __init__(self, *args, **kwargs):
                self.volume = []
                self.paused = []
                self._primed = threading.Event(); self._primed.set()
                self._start_allowed = threading.Event()
                self._last_error = ""
                self.playback_started_at = None
                self.playback_clock = None
                self.queued_audio_ms = 0
                self.underruns = 0
                self.done = False
                self.instances.append(self)
            def poll(self): return 0 if self.done else None
            def set_volume(self, value): self.volume.append(value)
            def set_paused(self, value): self.paused.append(value)
            def kill(self): self.done = True
            def wait(self, timeout=None): return 0

        incoming = Input(); outgoing = io.StringIO()
        config = {"outputs": [{"device": -1, "delay_ms": 0}], "command": [],
                  "output_channels": 2, "sample_rate": 48000, "bit_depth": 16,
                  "buffer_ms": 50, "volume": 100, "hold_for_handoff": True}
        thread = threading.Thread(target=app.run_isolated_audio_worker,
                                  args=(config, incoming, outgoing),
                                  kwargs={"process_factory": FakeOutput})
        thread.start()
        deadline = time.monotonic() + 3
        while not FakeOutput.instances and time.monotonic() < deadline: time.sleep(.01)
        self.assertTrue(FakeOutput.instances)
        incoming.lines.put('{"volume": 75}\n')
        incoming.lines.put('{"paused": true}\n')
        incoming.lines.put('{"paused": false}\n')
        incoming.lines.put('{"start": true}\n')
        deadline = time.monotonic() + 3
        output = FakeOutput.instances[0]
        while (len(output.paused) < 2 or not output._start_allowed.is_set()) and time.monotonic() < deadline:
            time.sleep(.01)
        incoming.lines.put('stop\n')
        thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual([75], output.volume)
        self.assertEqual([True, False], output.paused)
        self.assertTrue(output._start_allowed.is_set())

    def test_held_global_volume_key_repeats(self):
        app._ASYNC_KEY_LATCH.clear()
        app._ASYNC_HELD_ACTION_REPEAT_AT.clear()
        app._GLOBAL_SEEK_CAPTURE = None
        clock = mock.Mock(return_value=100.0)
        with mock.patch.object(app, "_windows_key_down", side_effect=lambda key: key in (0x11, 0x12, 0x26)), \
             mock.patch.object(app.time, "monotonic", clock):
            self.assertEqual(app.VOLUME_UP_5, app.read_windows_key_action())
            clock.return_value = 100.33
            self.assertEqual(app.VOLUME_UP_5, app.read_windows_key_action())
            clock.return_value = 100.42
            self.assertEqual(app.VOLUME_UP_5, app.read_windows_key_action())
        app._ASYNC_KEY_LATCH.clear()
        app._ASYNC_HELD_ACTION_REPEAT_AT.clear()

    def test_pause_feedback_describes_result(self):
        self.assertEqual("Pause", app.pause_visualizer_feedback_label(False))
        self.assertEqual("Unpause", app.pause_visualizer_feedback_label(True))


if __name__ == "__main__":
    unittest.main()

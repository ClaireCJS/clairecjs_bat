"""Focused regressions for ordered global taps and live audio-worker seeks."""
import io
import json
import queue
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

import PAFPlayer as app


class Lines:
    def __init__(self):
        self.items = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        value = self.items.get(timeout=5)
        if value is None:
            raise StopIteration
        return value


class FakeOutput:
    instances = []
    gate_replacements = None

    def __init__(self, command, *args, **kwargs):
        self.command = command
        self._primed = threading.Event()
        self._start_allowed = threading.Event()
        self._last_error = ""
        self.underruns = 0
        self.queued_audio_ms = 0
        self.stopped = False
        self.buffer_frames = kwargs.get("buffer_frames")
        self.__class__.instances.append(self)
        if len(self.__class__.instances) == 1 or self.__class__.gate_replacements is None:
            self._primed.set()

    @property
    def playback_started_at(self):
        return time.monotonic() if self._start_allowed.is_set() and not self.stopped else None

    @property
    def playback_clock(self):
        return {"seconds": 0.0, "at": time.monotonic(), "queued_seconds": 0.0}

    def poll(self):
        return 0 if self.stopped else None

    def set_volume(self, value):
        self.volume = value

    def set_bass_db(self, value):
        self.bass_db = value

    def set_paused(self, value):
        self.paused = value

    def terminate(self):
        self.stopped = True

    def kill(self):
        self.stopped = True

    def wait(self, timeout=None):
        return 0


class ResponsiveGlobalSeekTests(unittest.TestCase):
    def test_live_renderer_reuses_worker_for_seek(self):
        worker = mock.Mock()
        worker.seek_to.return_value = True
        with mock.patch.object(app, "direct_ffmpeg_executable", return_value=Path("ffmpeg.exe")), \
             mock.patch.object(app, "matrixmixer_inspired_ffmpeg_command", return_value=["ffmpeg", "pipe:1"]), \
             mock.patch.object(app, "waveout_output_devices", side_effect=AssertionError("should not re-enumerate")):
            result, command = app.launch_matrixmixer_inspired_renderer(
                Path("song.flac"), 35.0, 100, 1.0, 2, 0, 48000,
                end_seconds=90.0, replaygain_info=None, target_buffer_ms=50,
                reuse_process=worker,
            )
        self.assertIs(result, worker)
        self.assertEqual(["ffmpeg", "pipe:1"], command)
        worker.seek_to.assert_called_once_with(command, 20)

    def test_rapid_taps_and_reversal_keep_order(self):
        capture = app.GlobalSeekCapture()
        for direction, when in [(1, 0), (0, .015), (1, .030), (0, .045),
                                (1, .060), (0, .075), (-1, .090), (0, .105)]:
            capture.sample(direction, when)
        self.assertEqual([5, 5, 5, -5], [capture.drain_one() for _ in range(4)])
        self.assertEqual(0, capture.drain_one())
        self.assertEqual(0, capture.drain())

    def test_held_seek_repeats_and_legacy_sum_still_works(self):
        capture = app.GlobalSeekCapture()
        capture.sample(1, 0.0)
        capture.sample(1, 0.50)
        self.assertEqual(20, capture.drain())
        self.assertEqual(0, capture.drain_one())

    def test_worker_reuses_process_and_keeps_old_audio_until_ready(self):
        FakeOutput.instances = []
        FakeOutput.gate_replacements = threading.Event()
        incoming = Lines()
        outgoing = io.StringIO()
        config = {"outputs": [{"device": -1, "delay_ms": 0}], "command": ["old"],
                  "output_channels": 2, "sample_rate": 48000, "bit_depth": 16,
                  "buffer_ms": 50, "volume": 100, "hold_for_handoff": True}
        runner = threading.Thread(target=app.run_isolated_audio_worker,
                                  args=(config, incoming, outgoing),
                                  kwargs={"process_factory": FakeOutput})
        runner.start()
        try:
            deadline = time.monotonic() + 3
            while len(FakeOutput.instances) < 1 and time.monotonic() < deadline:
                time.sleep(.005)
            self.assertEqual(1, len(FakeOutput.instances))
            incoming.items.put('{"start": true}\n')
            incoming.items.put(json.dumps({"seek": {"command": ["new"], "buffer_ms": 20}}) + "\n")
            deadline = time.monotonic() + 3
            while len(FakeOutput.instances) < 2 and time.monotonic() < deadline:
                time.sleep(.005)
            self.assertEqual(2, len(FakeOutput.instances))
            old, new = FakeOutput.instances
            self.assertFalse(old.stopped)
            self.assertIsNone(new.playback_started_at)
            self.assertEqual(1024, new.buffer_frames)
            new._primed.set()
            deadline = time.monotonic() + 3
            while '"seek_started"' not in outgoing.getvalue() and time.monotonic() < deadline:
                time.sleep(.005)
            self.assertIn('"seek_started"', outgoing.getvalue())
            deadline = time.monotonic() + 3
            while not old.stopped and time.monotonic() < deadline:
                time.sleep(.005)
            self.assertTrue(old.stopped)
            self.assertFalse(new.stopped)
        finally:
            incoming.items.put("stop\n")
            runner.join(3)
            FakeOutput.gate_replacements = None
        self.assertFalse(runner.is_alive())
        self.assertTrue(FakeOutput.instances[-1].stopped)

    def test_seek_failure_preserves_old_output(self):
        FakeOutput.instances = []
        FakeOutput.gate_replacements = None
        incoming = Lines()
        outgoing = io.StringIO()
        config = {"outputs": [{"device": -1, "delay_ms": 0}], "command": ["old"],
                  "output_channels": 2, "sample_rate": 48000, "bit_depth": 16,
                  "buffer_ms": 50, "volume": 100, "hold_for_handoff": True}
        runner = threading.Thread(target=app.run_isolated_audio_worker,
                                  args=(config, incoming, outgoing),
                                  kwargs={"process_factory": FakeOutput})
        runner.start()
        try:
            deadline = time.monotonic() + 3
            while not FakeOutput.instances and time.monotonic() < deadline:
                time.sleep(.005)
            incoming.items.put('{"start": true}\n')
            incoming.items.put('{"seek": {"command": []}}\n')
            deadline = time.monotonic() + 3
            while '"seek_failed"' not in outgoing.getvalue() and time.monotonic() < deadline:
                time.sleep(.005)
            self.assertIn('"seek_failed"', outgoing.getvalue())
            self.assertFalse(FakeOutput.instances[0].stopped)
        finally:
            incoming.items.put("stop\n")
            runner.join(3)
        self.assertFalse(runner.is_alive())


if __name__ == "__main__":
    unittest.main()

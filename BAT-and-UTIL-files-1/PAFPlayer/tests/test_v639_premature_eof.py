"""Regression checks for a worker that ends before the source track does.

The real-device check is opt-in because it takes the song's full duration.
It starts an independent audio worker at zero volume and never connects to
PAFPlayer's official instance, web server, or command channel.
"""

from __future__ import annotations

import os
from pathlib import Path
import time
import unittest

import PAFPlayer as app
from PAFPlayer_memory_audio import MemoryAudioSource


MAGIC_JOHNSON = Path(
    r"T:\mp3\Red Hot Chili Peppers\4 - 1989 - Mother's Milk\04_Magic Johnson.mp3"
)


class PrematureEndTests(unittest.TestCase):
    def test_early_eof_requires_recovery(self):
        self.assertAlmostEqual(53.2794, app.premature_audio_eof_remaining(176.7794, 123.5))
        self.assertEqual(0.0, app.premature_audio_eof_remaining(176.7794, 175.7))
        self.assertEqual(0.0, app.premature_audio_eof_remaining(None, 123.5))
        self.assertEqual(0.0, app.premature_audio_eof_remaining(float("nan"), 123.5))

    @unittest.skipUnless(os.name == "nt", "Windows WaveOut is required")
    @unittest.skipUnless(
        os.environ.get("PAFPLAYER_LIVE_AUDIO_TEST") == "1",
        "set PAFPLAYER_LIVE_AUDIO_TEST=1 for the muted real-device check",
    )
    def test_magic_johnson_muted_isolated_worker_reaches_end(self):
        if not MAGIC_JOHNSON.is_file():
            self.skipTest(f"WARNING: reference MP3 unavailable: {MAGIC_JOHNSON}")
        if app.direct_ffmpeg_executable() is None:
            self.skipTest("WARNING: FFmpeg unavailable for the real-device check")
        devices = {int(row["value"]) for row in app.waveout_output_devices()}
        if 0 not in devices:
            self.skipTest("WARNING: original HDMI output device 0 is unavailable")

        source = MemoryAudioSource.try_open(MAGIC_JOHNSON, max_bytes=10_000_000)
        if source is None:
            self.skipTest("WARNING: reference MP3 could not be buffered in RAM")
        worker = None
        try:
            position = 0.940091
            playback_end = 176.7794
            played_seconds = 0.0
            for attempt in range(app.PREMATURE_AUDIO_EOF_MAX_RETRIES + 1):
                command = app.matrixmixer_inspired_ffmpeg_command(
                    app.direct_ffmpeg_executable(), MAGIC_JOHNSON,
                    position, 100, 1.0, 7, 0, 96000, 24,
                    end_seconds=playback_end,
                    bass_boost_enabled=False,
                    bass_boost_percent=0,
                    reduce_bass_when_locked=False,
                    locked_bass_reduction_percent=0,
                    session_locked=False,
                    live_bass=True,
                    input_url=source.url if attempt == 0 else None,
                )
                worker = app.IsolatedWaveOutProcess({
                    "command": command, "output_channels": 7,
                    "sample_rate": 96000, "bit_depth": 24,
                    "buffer_ms": 250, "volume": 0,
                    "outputs": [{"device": 0, "delay_ms": 0}],
                })
                last_clock = None
                deadline = time.monotonic() + 240.0
                while worker.poll() is None and time.monotonic() < deadline:
                    sample = worker.playback_clock
                    if isinstance(sample, dict):
                        last_clock = sample
                    time.sleep(0.05)
                self.assertEqual(0, worker.poll(), worker._last_error)
                self.assertIsNotNone(worker.playback_started_at)
                segment_seconds = float(last_clock["seconds"]) if last_clock else 0.0
                played_seconds += segment_seconds
                end_position = position + segment_seconds
                remaining = app.premature_audio_eof_remaining(playback_end, end_position)
                print(
                    f"muted segment {attempt + 1}: {segment_seconds:.2f}s, "
                    f"end={end_position:.2f}s, remaining={remaining:.2f}s",
                    flush=True,
                )
                worker.wait(timeout=5)
                worker = None
                if not remaining:
                    break
                position = max(0.940091, end_position - 0.05)
            self.assertGreaterEqual(played_seconds, 170.0, "the song was not played through")
            self.assertEqual(0.0, remaining, "the song still ended prematurely")
        finally:
            if worker is not None:
                if worker.poll() is None:
                    worker.kill()
                worker.wait(timeout=5)
            source.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)

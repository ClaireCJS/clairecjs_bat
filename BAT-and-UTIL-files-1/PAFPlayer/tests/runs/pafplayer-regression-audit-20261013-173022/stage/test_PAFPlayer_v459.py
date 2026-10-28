"""Real decode and natural-completion regressions; never opens an audio device."""
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock
import wave

import numpy as np
import PAFPlayer as app


class CompleteDecodedEnding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        executable = shutil.which('ffmpeg')
        if not executable:
            raise unittest.SkipTest('FFmpeg is required for real PCM decoding')
        cls.executable = Path(executable)
        # Retained with the isolated runner's fixtures for inspection.
        cls.audio = Path(tempfile.mkdtemp(prefix='v459-ending-')) / 'ending.wav'
        cls.rate = 48000
        timeline = np.arange(cls.rate * 12, dtype=np.float64) / cls.rate
        frequency = np.where(timeline >= 11, 1429., 220.)
        samples = (np.sin(2 * np.pi * frequency * timeline) * 12000).astype('<i2')
        with wave.open(str(cls.audio), 'wb') as output:
            output.setparams((1, 2, cls.rate, 0, 'NONE', 'not compressed'))
            output.writeframes(samples.tobytes())

    def assert_segment(self, speed, start=0., end=12., *, marker=True,
                       channels=2, rate=48000, depth=16):
        with mock.patch.object(app, 'probe_audio_stream_layout', return_value=(1, 'mono')):
            command = app.matrixmixer_inspired_ffmpeg_command(
                self.executable, self.audio, start, 100, speed, channels, 0,
                rate, depth, end_seconds=end,
            )
        decoded = subprocess.run(
            command, capture_output=True, timeout=30,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                          | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0),
        )
        self.assertEqual(decoded.returncode, 0, decoded.stderr.decode('utf-8', errors='replace'))
        channel_count = app.MM_CHANNEL_COUNTS[channels]
        if depth == 24:
            octets = np.frombuffer(decoded.stdout, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
            packed = octets[:, 0] | (octets[:, 1] << 8) | (octets[:, 2] << 16)
            pcm = ((packed ^ 0x800000) - 0x800000).reshape(-1, channel_count)
        else:
            pcm = np.frombuffer(decoded.stdout, dtype='<i2').reshape(-1, channel_count)
        expected_seconds = ((12. if end is None else end) - start) / speed
        self.assertAlmostEqual(len(pcm) / rate, expected_seconds, delta=.06)
        tail = pcm[-rate // 4:, 0].astype(np.float64)
        magnitudes = np.abs(np.fft.rfft(tail * np.hanning(len(tail))))
        peak = np.fft.rfftfreq(len(tail), 1 / rate)[np.argmax(magnitudes)]
        self.assertAlmostEqual(peak, 1429. if marker else 220., delta=10.)

    def test_ninety_percent_speed_keeps_final_tone(self):
        self.assert_segment(.9)

    def test_half_speed_keeps_final_tone(self):
        self.assert_segment(.5)

    def test_normal_speed_keeps_final_tone(self):
        self.assert_segment(1.)

    def test_fast_speed_keeps_final_tone(self):
        self.assert_segment(1.5)

    def test_seek_near_ending_at_slow_speed_keeps_tail(self):
        self.assert_segment(.9, start=9.)

    def test_fast_bounded_segment_excludes_audio_beyond_source_end(self):
        self.assert_segment(1.5, start=7., end=10., marker=False)

    def test_unknown_duration_decodes_to_eof(self):
        self.assert_segment(.9, start=7., end=None)

    def test_surround_96khz_24bit_keeps_final_tone(self):
        self.assert_segment(.9, channels=7, rate=96000, depth=24)


class NaturalCompletion(unittest.TestCase):
    def test_decoder_eof_does_not_finish_until_queued_pcm_drains(self):
        process = app.MatrixMixerInspiredWaveOutProcess.__new__(app.MatrixMixerInspiredWaveOutProcess)
        process.channels = process.output_channels = 2
        process.container_bits, process.sample_rate = 16, 48000
        process.initial_delay_ms = 0
        process._stop = threading.Event()
        process._avrt = process._done_event = process.start_barrier = None
        process._waveout_preroll_paused = True
        process.preroll_buffers, process.pending_buffer_limit = 4, 8
        process._last_meter_update = time.monotonic()
        process._meter_source_id = 'v459-test'
        process._returncode = None
        process._last_error = ''
        process._wave_handle = None
        process._ffmpeg = mock.Mock(stdout=io.BytesIO(b'\0' * (app.MM_INSPIRED_BUFFER_FRAMES * 4 + 40)))
        process._ffmpeg.wait.return_value = 0
        process._winmm = mock.Mock()
        for method in ('waveOutPrepareHeader', 'waveOutWrite', 'waveOutRestart'):
            getattr(process._winmm, method).return_value = app.MM_MMSYSERR_NOERROR
        process._close_waveout = mock.Mock()
        draining, consumed = threading.Event(), threading.Event()
        released = []

        def release(header):
            draining.set()
            if not consumed.wait(5):
                raise RuntimeError('Test consumer did not release the queued audio')
            released.append(header.dwBufferLength)

        process._release_header = release
        process._thread = threading.Thread(target=process._pump)
        with mock.patch.object(app, 'publish_matrix_output_levels'), mock.patch.object(app, 'remove_matrix_output_levels'):
            process._thread.start()
            try:
                self.assertTrue(draining.wait(3))
                self.assertIsNone(process.poll())
                process._ffmpeg.wait.assert_not_called()
                process._close_waveout.assert_not_called()
                process._winmm.waveOutRestart.assert_called_once()
            finally:
                consumed.set()
                process._thread.join(5)
        self.assertFalse(process._thread.is_alive())
        self.assertEqual(process.poll(), 0, process._last_error)
        self.assertEqual(released, [app.MM_INSPIRED_BUFFER_FRAMES * 4, 40])
        process._ffmpeg.wait.assert_called_once()
        process._ffmpeg.kill.assert_not_called()
        process._close_waveout.assert_called_once()

    def test_natural_close_does_not_reset_device(self):
        process = app.MatrixMixerInspiredWaveOutProcess.__new__(app.MatrixMixerInspiredWaveOutProcess)
        process._stop = threading.Event()
        process._winmm, process._wave_handle = mock.Mock(), None
        process._sample_playback_clock = mock.Mock()
        process._close_waveout()
        process._winmm.waveOutReset.assert_not_called()
        process._winmm.waveOutClose.assert_called_once()

    def test_next_song_waits_for_every_output_endpoint(self):
        first, last = mock.Mock(), mock.Mock()
        first.poll.return_value, last.poll.return_value = 0, None
        process = app.MultiOutputWaveOutProcess([first, last])
        self.assertIsNone(process.poll())
        last.poll.return_value = 0
        self.assertEqual(process.poll(), 0)
        first.kill.assert_not_called()
        last.kill.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""Live bass transport, same-stream lock changes, and real silent PCM checks."""
import ctypes
import io
import json
import math
from pathlib import Path
import queue
import subprocess
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest import mock
import wave

import numpy as np
import PAFPlayer as app
import test_v590_locked_bass as previous
import probe_v482_track_renderer as probe


def bridge(ffmpeg=None):
    p = app.MatrixMixerInspiredWaveOutProcess.__new__(app.MatrixMixerInspiredWaveOutProcess)
    p._bass_command_lock = threading.Lock()
    p._live_bass = True
    p._last_bass_db = None
    p._stop = threading.Event()
    p._ffmpeg = ffmpeg or mock.Mock(stdin=io.BytesIO())
    if ffmpeg is None: p._ffmpeg.poll.return_value = None
    p._winmm = mock.Mock()
    return p


class LiveBassTests(unittest.TestCase):
    def test_private_command_is_bounded_and_duplicates_do_not_accumulate(self):
        p = bridge()
        for gain in (-14, -14, 0, 1000, -1000): self.assertTrue(p.set_bass_db(gain))
        self.assertEqual(b'cbass@paf_bass -1 gain -14\ncbass@paf_bass -1 gain 0\n'
                         b'cbass@paf_bass -1 gain 20\ncbass@paf_bass -1 gain -20\n',
                         p._ffmpeg.stdin.getvalue())
        self.assertFalse(p._winmm.mock_calls)
        p._ffmpeg.terminate.assert_not_called(); p._ffmpeg.kill.assert_not_called()

    def test_invalid_requests_closed_pipe_and_finished_decoder_fail_safely(self):
        for gain in (float('nan'), float('inf'), '0\nq', None):
            p = bridge(); self.assertFalse(p.set_bass_db(gain)); self.assertFalse(p._ffmpeg.stdin.getvalue())
        p = bridge(); p._ffmpeg.stdin.close(); self.assertFalse(p.set_bass_db(-14))
        p = bridge(); p._ffmpeg.poll.return_value = 0; self.assertFalse(p.set_bass_db(-14))
        p = bridge(); p._stop.set(); self.assertFalse(p.set_bass_db(-14))
        p = bridge(); p._live_bass = False; self.assertFalse(p.set_bass_db(-14))

    def test_owner_command_does_not_reset_the_clock(self):
        p = app.IsolatedWaveOutProcess.__new__(app.IsolatedWaveOutProcess)
        p._process = mock.Mock(stdin=io.StringIO()); p._process.poll.return_value = None
        p._stop_sent = False; p._clock_origin = 18.5; p._started_at = 123.
        for gain in (-14, 0, 80): self.assertTrue(p.set_bass_db(gain))
        self.assertEqual([{'bass_db': -14.}, {'bass_db': 0.}, {'bass_db': 20.}],
                         [json.loads(s) for s in p._process.stdin.getvalue().splitlines()])
        self.assertEqual((18.5, 123.), (p._clock_origin, p._started_at))
        self.assertFalse(p.set_bass_db(float('nan')))
        p._stop_sent = True; self.assertFalse(p.set_bass_db(-14))
        p._process.terminate.assert_not_called()

    def test_every_output_receives_lock_and_unlock_without_recreation(self):
        incoming = queue.Queue()
        class Input:
            def __iter__(self): return self
            def __next__(self): return incoming.get(timeout=5)
        outputs = []
        def factory(*args, **kwargs):
            p = mock.Mock(_last_error='', playback_started_at=1., playback_clock=None,
                          queued_audio_ms=250., underruns=0)
            p.poll.return_value = None; outputs.append(p); return p
        config = dict(command=['ffmpeg'], output_channels=7, sample_rate=96000,
                      bit_depth=24, buffer_ms=250,
                      outputs=[dict(device=0, delay_ms=0), dict(device=2, delay_ms=30)])
        output = io.StringIO()
        thread = threading.Thread(target=app.run_isolated_audio_worker,
                                  args=(config, Input(), output), kwargs={'process_factory': factory})
        with mock.patch.object(app, 'matrix_output_levels_snapshot', return_value={}):
            thread.start()
            try:
                until = time.monotonic()+3
                while '"ready": true' not in output.getvalue() and time.monotonic()<until: time.sleep(.01)
                self.assertEqual(2, len(outputs))
                incoming.put('{"bass_db": -14}\n'); incoming.put('{"bass_db": 0}\n')
                until = time.monotonic()+3
                while outputs[-1].set_bass_db.call_count<2 and time.monotonic()<until: time.sleep(.01)
                for p in outputs:
                    self.assertEqual([mock.call(-14), mock.call(0)], p.set_bass_db.call_args_list)
                    p.kill.assert_not_called(); p.set_paused.assert_not_called()
            finally:
                incoming.put('stop\n'); thread.join(5)
            self.assertFalse(thread.is_alive())

    def test_named_shelf_stays_before_expansion_at_unity_and_nonzero(self):
        for channels in (2, 5, 7, 12):
            for locked in (False, True):
                with mock.patch.object(app, 'probe_audio_stream_layout', return_value=(2, 'stereo')):
                    command = app.matrixmixer_inspired_ffmpeg_command(
                        Path('ffmpeg.exe'), Path('song.wav'), 12, 100, 1., channels, 0,
                        bass_boost_enabled=False, bass_boost_percent=0, reduce_bass_when_locked=True,
                        locked_bass_reduction_percent=70, session_locked=locked, live_bass=True)
                self.assertIn('-stdin', command); self.assertNotIn('-nostdin', command)
                filters = command[command.index('-af')+1]
                self.assertEqual(1, filters.count('bass@paf_bass='))
                self.assertIn('g=-14:' if locked else 'g=0:', filters)
                if channels != 2: self.assertLess(filters.index('bass@'), filters.index('pan='))

    def test_launch_enables_private_pipe_for_actual_buffered_renderer(self):
        with mock.patch.object(app, 'direct_ffmpeg_executable', return_value=Path('ffmpeg.exe')), \
             mock.patch.object(app, 'matrixmixer_inspired_ffmpeg_command', return_value=['ffmpeg.exe']) as command, \
             mock.patch.object(app, 'waveout_output_devices', return_value=[{'value': -1}]), \
             mock.patch.object(app, 'load_multi_output_latencies_ms', return_value={}), \
             mock.patch.object(app, 'IsolatedWaveOutProcess'):
            app.launch_matrixmixer_inspired_renderer(Path('song.wav'), 0, 100, 1., 7, 0, 96000,
                                                     end_seconds=None, replaygain_info=None)
        self.assertTrue(command.call_args.kwargs['live_bass'])

    def test_web_bass_change_uses_same_live_process(self):
        local, ns = probe.capture_renderer(170, 47)
        apply = local['apply_web_direct_setting']
        cells = dict(zip(apply.__code__.co_freevars, apply.__closure__))
        live = mock.Mock(); live.set_bass_db.return_value = True
        cells['process'].cell_contents = live
        settings = dict(ReduceBassWhenLocked=0, LockedBassReductionPercent=70,
                        BassBoostEnabled=0, BassBoostPercent=0)
        with mock.patch.dict(ns, load_bass_settings=lambda: dict(settings),
                             save_player_setting_value=lambda k,v: settings.__setitem__(k,v),
                             windows_session_is_locked=lambda: True):
            self.assertEqual((True, False), apply('web-set:reduce_bass_when_locked:1', 100.))
            self.assertEqual((True, False), apply('web-set:reduce_bass_when_locked:0', 101.))
        self.assertEqual([mock.call(-14.), mock.call(0.)], live.set_bass_db.call_args_list)
        live.terminate.assert_not_called(); live.kill.assert_not_called()


class LiveLockTransition(unittest.TestCase):
    def test_lock_and_unlock_keep_position_decoder_and_audio_queue(self):
        previous.BassTransitionTests.setUpClass()
        case = previous.BassTransitionTests(); case.setUp()
        case.process.set_bass_db = mock.Mock(return_value=True)
        case.poll(100); case.locked=True; case.poll(101); case.locked=False; case.poll(102)
        self.assertEqual([mock.call(-14.), mock.call(0.)], case.process.set_bass_db.call_args_list)
        case.stop.assert_not_called(); case.ns['record_segment'].assert_not_called()
        self.assertEqual(0, case.ns['position']); self.assertFalse(case.ns['natural_eof'])

    def test_unavailable_live_pipe_keeps_legacy_same_song_fallback(self):
        previous.BassTransitionTests.setUpClass()
        case = previous.BassTransitionTests(); case.setUp()
        case.process.set_bass_db = mock.Mock(return_value=False)
        case.test_lock_and_unlock_restart_same_song_without_natural_eof()


class DecodedContinuity(unittest.TestCase):
    def test_real_96khz_surround_pcm_changes_bass_without_missing_frames(self):
        """One decoder, no audio device: drain real 24-bit PCM and inspect both transitions."""
        rate, duration, channels = 96000, 7, 8
        folder = Path(tempfile.mkdtemp(prefix='v591-live-bass-'))
        path = folder/'continuous.wav'
        t = np.arange(48000*duration)/48000
        x = .08*np.sin(2*np.pi*40*t)+.08*np.sin(2*np.pi*1000*t)
        # The final 250 ms contain a marker so the test also detects a clipped ending.
        x += (t>duration-.25)*.02*np.sin(2*np.pi*2000*t)
        with wave.open(str(path), 'wb') as out:
            out.setparams((2,2,48000,0,'NONE','not compressed'))
            out.writeframes(np.repeat((x*32767).astype('<i2')[:,None],2,axis=1).tobytes())
        with mock.patch.object(app, 'probe_audio_stream_layout', return_value=(2,'stereo')):
            cmd = app.matrixmixer_inspired_ffmpeg_command(
                app.direct_ffmpeg_executable(), path, 0, 100, 1., 7, 0, rate, 24,
                bass_boost_enabled=False, bass_boost_percent=0, reduce_bass_when_locked=True,
                locked_bass_reduction_percent=70, session_locked=False, live_bass=True)
        cmd.insert(cmd.index('-i'), '-re')
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        audio, errors, arrivals = [], [], []
        def read():
            while True:
                data=p.stdout.read(rate*channels*3//100)
                if not data: break
                audio.append(data); arrivals.append(time.monotonic())
        reader=threading.Thread(target=read,daemon=True)
        logger=threading.Thread(target=lambda:errors.append(p.stderr.read()),daemon=True)
        renderer=bridge(p); pid=p.pid
        reader.start(); logger.start()
        try:
            time.sleep(1.5); self.assertTrue(renderer.set_bass_db(-14))
            time.sleep(3); self.assertTrue(renderer.set_bass_db(0))
            self.assertEqual(pid,p.pid); self.assertIsNone(p.poll())
            p.wait(timeout=12)
        finally:
            if p.poll() is None: p.kill(); p.wait()
            p.stdin.close(); reader.join(3); logger.join(3); p.stdout.close(); p.stderr.close()
        self.assertEqual(0,p.returncode,b''.join(errors).decode(errors='replace'))
        octets=np.frombuffer(b''.join(audio),dtype=np.uint8).reshape(-1,3).astype(np.int32)
        values=octets[:,0]|(octets[:,1]<<8)|(octets[:,2]<<16)
        pcm=((values^0x800000)-0x800000).reshape(-1,channels)
        self.assertEqual(rate*duration,len(pcm))
        def magnitude(begin,freq):
            a=pcm[int(begin*rate):int((begin+.5)*rate),0].astype(float)
            return abs(np.dot(a,np.exp(-2j*np.pi*freq*np.arange(len(a))/rate)))/len(a)
        low=20*math.log10(magnitude(3,40)/magnitude(.5,40))
        high=20*math.log10(magnitude(3,1000)/magnitude(.5,1000))
        self.assertLess(low,-10); self.assertLess(abs(high),.5)
        self.assertLess(abs(20*math.log10(magnitude(5.5,40)/magnitude(.5,40))),.1)
        # Every 10 ms block, including the two transitions, contains the continuing treble.
        rms=np.sqrt(np.mean(pcm[:,0].astype(float).reshape(-1,rate//100)**2,axis=1))
        self.assertGreater(float(rms[10:].min()),100000)
        tail=pcm[-rate//8:,0].astype(float)
        self.assertGreater(abs(np.dot(tail,np.exp(-2j*np.pi*2000*np.arange(len(tail))/rate)))/len(tail),50000)
        self.assertEqual(2,b''.join(errors).count(b'ret:0'))
        renderer._winmm.waveOutReset.assert_not_called()
        report=dict(frames=len(pcm),seconds=len(pcm)/rate,rate=rate,channels=channels,bits=24,
                    low_db=low,high_db=high,minimum_10ms_rms=float(rms[10:].min()),
                    maximum_delivery_gap_ms=max(np.diff(arrivals))*1000,
                    command_replies=b''.join(errors).decode(errors='replace'))
        print('V591 real PCM continuity: '+json.dumps(report))


if __name__ == '__main__': unittest.main()

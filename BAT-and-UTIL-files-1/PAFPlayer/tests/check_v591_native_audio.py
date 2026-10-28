"""Muted native WaveOut lifecycle check in guarded staging; no player commands."""
from pathlib import Path

# Reuse the retained-isolation setup, but do not run the unit-test suite.
setup = Path(__file__).with_name('verify_v591_live_bass.py').read_text(encoding='utf-8')
exec(compile(setup.split('suite = unittest.TestSuite()')[0], str(__file__), 'exec'))
import time
import wave
import numpy as np

rate = 48000
t = np.arange(rate*6)/rate
samples = (.05*np.sin(2*np.pi*40*t)+.05*np.sin(2*np.pi*1000*t))*32767
audio = work/'native-bass.wav'
with wave.open(str(audio), 'wb') as stream:
    stream.setparams((2,2,rate,0,'NONE','not compressed'))
    stream.writeframes(np.repeat(samples.astype('<i2')[:,None],2,axis=1).tobytes())
with mock.patch.object(app, 'probe_audio_stream_layout', return_value=(2,'stereo')):
    command = app.matrixmixer_inspired_ffmpeg_command(
        app.direct_ffmpeg_executable(), audio, 0, 100, 1., 7, 0, 96000, 24,
        bass_boost_enabled=False, bass_boost_percent=0, reduce_bass_when_locked=False,
        locked_bass_reduction_percent=70, session_locked=False, live_bass=True)
config = dict(command=command, output_channels=7, sample_rate=96000, bit_depth=24,
              buffer_ms=250, volume=0, outputs=[dict(device=-1,delay_ms=0)])
p = app.IsolatedWaveOutProcess(config)
pid, changes, samples = p.pid, [], []
deadline = time.monotonic()+20
try:
    while p.poll() is None and time.monotonic()<deadline:
        clock = p.playback_clock
        if clock:
            samples.append(dict(clock=clock, health=p.audio_health))
            elapsed = clock['seconds']
            if not changes and elapsed>=1:
                assert p.set_bass_db(-14); changes.append(dict(at=elapsed,gain=-14,pid=p.pid))
            elif len(changes)==1 and elapsed>=3:
                assert p.set_bass_db(0); changes.append(dict(at=elapsed,gain=0,pid=p.pid))
        time.sleep(.02)
    assert p.poll()==0, (p.poll(),p._last_error)
    assert len(changes)==2 and all(c['pid']==pid for c in changes), changes
    assert samples and samples[-1]['clock']['seconds']>=5.9, samples[-1:]
    assert max(s['health']['underruns'] for s in samples)==0
finally:
    if p.poll() is None: p.kill()
    p.wait(timeout=3)
report=dict(version='V591', volume=0, audible_output=False, real_waveout=True,
            pid=pid, rate=96000, channels=8, bit_depth=24, changes=changes,
            samples=samples, source_sha256=hashlib.sha256((stage/'PAFPlayer.py').read_bytes()).hexdigest(),
            blocked_writes=blocks, stage=str(stage))
path=unique(root/'tests/reports'/('v591-native-muted-'+stamp+'.json'))
with path.open('x',encoding='utf-8') as stream: json.dump(report,stream,indent=2)
print(json.dumps(dict(report=str(path),changes=changes,frames_seconds=samples[-1]['clock']['seconds'],
                      max_underruns=max(s['health']['underruns'] for s in samples)),indent=2))

"""Real decoder/clock checks using generated, muted audio; no music files changed."""
from pathlib import Path
import json
import math
import re
import struct
import subprocess
import sys
import time
import wave

import play_audio_file as p
from pafplayer_v416_edit import unique

sys.stdout.reconfigure(encoding='utf-8')
root = Path(__file__).resolve().parent
report = {}

# Actual FFmpeg analysis: two artificial drum-like bursts followed by silence.
fixture = unique(root / 'pafplayer_v416_timing_fixture.wav')
rate = 48000
with wave.open(str(fixture), 'wb') as wav:
    wav.setnchannels(1)
    wav.setsampwidth(2)
    wav.setframerate(rate)
    frames = bytearray()
    for sample in range(rate * 3):
        t = sample / rate
        burst = .5 <= t < .6 or 1.5 <= t < 1.6
        amplitude = .7 * math.sin(2 * math.pi * 100 * t) if burst else 0
        frames.extend(struct.pack('<h', round(32767 * amplitude)))
    wav.writeframes(frames)

timeline = p.build_audio_spectrum_timeline(fixture, 48)
data, width, fps = timeline
active_frames = [index for index in range(len(data) // width) if any(data[index * width:(index + 1) * width])]
assert active_frames, 'FFmpeg produced no spectrum data'
first = active_frames[0] / fps
last = active_frames[-1] / fps
assert .40 <= first <= .60, first
assert 1.50 <= last < 1.75, last
assert not any(p.spectrum_frame_interpolated_at(timeline, 2.0)), 'Spectrum survives silence'
pulses = p.ProgressBeatTimeline()
pulses.append(data, width, fps)
assert all(pulses.at(2.0, detector) == 0 for detector in range(1, 6))
report['ffmpeg'] = {'first_burst_source_seconds': first, 'last_nonzero_source_seconds': last,
                    'silence_at_2_seconds': True, 'frames': len(data) // width}

html = p._paf_web_html()
javascript = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', html, re.S))
syntax = subprocess.run(['node', '--check'], input=javascript, encoding='utf-8', text=True, capture_output=True)
assert syntax.returncode == 0, syntax.stderr
start = javascript.index('function timelineSpectrumAt(')
end = javascript.index('async function timelineTick', start)
behavior = '''const assert=require('node:assert/strict');
let spectrumTimeline={source:'track',position:1,playing:true,speed:2,at:1000,fps:2,start_frame:2,width:1,raw:new Uint8Array([20,40,60,0])};
''' + javascript[start:end] + '''
assert.deepEqual([...timelineSpectrumAt(1000)],[20]);
assert.deepEqual([...timelineSpectrumAt(1125)],[30]);
assert.deepEqual([...timelineSpectrumAt(1250)],[40]);
spectrumTimeline.playing=false;
assert.deepEqual([...timelineSpectrumAt(1500)],[20]);
spectrumTimeline.position=99;
assert.equal(timelineSpectrumAt(1500).length,0);
spectrumTimeline.source='live';assert.equal(timelineSpectrumAt(1500),null);
console.log('timestamped browser frame selection passed');
'''
js_test = subprocess.run(['node'], input=behavior, encoding='utf-8', text=True, capture_output=True)
assert js_test.returncode == 0, js_test.stderr
report['browser_javascript'] = {'syntax': 'passed', 'timestamp_selection_pause_speed_and_expiry': 'passed'}

# Exercise the installed Chafa binary, including its actual ANSI parser.
grid = tuple(tuple((row * 40, column * 20, 70) for column in range(8)) for row in range(4))
cells = p._render_chafa_symbol_art_cells(grid, 8, 4)
assert len(cells) == 4 and all(len(row) == 8 for row in cells), 'Chafa geometry/parser failed'
report['chafa'] = {'symbol_cells': [len(cells[0]), len(cells)], 'supported': True}

if '--native' in sys.argv:
    process = None
    samples = []
    try:
        # The fixture is muted before it reaches the output device.
        command = [str(p.direct_ffmpeg_executable()), '-v', 'error', '-i', str(fixture),
                   '-af', 'volume=0', '-ar', str(rate), '-ac', '2', '-f', 's16le', '-']
        process = p.MatrixMixerInspiredWaveOutProcess(command, 2, rate, -1, 16, target_buffer_ms=100)
        deadline = time.monotonic() + 8
        while process.poll() is None and time.monotonic() < deadline:
            clock = process.playback_clock
            if clock is not None:
                samples.append(clock)
            time.sleep(.02)
        assert process.poll() == 0, (process.poll(), process._last_error)
        assert len(samples) > 10, len(samples)
        assert samples[-1]['seconds'] > 2.7, samples[-1]
        assert all(b['seconds'] >= a['seconds'] for a, b in zip(samples, samples[1:]))
        report['native_waveout'] = {'muted': True, 'samples': len(samples),
            'first_seconds': samples[0]['seconds'], 'last_seconds': samples[-1]['seconds'],
            'monotonic': True}
    finally:
        if process is not None:
            p.stop_process(process)

destination = unique(root / 'pafplayer_v416_validation.json')
destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
print(destination)

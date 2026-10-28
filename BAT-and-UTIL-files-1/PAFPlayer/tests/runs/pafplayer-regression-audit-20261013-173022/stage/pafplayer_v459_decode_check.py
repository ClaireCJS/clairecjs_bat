"""Decode-only reproduction of source-end/tempo truncation; never opens audio."""
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest import mock
import wave

import numpy as np

source_file = Path(sys.argv[1]).resolve()
destination = Path(sys.argv[2]).resolve()
destination.mkdir(exist_ok=False)
sys.argv = [str(source_file), '--unit-tests']
spec = importlib.util.spec_from_file_location('eof_player', source_file)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)

rate = 48000
audio = destination / 'fifty-seconds-final-tone.wav'
time_axis = np.arange(rate * 50, dtype=np.float64) / rate
frequency = np.where(time_axis >= 49, 1429., 220.)
samples = (np.sin(2*np.pi*frequency*time_axis)*12000).astype('<i2')
with wave.open(str(audio), 'wb') as output:
    output.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
    output.writeframes(samples.tobytes())

results = []
with mock.patch.object(app, 'probe_audio_stream_layout', return_value=(1, 'mono')):
    for speed, start, end in ((.9, 0., 50.), (.5, 0., 50.), (1., 0., 50.), (1.5, 0., 50.), (.9, 40., 50.), (1.5, 7., 42.)):
        command = app.matrixmixer_inspired_ffmpeg_command(
            Path(app.shutil.which('ffmpeg')), audio, start, 100, speed, 2, 0,
            rate, 16, end_seconds=end,
        )
        decoded = subprocess.run(command, capture_output=True, timeout=30,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0))
        if decoded.returncode:
            raise RuntimeError(decoded.stderr.decode('utf-8', errors='replace'))
        pcm = np.frombuffer(decoded.stdout, dtype='<i2').reshape(-1, 2)
        tail = pcm[-rate//2:, 0].astype(np.float64)
        magnitudes = np.abs(np.fft.rfft(tail*np.hanning(len(tail))))
        peak_hz = float(np.fft.rfftfreq(len(tail), 1/rate)[int(np.argmax(magnitudes))])
        row = dict(speed=speed, start=start, end=end, output_seconds=len(pcm)/rate,
            expected_seconds=(end-start)/speed, tail_peak_hz=peak_hz,
            duration_before_input=command.index('-t') < command.index('-i'))
        results.append(row)
        print(json.dumps(row), flush=True)
report = {'source':str(source_file), 'sha256':hashlib.sha256(source_file.read_bytes()).hexdigest(), 'results':results}
with (destination / 'results.json').open('x', encoding='utf-8') as output:
    json.dump(report, output, indent=2)

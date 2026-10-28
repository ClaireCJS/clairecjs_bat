"""Silent, bounded real FFmpeg stdin-command/PCM probe; no output device opened."""
from datetime import datetime
import json
from pathlib import Path
import subprocess
import threading
import time
import numpy as np

root = Path(__file__).resolve().parents[1]
exe = r'C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\ffmpeg.exe'
cmd = [exe, '-hide_banner', '-loglevel', 'error', '-stdin', '-re', '-f', 'lavfi',
       '-i', 'aevalsrc=0.08*sin(2*PI*40*t)+0.08*sin(2*PI*1000*t):s=48000:d=7',
       '-af', 'bass@paf_bass=g=0:f=120:w=0.7', '-f', 's16le', 'pipe:1']
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
chunks, errors = [], []
reader = threading.Thread(target=lambda: chunks.append(p.stdout.read()), daemon=True)
logger = threading.Thread(target=lambda: errors.append(p.stderr.read()), daemon=True)
reader.start(); logger.start()
try:
    for delay, gain in ((1.5, -14), (3., 0)):
        time.sleep(delay)
        p.stdin.write(f'cbass@paf_bass -1 gain {gain}\n'.encode('ascii')); p.stdin.flush()
    p.wait(timeout=12)
finally:
    if p.poll() is None: p.kill(); p.wait()
    p.stdin.close(); reader.join(2); logger.join(2)
    p.stdout.close(); p.stderr.close()
x = np.frombuffer(b''.join(chunks), dtype='<i2').astype(float)
def level(begin, freq):
    a = x[int(begin*48000):int((begin+.5)*48000)]
    return abs(np.dot(a, np.exp(-2j*np.pi*freq*np.arange(len(a))/48000))) / len(a)
levels = {str(t): {str(f): level(t, f) for f in (40,1000)} for t in (.5,3,5.5)}
report = dict(command=cmd, returncode=p.returncode, frames=len(x), levels=levels,
              stderr=b''.join(errors).decode(errors='replace'))
path=root/'tests/reports'/('v591-ffmpeg-command-probe-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
with path.open('x',encoding='utf-8') as out: json.dump(report,out,indent=2)
print(json.dumps(report,indent=2))
print(path)

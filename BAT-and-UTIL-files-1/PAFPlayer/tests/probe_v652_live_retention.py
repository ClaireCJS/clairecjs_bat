"""Three-minute read-only retention sample; no commands, settings writes or GC requests."""
from datetime import datetime
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
def get(route):
    with urllib.request.urlopen('http://127.0.0.1:666'+route, timeout=5) as response:
        return json.load(response)

hello = get('/api/remote-tray/hello?timeline=0')
assert hello.get('official') is True and str(hello.get('program', '')).casefold() == 'pafplayer'
first = get('/api/runtime-diagnostics')
started = time.perf_counter(); samples = []; printed = -30; errors = []
while time.perf_counter()-started < 180:
    tick = time.perf_counter()
    try:
        diag = get('/api/runtime-diagnostics')
        assert diag['pid'] == first['pid'], 'Player process changed during sampling'
        status = get('/api/status')
        row = {'elapsed': round(tick-started, 3), 'request_ms': round(1000*(time.perf_counter()-tick), 3),
               'diagnostics': diag, 'status': {k:v for k,v in status.items() if
                   k in ('visualizer_perf', 'position_seconds', 'track_visit', 'paused',
                         'console_karaoke_enabled', 'artwork_karaoke_enabled', 'floating_lyrics_enabled')
                   or k.startswith(('audio_health', 'audio_isolat'))}}
        row['has_lyric'] = bool(status.get('lyric'))
        samples.append(row)
        if tick-started-printed >= 30:
            printed = tick-started
            print(json.dumps({'elapsed':round(printed,1), 'memory':diag['memory'],
                              'fps':(status.get('visualizer_perf') or {}).get('fps'),
                              'gc2':diag['gc_collections'][2]['collections']}), flush=True)
    except Exception as exc:
        errors.append({'elapsed':round(tick-started,3), 'error':str(exc)})
        if isinstance(exc, AssertionError):break
    time.sleep(max(0,2-(time.perf_counter()-tick)))
name = 'v652-live-retention-'+hello['version']+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')
report = ROOT/'tests/reports'/(name+'.json'); n = 0
while report.exists():
    n += 1; report = ROOT/'tests/reports'/(name+f' ({n}).json')
with report.open('x', encoding='utf8') as stream:
    json.dump({'version':hello['version'], 'pid':first['pid'], 'initial':first,
               'samples':samples, 'errors':errors,
               'limitations':'Short whole-player observation, not proof of multi-hour stability. HTTP time is not frame latency.'},stream,indent=2)
print(report)

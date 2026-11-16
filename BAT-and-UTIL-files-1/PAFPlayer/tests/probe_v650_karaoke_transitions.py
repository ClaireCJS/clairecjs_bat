"""Read-only bounded trace around karaoke gaps; no playback/settings commands."""
from datetime import datetime
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
def get(route):
    with urllib.request.urlopen('http://127.0.0.1:666'+route,timeout=5) as r:return json.load(r)
hello=get('/api/remote-tray/hello?timeline=0')
assert hello.get('official') is True and hello.get('program','').casefold()=='pafplayer'
assert int(hello['version'].lstrip('Vv'))>=648
started=time.perf_counter();samples=[];status_at=0.;printed=0.;last=None
while time.perf_counter()-started<45:
    tick=time.perf_counter()
    diag=get('/api/runtime-diagnostics?stacks=1')
    row={'elapsed':tick-started,'request_ms':1000*(time.perf_counter()-tick),'threads':diag['thread_stacks']}
    if tick-status_at>=.5:
        status_at=tick;s=get('/api/status')
        row['status']={k:s.get(k) for k in ('position_seconds','track_visit','lyric_timeline_revision','visualizer_perf','paused')}
        row['status']['has_lyric']=bool(s.get('lyric'))
        row['status']['cue_presence']=[[c[0],bool(c[1])] for c in s.get('lyric_timeline',[]) if isinstance(c,list) and len(c)>=2]
        state=(s.get('track_visit'),row['status']['has_lyric'])
        if state!=last or tick-printed>=10:
            print(json.dumps({'elapsed':round(tick-started,2),'position':s.get('position_seconds'),'has_lyric':row['status']['has_lyric']}),flush=True)
            last=state;printed=tick
    samples.append(row)
    time.sleep(max(0,.1-(time.perf_counter()-tick)))
name='v650-karaoke-transition-'+hello['version']+'-'+datetime.now().strftime('%Y%m%d-%H%M%S')
p=ROOT/'tests/reports'/(name+'.json');i=0
while p.exists():i+=1;p=ROOT/'tests/reports'/(name+f' ({i}).json')
with p.open('x',encoding='utf-8') as f:json.dump({'version':hello['version'],'samples':samples},f)
print(p)

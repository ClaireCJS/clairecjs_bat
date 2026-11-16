"""Read-only 20-second local stack capture; no playback commands or HUD toggle."""
from datetime import datetime
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:666'
def get(path):
    with urllib.request.urlopen(BASE+path,timeout=5) as response:
        return json.load(response)

hello=get('/api/remote-tray/hello?timeline=0')
assert hello.get('official') is True and str(hello.get('program','')).casefold()=='pafplayer'
assert int(str(hello['version']).lstrip('Vv'))>=648,'Restart into V648 or later first'
started=time.perf_counter();samples=[];last_perf=0.0
while time.perf_counter()-started<20:
    tick=time.perf_counter()
    result=get('/api/runtime-diagnostics?stacks=1')
    assert 'thread_stacks' in result
    row=dict(elapsed=tick-started,request_ms=(time.perf_counter()-tick)*1000,
             gc=result['gc_collections'],threads=result['thread_stacks'])
    if tick-last_perf>=2:
        last_perf=tick
        s=get('/api/status');row['perf']=s.get('visualizer_perf');row['has_lyric']=bool(s.get('lyric'))
        print(json.dumps(dict(elapsed=round(tick-started,1),request_ms=round(row['request_ms'],2),
                             fps=(row['perf'] or {}).get('fps'))),flush=True)
    samples.append(row)
    time.sleep(max(0,0.1-(time.perf_counter()-tick)))
name='v648-thread-stacks-'+datetime.now().strftime('%Y%m%d-%H%M%S')
report=ROOT/'tests/reports'/(name+'.json');collision=0
while report.exists():
    collision+=1;report=ROOT/'tests/reports'/(name+f' ({collision}).json')
with report.open('x',encoding='utf-8') as f:
    json.dump(dict(version=hello['version'],samples=samples),f)
print(report)

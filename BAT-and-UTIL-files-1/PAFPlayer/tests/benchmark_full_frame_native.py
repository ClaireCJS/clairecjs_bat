"""Offline exact-output experiment using the existing native full-row encoder."""
from datetime import datetime
import gc
import ast
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards,unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('full-frame-native-'+stamp));stage.mkdir()
with (stage/'PAFPlayer.py').open('xb') as f:f.write((ROOT/'PAFPlayer.py').read_bytes())
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):os.environ[key]=str(stage)
tempfile.tempdir=str(stage);sys.path.insert(0,str(stage));sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocked=install_guards(ROOT/'tests')
import PAFPlayer as app
assert app._visualizer_artwork_encoder() is not None
rng=random.Random(653);width=140;height=48
fixed=[bytes(rng.randrange(256) for _ in range(6))+b'A' for _ in range(width*height)]
frames=[]
for frame in range(200):
    data=b''.join(bytes(rng.randrange(256) for _ in range(6))+b'B' if (i+frame)%5==0 else color for i,color in enumerate(fixed))
    frames.append([data[n:n+width*7] for n in range(0,len(data),width*7)])
baseline=ast.parse((ROOT/'releases/PAFPlayer_v653_idle_art_music_dance.py').read_text(encoding='utf8'))
node=next(n for n in baseline.body if isinstance(n,ast.FunctionDef) and n.name=='_visualizer_native_rows_output')
ns=dict(vars(app));exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<V653 row formatter>','exec'),ns)
def original(rows):
    result=[]
    ns['_visualizer_native_rows_output'](rows,None,False,result,True,False,False,False,False,False)
    return result
def experimental(rows):
    result=[]
    app._visualizer_native_rows_output(rows,None,False,result,True,False,False,False,False,False)
    return result
results=[];expected=None
for name,fn in [('existing',original),('production-native',experimental)]:
    app._visualizer_packed_art_sgr.cache_clear();fn(frames[0]);gc.collect()
    before=gc.get_stats();begin=time.perf_counter();digest=hashlib.sha256()
    for rows in frames:digest.update(''.join(fn(rows)).encode('ascii'))
    elapsed=time.perf_counter()-begin
    if expected is None:expected=digest.hexdigest()
    results.append(dict(path=name,ms_per_frame=1000*elapsed/len(frames),identical=digest.hexdigest()==expected,
                        collections=[a['collections']-b['collections'] for a,b in zip(gc.get_stats(),before)]))
report=unique(ROOT/'tests/reports'/('full-frame-native-'+stamp+'.json'))
with report.open('x',encoding='utf8') as f:json.dump(dict(results=results,source_sha256=hashlib.sha256((stage/'PAFPlayer.py').read_bytes()).hexdigest(),
    stage=str(stage),blocked_writes=blocked,limitations='Offline row-formatting benchmark; not end-to-end live FPS or terminal write latency.'),f,indent=2)
print(json.dumps(results,indent=2));print(report)

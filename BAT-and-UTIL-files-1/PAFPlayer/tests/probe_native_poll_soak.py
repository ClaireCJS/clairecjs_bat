"""Accelerated read-only native polling with normal GC in a separate process."""
from datetime import datetime
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
requested=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'PAFPlayer.py'
sys.path.insert(0,str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards,unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('native-soak-'+stamp));stage.mkdir()
with (stage/'PAFPlayer.py').open('xb') as f:f.write(requested.read_bytes())
for key in ('APPDATA','LOCALAPPDATA','TMP','TEMP'):os.environ[key]=str(stage)
tempfile.tempdir=str(stage);sys.path.insert(0,str(stage));sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocked=install_guards(ROOT/'tests')
import PAFPlayer as app
import PAFPlayer_steam as steam

events=[];begins={};result={};errors=[]
def callback(phase, info):
    generation=info['generation']
    if phase=='start':begins[generation]=time.perf_counter()
    else:events.append({'generation':generation,'ms':1000*(time.perf_counter()-begins[generation]),'collected':info['collected']})
def snapshot():
    memory=app.paf_runtime_diagnostics_snapshot()['memory']
    return dict(memory=memory,pointer_types=len(app.ctypes._pointer_type_cache),
                function_types=len(app.ctypes._win_functype_cache),tracked_objects=len(gc.get_objects()))
def work():
    try:
        for _ in range(3):app.probe_external_audio_sessions();steam.process_images()
        gc.collect();result['before']=snapshot();gc.callbacks.append(callback)
        begin=time.perf_counter();known=0
        try:
            for i in range(500):
                known+=bool(app.probe_external_audio_sessions()['known'])
                if i%5==0:app.paf_runtime_diagnostics_snapshot()
                if i%25==0:steam.process_images()
        finally:gc.callbacks.remove(callback)
        result['seconds']=time.perf_counter()-begin;result['known_audio_samples']=known
        # A forced collection is used only after the isolated benchmark ends,
        # so retained growth excludes ordinary reclaimable garbage.
        gc.collect();result['after']=snapshot()
    except BaseException as exc:errors.append(repr(exc))
thread=threading.Thread(target=work);thread.start();thread.join()
report=unique(ROOT/'tests/reports'/('native-soak-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
summary=dict(version=app.PROGRAM_VERSION,source_sha256=hashlib.sha256((stage/'PAFPlayer.py').read_bytes()).hexdigest(),
    audio_polls=500,diagnostic_polls=100,steam_polls=20,result=result,gc_events=events,errors=errors,blocked_writes=blocked,
    stage=str(stage),limitations='Accelerated native-poll workload, not a live full-player soak or frame-latency measurement.')
with report.open('x',encoding='utf8') as f:json.dump(summary,f,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('gc_events','stage','blocked_writes')},indent=2));print(report)
if errors:raise SystemExit(1)

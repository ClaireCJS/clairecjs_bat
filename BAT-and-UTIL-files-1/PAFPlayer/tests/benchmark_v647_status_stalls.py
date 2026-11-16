"""Measure real status title expressions with a competing Python render worker.

No playback, UI, settings writes, or server is started. The worker represents
GIL contention, not a complete karaoke display or an achieved FPS measurement.
"""
import ast
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import threading
import time
from run_PAFPlayer_tests import install_guards, unique

ROOT=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'PAFPlayer.py'
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('status-contention-v647-'+stamp));stage.mkdir(parents=True)
with (stage/'PAFPlayer.py').open('xb') as f:f.write(source.read_bytes())
for key in ('TEMP','TMP','APPDATA','LOCALAPPDATA'):os.environ[key]=str(stage)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB']=str(stage/'history.sqlite3');tempfile.tempdir=str(stage)
sys.path.insert(0,str(stage));sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocks=install_guards(ROOT/'tests')
import PAFPlayer as app

tree=ast.parse(source.read_text(encoding='utf-8'))
play=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='play_audio_file')
publish=next(n for n in ast.walk(play) if isinstance(n,ast.Call) and
             isinstance(n.func,ast.Attribute) and n.func.attr=='publish' and len(n.keywords)>100)
fields=[k for k in publish.keywords if k.arg in ('console_title_style','console_title_content')]
assert len(fields)==2
expr=compile(ast.fix_missing_locations(ast.Expression(ast.Dict(
    keys=[ast.Constant(k.arg) for k in fields],values=[k.value for k in fields]))),'<actual periodic status titles>','eval')
ns=dict(load_player_settings=lambda:app.load_player_settings(read_only=True),
        console_title_style=1,console_title_content=1)
settings_calls=[0]
def settings():
    settings_calls[0]+=1
    return app.load_player_settings(read_only=True)
ns['load_player_settings']=settings

def run():
    timings=[]
    for _ in range(5):
        start=time.perf_counter();eval(expr,ns);timings.append((time.perf_counter()-start)*1000)
    return dict(median_ms=statistics.median(timings),max_ms=max(timings),samples_ms=timings)

quiet=run();stop=threading.Event();ready=threading.Event()
def competing_render_work():
    ready.set()
    while not stop.is_set():
        sum(i*i for i in range(3000))
worker=threading.Thread(target=competing_render_work,name='fixture-render-load')
worker.start();ready.wait()
try:contended=run()
finally:stop.set();worker.join(3);assert not worker.is_alive()
summary=dict(version=app.PROGRAM_VERSION,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             quiet=quiet,competing_python_thread=contended,settings_load_calls=settings_calls[0],
             caveat='Synthetic shared-interpreter contention; not full player FPS',blocks=blocks)
report=unique(ROOT/'tests/reports'/('v647-status-contention-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2)
print(json.dumps(summary));print(report)

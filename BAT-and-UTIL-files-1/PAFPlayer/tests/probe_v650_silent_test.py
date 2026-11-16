"""Isolate the existing five-second silent-playback assertion with stack evidence."""
from datetime import datetime
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
requested=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'PAFPlayer.py'
sys.path.insert(0,str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards,unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('v650-silence-'+stamp));stage.mkdir()
with (stage/'PAFPlayer.py').open('xb') as f:f.write(requested.read_bytes())
for k in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):os.environ[k]=str(stage)
tempfile.tempdir=str(stage);sys.path.insert(0,str(stage));sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocked=install_guards(ROOT/'tests')
import PAFPlayer as app
samples=[];done=threading.Event();started=time.perf_counter()
def sample():
    while not done.wait(.25):samples.append({'elapsed':time.perf_counter()-started,'threads':app.paf_runtime_thread_stacks()})
sampler=threading.Thread(target=sample,daemon=True);sampler.start()
report=unique(ROOT/'tests/reports'/('v650-silence-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.with_suffix('.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(app.PlayWaveFileTests('test_one_second_silence_completes_with_drcs_and_looping_off'))
done.set();sampler.join(2)
with report.open('x',encoding='utf-8') as f:json.dump({'version':app.PROGRAM_VERSION,'tests':result.testsRun,'failures':[(str(c),t) for c,t in result.failures],'errors':[(str(c),t) for c,t in result.errors],'samples':samples,'blocked_writes':blocked},f)
print(report)

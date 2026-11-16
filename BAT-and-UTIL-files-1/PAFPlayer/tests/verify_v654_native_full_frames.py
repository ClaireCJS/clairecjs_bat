"""Guarded native-poll regressions plus existing Steam/media/retention tests."""
import ast
import contextlib
from datetime import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
requested=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'PAFPlayer.py'
existing_only='--existing-only' in sys.argv[2:]
sys.path.insert(0,str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards,unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('v654-checks-'+stamp));stage.mkdir();(stage/'tests').mkdir()
modules=['test_v654_native_full_frames','test_pipeline_native_allocations','test_v650_karaoke_resize','test_v651_idle_dance_session_errors',
         'test_PAFPlayer_v458','test_v580_tray_and_steam','test_v581_steam_notices',
         'test_play_audio_file_v418','test_v648_local_stack_diagnostics']
for path in [requested,*[ROOT/'tests'/(name+'.py') for name in modules]]:
    with (stage/'PAFPlayer.py' if path==requested else stage/'tests'/path.name).open('xb') as f:f.write(path.read_bytes())
steam_source=requested.parent/'PAFPlayer_steam.py'
if not steam_source.is_file():steam_source=ROOT/'src/PAFPlayer_steam.py'
with (stage/'PAFPlayer_steam.py').open('xb') as f:f.write(steam_source.read_bytes())
with (stage/'baseline_v653.py').open('xb') as f:f.write((ROOT/'releases/PAFPlayer_v653_idle_art_music_dance.py').read_bytes())
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):os.environ[key]=str(stage)
tempfile.tempdir=str(stage);os.environ['PLAY_AUDIO_FILE_HISTORY_DB']=str(stage/'history.sqlite3')
sys.path[:0]=[str(stage),str(stage/'tests')];sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocked=install_guards(ROOT/'tests')
import PAFPlayer as app
sys.modules['play_audio_file']=app
suite=unittest.TestSuite()
for name in modules:
    if existing_only and name=='test_pipeline_native_allocations':continue
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
for name in ('test_v447_native_audio_probe_reads_mute_without_calling_setmute',
             'test_v452_external_media_loudness_match_is_guarded_and_bidirectional',
             'test_v86_idle_art_default_cli_and_media_player_guard_are_present',
             'test_v86_idle_art_drift_box_is_tiny_and_monitor_safe'):
    suite.addTest(app.PlayWaveFileTests(name))
report=unique(ROOT/'tests/reports'/('v654-checks-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.with_suffix('.log').open('x',encoding='utf8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
source=(stage/'PAFPlayer.py').read_text(encoding='utf8');bundles={}
compile(source,str(stage/'PAFPlayer.py'),'exec')
for node in ast.parse(source).body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES':bundles.update(ast.literal_eval(node.value))
            elif isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES':bundles[ast.literal_eval(target.slice)]=ast.literal_eval(node.value)
parity=[]
for name,body in bundles.items():
    compile(body,name,'exec')
    paths=[ROOT/'src'/(name+'.py'),ROOT/'lockscreen/src'/(name+'.py'),ROOT/'screensaver/src'/(name+'.py')]
    if name=='PAFPlayer_steam' and (requested.parent/'PAFPlayer_steam.py').is_file():paths.insert(0,requested.parent/'PAFPlayer_steam.py')
    if name=='PAFPlayer_lockscreen_installer':paths.append(ROOT/'lockscreen/lockscreen_installer.py')
    path=next((p for p in paths if p.is_file()),None)
    if path:
        assert body==path.read_text(encoding='utf8'),name
        parity.append(name)
scripts=re.findall(r'<script[^>]*>(.*?)</script>',app._paf_web_html(),re.S)
for script in scripts:
    proc=subprocess.run([r'C:\Program Files\nodejs\node.exe','--check','-'],input=script,text=True,capture_output=True,timeout=15)
    assert proc.returncode==0,proc.stderr
summary=dict(version=app.PROGRAM_VERSION,source_sha256=hashlib.sha256((stage/'PAFPlayer.py').read_bytes()).hexdigest(),
    tests=result.testsRun,failures=[(str(c),t) for c,t in result.failures],errors=[(str(c),t) for c,t in result.errors],
    bundles=len(bundles),parity=parity,javascript_blocks=len(scripts),stage=str(stage),blocked_writes=blocked)
with report.open('x',encoding='utf8') as f:json.dump(summary,f,indent=2)
print(json.dumps({k:v for k,v in summary.items() if k not in ('blocked_writes','parity')},indent=2));print(report)
sys.exit(0 if result.wasSuccessful() else 1)

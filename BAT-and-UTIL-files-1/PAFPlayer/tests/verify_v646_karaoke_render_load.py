"""Retained guarded tests, compilation, bundle parity and generated JS syntax."""
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

root=Path(__file__).resolve().parents[1]
requested=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root/'PAFPlayer.py'
sys.path.insert(0,str(root/'tests'))
from run_PAFPlayer_tests import install_guards,unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(root/'tests/runs'/('checks-v646-'+stamp));stage.mkdir(parents=True);(stage/'tests').mkdir()
for path in (requested,root/'tests/test_v643_artwork_karaoke_fit.py',root/'tests/test_v646_karaoke_render_load.py',root/'tests/test_v619_karaoke_entry.py',root/'tests/test_v645_artwork_window_controls.py',root/'tests/test_v642_artwork_chrome.py',root/'tests/test_v641_emojimax_solution_color.py'):
    with (stage/'PAFPlayer.py' if path==requested else stage/'tests'/path.name).open('xb') as f:f.write(path.read_bytes())
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'):os.environ[key]=str(stage)
tempfile.tempdir=str(stage);os.environ['PLAY_AUDIO_FILE_HISTORY_DB']=str(stage/'history.sqlite3')
sys.path[:0]=[str(stage),str(stage/'tests')];sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocks=install_guards(root/'tests')
import PAFPlayer as app
suite=unittest.TestSuite()
for name in ('test_v646_karaoke_render_load','test_v619_karaoke_entry','test_v645_artwork_window_controls','test_v643_artwork_karaoke_fit','test_v642_artwork_chrome','test_v641_emojimax_solution_color'):
    if name=='test_v646_karaoke_render_load' and app.PROGRAM_VERSION=='V645':continue
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)))
names=[]
for name in dir(app.PlayWaveFileTests):
    if name.startswith('test_') and any(x in name for x in ('album_art','artwork','floating')) and any(x in name for x in ('border','focus','geometry','placement','chrome','title','compact','scaled','zoom')):
        names.append(name)
    elif name.startswith('test_') and any(x in name for x in ('karaoke', 'lyric', 'emojimax')):
        names.append(name)
suite.addTests(app.PlayWaveFileTests(n) for n in names)
report=unique(root/'tests/reports'/('v646-checks-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.with_suffix('.log').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
source=requested.read_text(encoding='utf-8');tree=ast.parse(source)
bundles={};compiled=[];parity=[]
for path in [requested,*root.glob('tests/*v646*.py'),*root.glob('tools/*v646*.py')]:
    compile(path.read_text(encoding='utf-8'),str(path),'exec');compiled.append(str(path))
for node in tree.body:
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES':bundles.update(ast.literal_eval(node.value))
            if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES':bundles[ast.literal_eval(target.slice)]=ast.literal_eval(node.value)
for name,text in bundles.items():
    compile(text,name,'exec')
    path=next((p for p in (root/'src'/(name+'.py'),root/'lockscreen/src'/(name+'.py'),root/'screensaver/src'/(name+'.py'),root/'lockscreen/lockscreen_installer.py' if name=='PAFPlayer_lockscreen_installer' else root/'nonexistent') if p.is_file()),root/'nonexistent')
    if path.is_file():
        assert text==path.read_text(encoding='utf-8'),name
        parity.append(name)
html=app._paf_web_html();scripts=re.findall(r'<script[^>]*>(.*?)</script>',html,re.S)
for script in scripts:
    checked=subprocess.run([r'C:\Program Files\nodejs\node.exe','--check','-'],input=script,text=True,capture_output=True,timeout=15)
    assert checked.returncode==0,checked.stderr
summary=dict(version=app.PROGRAM_VERSION,tests=result.testsRun,failures=[(str(c),t) for c,t in result.failures],errors=[(str(c),t) for c,t in result.errors],skipped=len(result.skipped),
             compiled=compiled,bundles=len(bundles),parity=parity,javascript_blocks=len(scripts),blocked_writes=blocks,stage=str(stage),
             source_sha256=hashlib.sha256(requested.read_bytes()).hexdigest())
with report.open('x',encoding='utf-8') as f:json.dump(summary,f,indent=2)
print(json.dumps(dict(version=app.PROGRAM_VERSION,tests=result.testsRun,failures=[str(c) for c,t in result.failures],errors=[str(c) for c,t in result.errors],bundles=len(bundles),parity=len(parity),scripts=len(scripts)),indent=2));print(report)
sys.exit(0 if result.wasSuccessful() else 1)
